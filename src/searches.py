import dbm.dumb
import logging
import shelve
from enum import Enum, auto
from itertools import cycle
from random import random, randint, shuffle
from time import sleep
from typing import Final

from selenium.webdriver.common.by import By
from trendspy import Trends

from src.browser import Browser
from src.utils import CONFIG, getProjectRoot


class RetriesStrategy(Enum):
    """
    method to use when retrying
    """

    EXPONENTIAL = auto()
    """
    an exponentially increasing `base-delay-in-seconds` between attempts
    """
    CONSTANT = auto()
    """
    the default; a constant `base-delay-in-seconds` between attempts
    """


class Searches:
    maxRetries: Final[int] = CONFIG.retries.max
    """
    the max amount of retries to attempt
    """
    baseDelay: Final[float] = CONFIG.get("retries.base-delay-in-seconds")
    """
    how many seconds to delay
    """
    # retriesStrategy = Final[  # todo Figure why doesn't work with equality below
    retriesStrategy = RetriesStrategy[CONFIG.retries.strategy]

    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver

        dumbDbm = dbm.dumb.open((getProjectRoot() / "google_trends").__str__())
        self.googleTrendsShelf: shelve.Shelf = shelve.Shelf(dumbDbm)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.googleTrendsShelf.__exit__(None, None, None)

    def bingSearches(self) -> None:
        # Function to perform Bing searches
        logging.info(
            f"[BING] Starting {self.browser.browserType.capitalize()} Edge Bing searches..."
        )

        self.browser.utils.goToSearch()

        while True:
            desktopAndMobileRemaining = self.browser.getRemainingSearches(
                desktopAndMobile=True
            )
            logging.info(f"[BING] Remaining searches={desktopAndMobileRemaining}")
            if (
                self.browser.browserType == "desktop"
                and desktopAndMobileRemaining.desktop == 0
            ) or (
                self.browser.browserType == "mobile"
                and desktopAndMobileRemaining.mobile == 0
            ):
                break

            if desktopAndMobileRemaining.getTotal() > len(self.googleTrendsShelf):
                logging.debug(
                    f"google_trends before load = {list(self.googleTrendsShelf.items())}"
                )
                trends = Trends()
                trends = trends.trending_now(geo=CONFIG.browser.geolocation)[
                    : desktopAndMobileRemaining.getTotal()
                ]
                shuffle(trends)
                for trend in trends:
                    self.googleTrendsShelf[trend.keyword] = trend
                logging.debug(
                    f"google_trends after load = {list(self.googleTrendsShelf.items())}"
                )

            self.bingSearch()
            del self.googleTrendsShelf[list(self.googleTrendsShelf.keys())[0]]
            sleep(randint(10, 15))

        logging.info(
            f"[BING] Finished {self.browser.browserType.capitalize()} Edge Bing searches !"
        )

    def bingSearch(self) -> None:
        # Function to perform a single Bing search
        pointsBefore = self.browser.utils.getAccountPoints()

        trend = list(self.googleTrendsShelf.keys())[0]
        trendKeywords = self.googleTrendsShelf[trend].trend_keywords
        logging.debug(f"trendKeywords={trendKeywords}")
        termsCycle: cycle[str] = cycle(trendKeywords)
        baseDelay = Searches.baseDelay
        logging.debug(f"trend={trend}")

        # todo If first 3 searches of day, don't retry since points register differently, will be a bit quicker
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
                logging.debug(
                    f"[BING] Search attempt not counted {i}/{Searches.maxRetries}, sleeping {sleepTime}"
                    f" seconds..."
                )
                sleep(sleepTime)

            searchbar = self.browser.utils.waitUntilClickable(
                By.ID, "sb_form_q", timeToWait=40
            )
            searchbar.clear()
            term = next(termsCycle)
            logging.debug(f"term={term}")
            sleep(1)
            searchbar.send_keys(term)
            sleep(1)
            searchbar.submit()

            pointsAfter = self.browser.utils.getAccountPoints()
            if pointsBefore < pointsAfter:
                sleep(randint(CONFIG.cooldown.min, CONFIG.cooldown.max))
                return

            # todo
            # if i == (maxRetries / 2):
            #     logging.info("[BING] " + "TIMED OUT GETTING NEW PROXY")
            #     self.webdriver.proxy = self.browser.giveMeProxy()
        logging.error("[BING] Reached max search attempt retries")
