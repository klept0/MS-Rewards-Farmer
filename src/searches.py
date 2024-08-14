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
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from src.browser import Browser
from src.utils import Utils

LOAD_DATE_KEY = "loadDate"


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
        logging.debug(f"googleTrendsShelf.__dict__ = {self.googleTrendsShelf.__dict__}")
        logging.debug(f"google_trends = {list(self.googleTrendsShelf.items())}")
        loadDate: date | None = None
        if LOAD_DATE_KEY in self.googleTrendsShelf:
            loadDate = self.googleTrendsShelf[LOAD_DATE_KEY]

        if loadDate is None or loadDate < date.today():
            self.googleTrendsShelf.clear()
            trends = self.getGoogleTrends(
                browser.getRemainingSearches(desktopAndMobile=True).getTotal()
            )
            random.shuffle(trends)
            for trend in trends:
                self.googleTrendsShelf[trend] = None
            self.googleTrendsShelf[LOAD_DATE_KEY] = date.today()
            logging.debug(
                f"google_trends after load = {list(self.googleTrendsShelf.items())}"
            )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.googleTrendsShelf.__exit__(None, None, None)

    def getGoogleTrends(self, wordsCount: int) -> list[str]:
        # Function to retrieve Google Trends search terms
        searchTerms: list[str] = []
        i = 0
        session = Utils.makeRequestsSession()
        while len(searchTerms) < wordsCount:
            i += 1
            # Fetching daily trends from Google Trends API
            r = session.get(
                f"https://trends.google.com/trends/api/dailytrends?hl={self.browser.localeLang}"
                f'&ed={(date.today() - timedelta(days=i)).strftime("%Y%m%d")}&geo={self.browser.localeGeo}&ns=15'
            )
            assert r.status_code == requests.codes.ok
            trends = json.loads(r.text[6:])
            for topic in trends["default"]["trendingSearchesDays"][0][
                "trendingSearches"
            ]:
                searchTerms.append(topic["title"]["query"].lower())
                searchTerms.extend(
                    relatedTopic["query"].lower()
                    for relatedTopic in topic["relatedQueries"]
                )
            searchTerms = list(set(searchTerms))
        del searchTerms[wordsCount : (len(searchTerms) + 1)]
        return searchTerms

    def getRelatedTerms(self, term: str) -> list[str]:
        # Function to retrieve related terms from Bing API
        relatedTerms: list[str] = requests.get(
            f"https://api.bing.com/osjson.aspx?query={term}",
            headers={"User-agent": self.browser.userAgent},
        ).json()[1]
        if not relatedTerms:
            return [term]
        return relatedTerms

    def bingSearches(self) -> None:
        # Function to perform Bing searches
        logging.info(
            f"[BING] Starting {self.browser.browserType.capitalize()} Edge Bing searches..."
        )

        self.browser.utils.goToSearch()

        remainingSearches = self.browser.getRemainingSearches()
        for searchCount in range(1, remainingSearches + 1):
            # todo Disable cooldown for first 3 searches (Earning starts with your third search)
            logging.info(f"[BING] {searchCount}/{remainingSearches}")
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
                    f"[BING] Search attempt failed {i}/{Searches.maxRetries}, sleeping {sleepTime}"
                    f" seconds..."
                )
                time.sleep(sleepTime)

            searchbar = self.browser.utils.waitUntilClickable(
                By.ID, "sb_form_q", timeToWait=20
            )
            for _ in range(1000):
                self.browser.utils.click(searchbar)
                searchbar.clear()
                term = next(termsCycle)
                logging.debug(f"term={term}")
                searchbar.send_keys(term)
                with contextlib.suppress(TimeoutException):
                    WebDriverWait(self.webdriver, 10).until(
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
