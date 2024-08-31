import contextlib
import logging
import random
import time

from selenium.common import TimeoutException
from selenium.webdriver.common.by import By

from src.browser import Browser
from .activities import Activities
from .utils import Utils


# todo Rename MoreActivities?
class MorePromotions:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.activities = Activities(browser)

    # todo Refactor so less complex
    def completeMorePromotions(self):
        # Function to complete More Promotions
        logging.info("[MORE PROMOS] " + "Trying to complete More Promotions...")
        morePromotions: list[dict] = self.browser.utils.getDashboardData()[
            "morePromotions"
        ]
        self.browser.utils.goToRewards()
        for promotion in morePromotions:
            try:
                promotionTitle = promotion["title"].replace("\u200b", "").replace("\xa0", " ")
                logging.debug(f"promotionTitle={promotionTitle}")
                # Open the activity for the promotion
                if (
                    promotion["complete"] is not False
                    or promotion["pointProgressMax"] == 0
                ):
                    logging.debug("Already done, continuing")
                    continue
                self.activities.openMorePromotionsActivity(
                    morePromotions.index(promotion)
                )
                self.browser.webdriver.execute_script("window.scrollTo(0, 1080)")
                with contextlib.suppress(TimeoutException):
                    searchbar = self.browser.utils.waitUntilClickable(
                        By.ID, "sb_form_q"
                    )
                    self.browser.utils.click(searchbar)
                # todo These and following are US-English specific, maybe there's a good way to internationalize
                # todo Could use dictionary of promotionTitle to search to simplify
                if "Search the lyrics of a song" in promotionTitle:
                    searchbar.send_keys("black sabbath supernaut lyrics")
                    searchbar.submit()
                elif "Translate anything" in promotionTitle:
                    searchbar.send_keys("translate pencil sharpener to spanish")
                    searchbar.submit()
                elif "Let's watch that movie again!" in promotionTitle:
                    searchbar.send_keys("aliens movie")
                    searchbar.submit()
                elif "Discover open job roles" in promotionTitle:
                    searchbar.send_keys("walmart open job roles")
                    searchbar.submit()
                elif "Plan a quick getaway" in promotionTitle:
                    searchbar.send_keys("flights nyc to paris")
                    searchbar.submit()
                elif "You can track your package" in promotionTitle:
                    searchbar.send_keys("usps tracking")
                    searchbar.submit()
                elif "Find somewhere new to explore" in promotionTitle:
                    searchbar.send_keys("directions to new york")
                    searchbar.submit()
                elif "Too tired to cook tonight?" in promotionTitle:
                    searchbar.send_keys("Pizza Hut near me")
                    searchbar.submit()
                elif "Quickly convert your money" in promotionTitle:
                    searchbar.send_keys("convert 374 usd to yen")
                    searchbar.submit()
                elif "Learn to cook a new recipe" in promotionTitle:
                    searchbar.send_keys("how cook pierogi")
                    searchbar.submit()
                elif "Find places to stay" in promotionTitle:
                    searchbar.send_keys("hotels rome italy")
                    searchbar.submit()
                elif "How's the economy?" in promotionTitle:
                    searchbar.send_keys("sp 500")
                    searchbar.submit()
                elif "Who won?" in promotionTitle:
                    searchbar.send_keys("braves score")
                    searchbar.submit()
                elif "Gaming time" in promotionTitle:
                    searchbar.send_keys("vampire survivors video game")
                    searchbar.submit()
                elif "Expand your vocabulary" in promotionTitle:
                    searchbar.send_keys("definition definition")
                    searchbar.submit()
                elif "What time is it?" in promotionTitle:
                    searchbar.send_keys("china time")
                    searchbar.submit()
                elif promotion["promotionType"] == "urlreward":
                    # Complete search for URL reward
                    self.activities.completeSearch()
                elif (
                    promotion["promotionType"] == "quiz"
                ):
                    # Complete different types of quizzes based on point progress max
                    if promotion["pointProgressMax"] == 10:
                        self.activities.completeABC()
                    elif promotion["pointProgressMax"] in [30, 40]:
                        self.activities.completeQuiz()
                    elif promotion["pointProgressMax"] == 50:
                        self.activities.completeThisOrThat()
                else:
                    # Default to completing search
                    self.activities.completeSearch()
                self.browser.webdriver.execute_script("window.scrollTo(0, 1080)")
                time.sleep(random.randint(5, 10))

                self.browser.utils.resetTabs()
                time.sleep(2)
            except Exception:  # pylint: disable=broad-except
                logging.error("[MORE PROMOS] Error More Promotions", exc_info=True)
                # Reset tabs in case of an exception
                self.browser.utils.resetTabs()
                continue
        incompletePromotions: list[tuple[str, str]] = []
        for promotion in self.browser.utils.getDashboardData()["morePromotions"]:  # Have to refresh
            if promotion["pointProgress"] < promotion["pointProgressMax"]:
                incompletePromotions.append((promotion["title"], promotion["promotionType"]))
        if incompletePromotions:
            Utils.sendNotification("Incomplete promotions(s)", incompletePromotions)
        logging.info("[MORE PROMOS] Exiting")
