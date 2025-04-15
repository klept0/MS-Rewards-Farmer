import dbm.dumb
import logging
import shelve
from enum import Enum, auto
from random import random, randint
from time import sleep
from typing import Final

from selenium.webdriver.common.by import By
from trendspy import Trends

from src.browser import Browser
from src.utils import CONFIG, getProjectRoot, cooldown, COUNTRY


class RetriesStrategy(Enum):
    """
    method to use when retrying
    """

    EXPONENTIAL = auto()
    """
    an exponentially increasing `backoff-factor` between attempts
    """
    CONSTANT = auto()
    """
    the default; a constant `backoff-factor` between attempts
    """


class Searches:
    """
    Class to handle searches in MS Rewards.
    """

    maxRetries: Final[int] = CONFIG.retries.max
    """
    the max amount of retries to attempt
    """
    baseDelay: Final[float] = CONFIG.get("retries.backoff-factor")
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
                trends = trends.trending_now(geo=COUNTRY)[
                    : desktopAndMobileRemaining.getTotal()
                ]
                for trend in trends:
                    self.googleTrendsShelf[trend.keyword] = trend
                logging.debug(
                    f"google_trends after load = {list(self.googleTrendsShelf.items())}"
                )

            self.bingSearch()
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
        logging.debug(f"trend={trend}")
        baseDelay = Searches.baseDelay

        for i in range(self.maxRetries + 1):
            if i != 0:
                if not trendKeywords:
                    del self.googleTrendsShelf[trend]

                    trend = list(self.googleTrendsShelf.keys())[0]
                    trendKeywords = self.googleTrendsShelf[trend].trend_keywords

                sleepTime: float
                if Searches.retriesStrategy == Searches.retriesStrategy.EXPONENTIAL:
                    sleepTime = baseDelay * 2 ** (i - 1)
                elif Searches.retriesStrategy == Searches.retriesStrategy.CONSTANT:
                    sleepTime = baseDelay
                else:
                    raise AssertionError
                sleepTime += baseDelay * random()  # Add jitter
                logging.debug(
                    f"[BING] Search attempt not counted {i}/{Searches.maxRetries},"
                    f" sleeping {sleepTime}"
                    f" seconds..."
                )
                sleep(sleepTime)

            self.browser.utils.goToSearch()
            searchbar = self.browser.utils.waitUntilClickable(
                By.ID, "sb_form_q", timeToWait=40
            )
            searchbar.clear()
            trendKeyword = trendKeywords.pop(0)
            logging.debug(f"trendKeyword={trendKeyword}")
            sleep(1)
            searchbar.send_keys(trendKeyword)
            sleep(1)
            searchbar.submit()

            pointsAfter = self.browser.utils.getAccountPoints()
            if pointsBefore < pointsAfter:
                del self.googleTrendsShelf[trend]
                cooldown()
                return

            # todo
            # if i == (maxRetries / 2):
            #     logging.info("[BING] " + "TIMED OUT GETTING NEW PROXY")
            #     self.webdriver.proxy = self.browser.giveMeProxy()
        logging.error("[BING] Reached max search attempt retries")
