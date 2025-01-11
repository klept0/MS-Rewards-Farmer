import contextlib
import logging
from random import randint
from time import sleep

from selenium.common import TimeoutException 
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.browser import Browser
from src.constants import REWARDS_URL
from src.utils import CONFIG, sendNotification, getAnswerCode

# todo These are US-English specific, maybe there's a good way to internationalize
ACTIVITY_TITLE_TO_SEARCH = {
    "Black Friday shopping": "black friday deals",
    "Discover open job roles": "jobs at microsoft",
    "Expand your vocabulary": "define demure",
    "Find places to stay": "hotels rome italy",
    "Find somewhere new to explore": "directions to new york",
    "Gaming time": "vampire survivors video game",
    "Get your shopping done faster": "new iphone",
    "Houses near you": "apartments manhattan",
    "How's the economy?": "sp 500",
    "Learn to cook a new recipe": "how cook pierogi",
    "Let's watch that movie again!": "aliens movie",
    "Plan a quick getaway": "flights nyc to paris",
    "Prepare for the weather": "weather tomorrow",
    "Quickly convert your money": "convert 374 usd to yen",
    "Search the lyrics of a song": "black sabbath supernaut lyrics",
    "Stay on top of the elections": "election news latest",
    "Too tired to cook tonight?": "Pizza Hut near me",
    "Translate anything": "translate pencil sharpener to spanish",
    "What time is it?": "china time",
    "What's for Thanksgiving dinner?": "pumpkin pie recipe",
    "Who won?": "braves score",
    "You can track your package": "usps tracking",
}


