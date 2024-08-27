import logging
import urllib.parse
from datetime import datetime

from src.browser import Browser
from .activities import Activities


class DailySet:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver
        self.activities = Activities(browser)

    def completeDailySet(self):
        # Function to complete the Daily Set
        logging.info("[DAILY SET] " + "Trying to complete the Daily Set...")
        data = self.browser.utils.getDashboardData()["dailySetPromotions"]
        self.browser.utils.goToRewards()
        todayDate = datetime.now().strftime("%m/%d/%Y")
        for activity in data.get(todayDate, []):
            cardId = int(activity["offerId"][-1:])
            try:
                # Open the Daily Set activity
                if activity["complete"] is not False:
                    continue
                self.activities.openDailySetActivity(cardId)
                if activity["promotionType"] == "urlreward":
                    logging.info(f"[DAILY SET] Completing search of card {cardId}")
                    # Complete search for URL reward
                    self.activities.completeSearch()
                if activity["promotionType"] == "quiz":
                    if (
                        activity["pointProgressMax"] == 50
                        and activity["pointProgress"] == 0
                    ):
                        logging.info(
                            "[DAILY SET] " + f"Completing This or That of card {cardId}"
                        )
                        # Complete This or That for a specific point progress max
                        self.activities.completeThisOrThat()
                    elif (
                        activity["pointProgressMax"] in [40, 30]
                    ):
                        logging.info(f"[DAILY SET] Completing quiz of card {cardId}")
                        # Complete quiz for specific point progress max
                        self.activities.completeQuiz()
                    elif (
                        activity["pointProgressMax"] == 10
                        and activity["pointProgress"] == 0
                    ):
                        # Extract and parse search URL for additional checks
                        searchUrl = urllib.parse.unquote(
                            urllib.parse.parse_qs(
                                urllib.parse.urlparse(activity["destinationUrl"]).query
                            )["ru"][0]
                        )
                        searchUrlQueries = urllib.parse.parse_qs(
                            urllib.parse.urlparse(searchUrl).query
                        )
                        filters = {}
                        for filterEl in searchUrlQueries["filters"][0].split(" "):
                            filterEl = filterEl.split(":", 1)
                            filters[filterEl[0]] = filterEl[1]
                        if "PollScenarioId" in filters:
                            logging.info(
                                f"[DAILY SET] Completing poll of card {cardId}"
                            )
                            # Complete survey for a specific scenario
                            self.activities.completeSurvey()
                        else:
                            logging.info(
                                f"[DAILY SET] Completing quiz of card {cardId}"
                            )
                            try:
                                # Try completing ABC activity
                                self.activities.completeABC()
                            except Exception:  # pylint: disable=broad-except
                                logging.warning("", exc_info=True)
                                # Default to completing quiz
                                self.activities.completeQuiz()
            except Exception:  # pylint: disable=broad-except
                logging.error(
                    f"[DAILY SET] Error Daily Set of card {cardId}", exc_info=True
                )
                # Reset tabs in case of an exception
                self.browser.utils.resetTabs()
                continue
        logging.info("[DAILY SET] Exiting")
