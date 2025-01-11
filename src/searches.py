import dbm.dumb
import json
import logging
import shelve
from datetime import date, timedelta
from enum import Enum, auto
from itertools import cycle
from random import random, randint, shuffle
from time import sleep
from typing import Final

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from src.browser import Browser
from src.utils import CONFIG, makeRequestsSession, getProjectRoot

class RetriesStrategy(Enum):
    EXPONENTIAL = auto()
    CONSTANT = auto()

class Searches:
    maxRetries: Final[int] = CONFIG.get("retries").get("max")
    baseDelay: Final[float] = CONFIG.get("retries").get("base_delay_in_seconds")
    retriesStrategy = RetriesStrategy[CONFIG.get("retries").get("strategy")]

    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver

        db_path = getProjectRoot() / "google_trends"
        dumbDbm = dbm.dumb.open(str(db_path))
        self.googleTrendsShelf: shelve.Shelf = shelve.Shelf(dumbDbm)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.googleTrendsShelf.__exit__(None, None, None)

    def getGoogleTrends(self, wordsCount: int) -> list[str]:
        logging.info("Fetching Google Trends data...")
        searchTerms = []
        session = makeRequestsSession()

        for i in range(1, wordsCount + 1):
            r = session.get(
                f"https://trends.google.com/trends/api/dailytrends?hl={self.browser.localeLang}" \
                f'&ed={(date.today() - timedelta(days=i)).strftime("%Y%m%d")}&geo={self.browser.localeGeo}&ns=15'
            )

            if r.status_code != requests.codes.ok:
                logging.error("Failed to fetch Google Trends data, retry config may need adjustment.")
                continue

            trends = json.loads(r.text[6:])
            for topic in trends["default"]["trendingSearchesDays"][0]["trendingSearches"]:
                searchTerms.append(topic["title"]["query"].lower())
                searchTerms.extend(
                    relatedTopic["query"].lower() for relatedTopic in topic["relatedQueries"]
                )

            searchTerms = list(set(searchTerms))

            if len(searchTerms) >= wordsCount:
                break

        logging.info(f"Retrieved {len(searchTerms)} Google Trends terms.")
        return searchTerms[:wordsCount]

    def getRelatedTerms(self, term: str) -> list[str]:
        logging.debug(f"Fetching related terms for: {term}")
        response = makeRequestsSession().get(
            f"https://api.bing.com/osjson.aspx?query={term}",
            headers={"User-agent": self.browser.userAgent},
        )

        if response.status_code != requests.codes.ok:
            logging.error(f"Failed to fetch related terms for: {term}")
            return [term]

        relatedTerms = response.json()[1]
        logging.debug(f"Related terms for {term}: {relatedTerms}")
        return relatedTerms if relatedTerms else [term]

    def bingSearches(self) -> None:
        logging.info(f"Starting {self.browser.browserType.capitalize()} Bing searches...")

        # Initialize rewards.bing.com tab
        rewards_tab = None
        for handle in self.webdriver.window_handles:
            self.webdriver.switch_to.window(handle)
            if self.webdriver.current_url.startswith("https://rewards.bing.com"):
                rewards_tab = handle
                break

        if not rewards_tab:
            logging.info("Opening rewards.bing.com in a new tab...")
            self.webdriver.execute_script("window.open('https://rewards.bing.com');")
            rewards_tab = self.webdriver.window_handles[-1]

        # Initialize bing.com tab
        search_tab = None
        for handle in self.webdriver.window_handles:
            self.webdriver.switch_to.window(handle)
            if self.webdriver.current_url.startswith("https://www.bing.com"):
                search_tab = handle
                break

        if not search_tab:
            logging.info("Opening bing.com in a new tab...")
            self.webdriver.execute_script("window.open('https://www.bing.com');")
            search_tab = self.webdriver.window_handles[-1]

        while True:
            # Switch to rewards.bing.com tab to check remaining searches
            self.webdriver.switch_to.window(rewards_tab)
            remainingSearches = self.browser.getRemainingSearches(desktopAndMobile=True)
            logging.info(f"Remaining searches: {remainingSearches}")

            if (self.browser.browserType == "desktop" and remainingSearches.desktop == 0) or \
            (self.browser.browserType == "mobile" and remainingSearches.mobile == 0):
                break

            # Ensure we have enough Google Trends terms
            if remainingSearches.getTotal() > len(self.googleTrendsShelf):
                trends = self.getGoogleTrends(remainingSearches.getTotal())
                shuffle(trends)
                for trend in trends:
                    self.googleTrendsShelf[trend] = None

            # Perform a search in the Bing tab
            self.webdriver.switch_to.window(search_tab)
            self.bingSearch(rewards_tab)

            # Remove used term from Google Trends shelf
            del self.googleTrendsShelf[list(self.googleTrendsShelf.keys())[0]]
            sleep(randint(10, 15))

        logging.info(f"Finished {self.browser.browserType.capitalize()} Bing searches.")

    def bingSearch(self, rewards_tab) -> None:
        pointsBefore = self.browser.utils.getAccountPoints()

        rootTerm = list(self.googleTrendsShelf.keys())[0]
        terms = self.getRelatedTerms(rootTerm)
        logging.info(f"Using root term: {rootTerm}")
        termsCycle: cycle[str] = cycle(terms)

        baseDelay = Searches.baseDelay

        for i in range(self.maxRetries + 1):
            if i != 0:
                sleepTime: float
                if Searches.retriesStrategy == Searches.retriesStrategy.EXPONENTIAL:
                    sleepTime = baseDelay * 2 ** (i - 1)
                elif Searches.retriesStrategy == Searches.retriesStrategy.CONSTANT:
                    sleepTime = baseDelay
                else:
                    raise AssertionError
                sleepTime += baseDelay * random()  # Add jitter
                logging.warning(
                    f"Retry {i}/{self.maxRetries}. Sleeping for {sleepTime:.2f} seconds..."
                )
                sleep(sleepTime)

            try:
                # Ensure the Bing search page is active or on a search result page
                if not self.webdriver.current_url.startswith("https://www.bing.com"):
                    logging.warning("[BING] Current tab is not Bing. Redirecting to Bing search page.")
                    self.webdriver.get("https://www.bing.com")

                searchbar = self.browser.utils.waitUntilClickable(
                    By.ID, "sb_form_q", timeToWait=60
                )
            except TimeoutException:
                logging.error("[BING] Search bar not found or clickable. Retrying...")
                continue

            searchbar.clear()
            term = next(termsCycle)
            logging.info(f"Searching for term: {term}")
            sleep(1)
            searchbar.send_keys(term)
            sleep(1)
            searchbar.submit()

            sleep(5)  # Wait for points to reflect

            # Switch back to rewards.bing.com tab to update points
            self.webdriver.switch_to.window(rewards_tab)
            pointsAfter = self.browser.utils.getAccountPoints()
            if pointsBefore < pointsAfter:
                logging.info(
                    f"Points increased. Current points: {pointsAfter}"
                )
                return

        logging.error("[BING] Reached max search attempt retries")