class Activities:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver

    def openDailySetActivity(self, cardId: int):
            # Count total number of cards
            total_cards = len(self.webdriver.find_elements(By.XPATH, '//*[@id="daily-sets"]/mee-card-group[1]/div/mee-card'))
            logging.info(f"Total number of Daily Set activity cards: {total_cards}.")

            # Open the Daily Set activity for the given cardId
            cardId += 1
            element = self.webdriver.find_element(
                By.XPATH,
                f'//*[@id="daily-sets"]/mee-card-group[1]/div/mee-card[{cardId}]/div/card-content/mee-rewards-daily-set-item-content/div/a',
            )

            logging.info(f"Attempting to click on Daily Set activity card {cardId}.")
            # Perform Ctrl + Click (Strg+Linksklick)
            ActionChains(self.webdriver).key_down(Keys.CONTROL).click(element).key_up(Keys.CONTROL).perform()
            logging.info(f"Clicked on Daily Set activity card {cardId}.")

            # Mark activity as complete after the click
            logging.info(f"Marking card {cardId} as complete.")
            self.webdriver.execute_script("arguments[0].setAttribute('complete', 'true');", element)

            # Wait for new tab to open
            original_window = self.webdriver.current_window_handle
            all_windows = self.webdriver.window_handles

            # Check if a new tab was opened
            if len(all_windows) > 1:
                logging.info(f"New tab detected after clicking card {cardId}.")
                # Switch to the new tab
                self.webdriver.switch_to.window(all_windows[-1])
                logging.info(f"Switched to the new tab for card {cardId}.")

                # Close the new tab
                self.webdriver.close()
                logging.info(f"Closed the new tab for card {cardId}.")

                # Switch back to the original tab
                self.webdriver.switch_to.window(original_window)
                logging.info(f"Switched back to the original tab after handling card {cardId}.")
            else:
                logging.info(f"No new tab was opened for card {cardId}.")

    def openMorePromotionsActivity(self, cardId: int):
        cardId += 1
        # Open the More Promotions activity for the given cardId
        element = self.webdriver.find_element(
            By.CSS_SELECTOR,
            f"#more-activities > .m-card-group > .ng-scope:nth-child({cardId}) .ds-card-sec",
        )
        self.browser.utils.click(element)
        self.browser.utils.switchToNewTab()

    def completeSearch(self):
        # Simulate completing a search activity
        pass

    def completeSurvey(self):
        # Simulate completing a survey activity
        try:
            survey_option = WebDriverWait(self.webdriver, 10).until(
                EC.element_to_be_clickable((By.ID, f"btoption{randint(0, 1)}"))
            )
            survey_option.click()
        except TimeoutException:
            logging.error("Survey option not found or not clickable.")

    def completeQuiz(self):
        # Simulate completing a quiz activity
        with contextlib.suppress(TimeoutException):
            startQuiz = self.browser.utils.waitUntilQuizLoads()
            self.browser.utils.click(startQuiz)
        self.browser.utils.waitUntilVisible(By.ID, "overlayPanel", 5)
        currentQuestionNumber: int = self.webdriver.execute_script(
            "return _w.rewardsQuizRenderInfo.currentQuestionNumber"
        )
        maxQuestions = self.webdriver.execute_script(
            "return _w.rewardsQuizRenderInfo.maxQuestions"
        )
        numberOfOptions = self.webdriver.execute_script(
            "return _w.rewardsQuizRenderInfo.numberOfOptions"
        )
        for _ in range(currentQuestionNumber, maxQuestions + 1):
            if numberOfOptions == 8:
                answers = []
                for i in range(numberOfOptions):
                    isCorrectOption = self.webdriver.find_element(
                        By.ID, f"rqAnswerOption{i}"
                    ).get_attribute("iscorrectoption")
                    if isCorrectOption and isCorrectOption.lower() == "true":
                        answers.append(f"rqAnswerOption{i}")
                for answer in answers:
                    element = self.webdriver.find_element(By.ID, answer)
                    self.browser.utils.click(element)
                    self.browser.utils.waitUntilQuestionRefresh()
            elif numberOfOptions in [2, 3, 4]:
                correctOption = self.webdriver.execute_script(
                    "return _w.rewardsQuizRenderInfo.correctAnswer"
                )
                for i in range(numberOfOptions):
                    if (
                        self.webdriver.find_element(
                            By.ID, f"rqAnswerOption{i}"
                        ).get_attribute("data-option")
                        == correctOption
                    ):
                        element = self.webdriver.find_element(By.ID, f"rqAnswerOption{i}")
                        self.browser.utils.click(element)
                        self.browser.utils.waitUntilQuestionRefresh()
                        break

    def completeABC(self):
        # Simulate completing an ABC activity
        counter = self.webdriver.find_element(
            By.XPATH, '//*[@id="QuestionPane0"]/div[2]'
        ).text[:-1][1:]
        numberOfQuestions = max(int(s) for s in counter.split() if s.isdigit())
        for question in range(numberOfQuestions):
            element = self.webdriver.find_element(
                By.ID, f"questionOptionChoice{question}{randint(0, 2)}"
            )
            self.browser.utils.click(element)
            sleep(randint(10, 15))
            element = self.webdriver.find_element(By.ID, f"nextQuestionbtn{question}")
            self.browser.utils.click(element)
            sleep(randint(10, 15))

    def completeThisOrThat(self):
        # Simulate completing a This or That activity
        startQuiz = self.browser.utils.waitUntilQuizLoads()
        self.browser.utils.click(startQuiz)
        self.browser.utils.waitUntilVisible(
            By.XPATH, '//*[@id="currentQuestionContainer"]/div/div[1]', 10
        )
        sleep(randint(10, 15))
        for _ in range(10):
            correctAnswerCode = self.webdriver.execute_script(
                "return _w.rewardsQuizRenderInfo.correctAnswer"
            )
            answer1, answer1Code = self.getAnswerAndCode("rqAnswerOption0")
            answer2, answer2Code = self.getAnswerAndCode("rqAnswerOption1")

            answerToClick = answer1 if answer1Code == correctAnswerCode else answer2

            self.browser.utils.click(answerToClick)
            sleep(randint(10, 15))

    def getAnswerAndCode(self, answerId: str) -> tuple[WebElement, str]:
        # Helper function to get answer element and its code
        answerEncodeKey = self.webdriver.execute_script("return _G.IG")
        answer = self.webdriver.find_element(By.ID, answerId)
        answerTitle = answer.get_attribute("data-option")
        return (
            answer,
            getAnswerCode(answerEncodeKey, answerTitle),
        )

    def doActivity(self, activity: dict, activities: list[dict]) -> None:
        try:
            activityTitle = cleanupActivityTitle(activity["title"])
            logging.info(f"Processing activity: {activityTitle}")
            
            if activity["complete"] is True or activity["pointProgressMax"] == 0:
                logging.info("Activity already completed. Skipping.")
                return
            
            if activityTitle in CONFIG.get("apprise").get("notify").get("incomplete-activity").get("ignore"):
                logging.info(f"Ignoring activity: {activityTitle}")
                return

            cardId = activities.index(activity)
            isDailySet = "daily_set_date" in activity["attributes"] and activity["attributes"]["daily_set_date"]

            if isDailySet:
                self.openDailySetActivity(cardId)
            else:
                self.openMorePromotionsActivity(cardId)

            # Handle specific activity types
            try:
                if activityTitle in ACTIVITY_TITLE_TO_SEARCH:
                    searchbar = self.browser.utils.waitUntilClickable(By.ID, "sb_form_q", timeout=10)
                    searchbar.send_keys(ACTIVITY_TITLE_TO_SEARCH[activityTitle])
                    sleep(2)
                    searchbar.submit()
                elif "poll" in activityTitle:
                    logging.info(f"[ACTIVITY] Completing poll for card {cardId}")
                    self.completeSurvey()
                elif activity["promotionType"] == "urlreward":
                    self.completeSearch()
                elif activity["promotionType"] == "quiz":
                    if activity["pointProgressMax"] == 10:
                        self.completeABC()
                    elif activity["pointProgressMax"] in [30, 40]:
                        self.completeQuiz()
                    elif activity["pointProgressMax"] == 50:
                        self.completeThisOrThat()
                else:
                    self.completeSearch()
            except Exception as e:
                logging.error(f"Error while handling activity {activityTitle}: {e}")
            
        except Exception as e:
            logging.error(f"[ACTIVITY] Error processing activity {activityTitle}: {e}", exc_info=True)
        
        # Shorten sleep time or remove it entirely
        sleep(randint(2, 5))
        logging.info("Resetting tabs.")
        self.browser.utils.resetTabs()
        logging.info("Finished processing activity.")

    def completeActivities(self):
        logging.info("[DAILY SET] " + "Trying to complete the Daily Set...[acitivties.py]")
        dailySetPromotions = self.browser.utils.getDailySetPromotions()
        self.browser.utils.goToRewards()
        for activity in dailySetPromotions:
            self.doActivity(activity, dailySetPromotions)
        logging.info("[DAILY SET] Done")

        logging.info("[MORE PROMOS] " + "Trying to complete More Promotions...")
        morePromotions: list[dict] = self.browser.utils.getMorePromotions()
        self.browser.utils.goToRewards()
        for activity in morePromotions:
            self.doActivity(activity, morePromotions)
        logging.info("[MORE PROMOS] Done")

        # todo Send one email for all accounts?
        # fixme This is falsely considering some activities incomplete when complete
        if (
            CONFIG.get("apprise")
            .get("notify")
            .get("incomplete-activity")
            .get("enabled")
        ):
            incompleteActivities: dict[str, tuple[str, str, str]] = {}
            for activity in (
                self.browser.utils.getDailySetPromotions()
                + self.browser.utils.getMorePromotions()
            ):  # Have to refresh
                if activity["pointProgress"] < activity["pointProgressMax"]:
                    incompleteActivities[cleanupActivityTitle(activity["title"])] = (
                        activity["promotionType"],
                        activity["pointProgress"],
                        activity["pointProgressMax"],
                    )
            for incompleteActivityToIgnore in (
                CONFIG.get("apprise")
                .get("notify")
                .get("incomplete-activity")
                .get("ignore")
            ):
                incompleteActivities.pop(incompleteActivityToIgnore, None)
            if incompleteActivities:
                logging.info(f"incompleteActivities: {incompleteActivities}")
                sendNotification(
                    f"We found some incomplete activities for {self.browser.username}",
                    str(incompleteActivities) + "\n" + REWARDS_URL,
                )


def cleanupActivityTitle(activityTitle: str) -> str:
    return activityTitle.replace("\u200b", "").replace("\xa0", " ")
