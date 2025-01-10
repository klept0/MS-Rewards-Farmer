import contextlib
import dbm.dumb
import json
import logging
import random
import shelve
import time
from datetime import date, timedelta
from enum import Enum, auto
from itertools import cycle
from typing import Final

import requests
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from src.browser import Browser
from src.utils import Utils


class RetriesStrategy(Enum):
    """
    method to use when retrying
    """

    EXPONENTIAL = auto()
    """
    an exponentially increasing `base_delay_in_seconds` between attempts
    """
    CONSTANT = auto()
    """
    the default; a constant `base_delay_in_seconds` between attempts
    """


class Searches:
    config = Utils.loadConfig()
    maxRetries: Final[int] = config.get("retries", {}).get("max", 8)
    """
    the max amount of retries to attempt
    """
    baseDelay: Final[float] = config.get("retries", {}).get(
        "base_delay_in_seconds", 14.0625
    )
    """
    how many seconds to delay
    """
    # retriesStrategy = Final[  # todo Figure why doesn't work with equality below
    retriesStrategy = RetriesStrategy[
        config.get("retries", {}).get("strategy", RetriesStrategy.CONSTANT.name)
    ]

    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver

        dumbDbm = dbm.dumb.open((Utils.getProjectRoot() / "google_trends").__str__())
        self.googleTrendsShelf: shelve.Shelf = shelve.Shelf(dumbDbm)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.googleTrendsShelf.__exit__(None, None, None)

    def getGoogleTrends(self, wordsCount: int) -> list[str]:
        # Function to retrieve Google Trends search terms
        searchTerms: list[str] = []
        days_back = 0
        max_retries = 10  # Maximum number of days to look back
        session = Utils.makeRequestsSession()

        while len(searchTerms) < wordsCount and days_back < max_retries:
            days_back += 1
            # Fetching daily trends from Google Trends API
            try:
                r = session.get(
                    f"https://trends.google.com/trends/api/dailytrends?hl={self.browser.localeLang}"
                    f'&ed={(date.today() - timedelta(days=days_back)).strftime("%Y%m%d")}&geo={self.browser.localeGeo}&ns=15'
                )

                if r.status_code != requests.codes.ok:
                    logging.warning(
                        f"[GOOGLE TRENDS] Failed to fetch trends, status code: {r.status_code}"
                    )
                    continue

                try:
                    trends = json.loads(r.text[6:])
                except json.JSONDecodeError as e:
                    logging.warning(
                        f"[GOOGLE TRENDS] Failed to decode JSON response: {e}"
                    )
                    continue

                # Validate the response structure
                if not trends.get("default"):
                    logging.warning("[GOOGLE TRENDS] Missing 'default' key in response")
                    continue

                trending_days = trends["default"].get("trendingSearchesDays", [])
                if not trending_days:
                    logging.warning(
                        "[GOOGLE TRENDS] No trending searches found for this day"
                    )
                    continue

                trending_searches = trending_days[0].get("trendingSearches", [])
                if not trending_searches:
                    logging.warning("[GOOGLE TRENDS] Empty trending searches list")
                    continue

                for topic in trending_searches:
                    if "title" in topic and "query" in topic["title"]:
                        searchTerms.append(topic["title"]["query"].lower())
                        if "relatedQueries" in topic:
                            searchTerms.extend(
                                relatedTopic["query"].lower()
                                for relatedTopic in topic["relatedQueries"]
                                if "query" in relatedTopic
                            )

                searchTerms = list(set(searchTerms))

            except Exception as e:
                logging.error(f"[GOOGLE TRENDS] Unexpected error: {str(e)}")
                continue

        if len(searchTerms) < wordsCount:
            logging.warning(
                f"[GOOGLE TRENDS] Could only fetch {len(searchTerms)} terms out of {wordsCount} requested"
            )
            # Pad with dummy searches if we don't have enough terms
            while len(searchTerms) < wordsCount:
                searchTerms.append(f"news {random.randint(1, 1000)}")
        else:
            del searchTerms[wordsCount:]

        return searchTerms

    def getRelatedTerms(self, term: str) -> list[str]:
        # Function to retrieve related terms from Bing API
        relatedTerms: list[str] = (
            Utils.makeRequestsSession()
            .get(
                f"https://api.bing.com/osjson.aspx?query={term}",
                headers={"User-agent": self.browser.userAgent},
            )
            .json()[1]
        )  # todo Wrap if failed, or assert response?
        if not relatedTerms:
            return [term]
        return relatedTerms

    def bingSearches(self) -> None:
        # Function to perform Bing searches
        logging.info(
            f"[BING] Starting {self.browser.browserType.capitalize()} Edge Bing searches..."
        )

        self.browser.utils.goToSearch()

        while (remainingSearches := self.browser.getRemainingSearches()) > 0:
            logging.info(f"[BING] Remaining searches={remainingSearches}")
            desktopAndMobileRemaining = self.browser.getRemainingSearches(
                desktopAndMobile=True
            )
            if desktopAndMobileRemaining.getTotal() > len(self.googleTrendsShelf):
                # self.googleTrendsShelf.clear()  # Maybe needed?
                logging.debug(
                    f"google_trends before load = {list(self.googleTrendsShelf.items())}"
                )
                trends = self.getGoogleTrends(desktopAndMobileRemaining.getTotal())
                random.shuffle(trends)
                for trend in trends:
                    self.googleTrendsShelf[trend] = None
                logging.debug(
                    f"google_trends after load = {list(self.googleTrendsShelf.items())}"
                )
            self.bingSearch()
            time.sleep(random.randint(10, 15))

        logging.info(
            f"[BING] Finished {self.browser.browserType.capitalize()} Edge Bing searches !"
        )

    def bingSearch(self) -> None:
        # Function to perform a single Bing search
        pointsBefore = self.browser.utils.getAccountPoints()

        rootTerm = list(self.googleTrendsShelf.keys())[0]
        terms = self.getRelatedTerms(rootTerm)
        logging.debug(f"terms={terms}")
        termsCycle: cycle[str] = cycle(terms)
        baseDelay = Searches.baseDelay
        logging.debug(f"rootTerm={rootTerm}")

        for i in range(self.maxRetries + 1):
            if i != 0:
                sleepTime: float
                if Searches.retriesStrategy == Searches.retriesStrategy.EXPONENTIAL:
                    sleepTime = baseDelay * 2 ** (i - 1)
                elif Searches.retriesStrategy == Searches.retriesStrategy.CONSTANT:
                    sleepTime = baseDelay
                else:
                    raise AssertionError
                logging.debug(
                    f"[BING] Search attempt not counted {i}/{Searches.maxRetries}, sleeping {sleepTime}"
                    f" seconds..."
                )
                time.sleep(sleepTime)

            searchbar: WebElement
            for _ in range(1000):
                searchbar = self.browser.utils.waitUntilClickable(
                    By.ID, "sb_form_q", timeToWait=40
                )
                searchbar.clear()
                term = next(termsCycle)
                logging.debug(f"term={term}")
                time.sleep(1)
                searchbar.send_keys(term)
                time.sleep(1)
                with contextlib.suppress(TimeoutException):
                    WebDriverWait(self.webdriver, 20).until(
                        expected_conditions.text_to_be_present_in_element_value(
                            (By.ID, "sb_form_q"), term
                        )
                    )
                    break
                logging.debug("error send_keys")
            else:
                # todo Still happens occasionally, gotta be a fix
                raise TimeoutException
            searchbar.submit()

            pointsAfter = self.browser.utils.getAccountPoints()
            if pointsBefore < pointsAfter:
                del self.googleTrendsShelf[rootTerm]
                return

            # todo
            # if i == (maxRetries / 2):
            #     logging.info("[BING] " + "TIMED OUT GETTING NEW PROXY")
            #     self.webdriver.proxy = self.browser.giveMeProxy()
        logging.error("[BING] Reached max search attempt retries")

        logging.debug("Moving passedInTerm to end of list")
        del self.googleTrendsShelf[rootTerm]
        self.googleTrendsShelf[rootTerm] = None
