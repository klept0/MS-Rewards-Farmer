import contextlib
import logging
from random import randint
from time import sleep

import pyautogui
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from src.browser import Browser
from src.constants import REWARDS_URL
from src.utils import CONFIG, sendNotification, getAnswerCode, cooldown


class Activities:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver

    def openDailySetActivity(self, cardId: int):
        # Open the Daily Set activity for the given cardId
        cardId += 1
        element = self.webdriver.find_element(
            By.XPATH,
            f'//*[@id="daily-sets"]/mee-card-group[1]/div/mee-card[{cardId}]/div/card-content/mee-rewards-daily-set-item-content/div/a',
        )
        self.browser.utils.click(element)
        self.browser.utils.switchToNewTab()

    def openMorePromotionsActivity(self, cardId: int):
        cardId += 1
        # Open the More Promotions activity for the given cardId
        element = self.webdriver.find_element(
            By.CSS_SELECTOR,
            f"#more-activities > .m-card-group > .ng-scope:nth-child({cardId}) .ds-card-sec",
        )
        self.browser.utils.click(element)
        self.browser.utils.switchToNewTab()

    def openExploreOnBing(self, cardId: int) -> None:
        cardId -= 10
        element = self.webdriver.find_element(
            By.XPATH,
            f'//*[@id="explore-on-bing"]/mee-card-group/div/mee-card[{cardId}]',
        )
        self.browser.utils.click(element)
        self.browser.utils.switchToNewTab()

    def completeSearch(self):
        # Simulate completing a search activity
        pass

    def completeSurvey(self):
        # Simulate completing a survey activity
        # noinspection SpellCheckingInspection
        self.webdriver.find_element(By.ID, f"btoption{randint(0, 1)}").click()

    def completeQuiz(self):
        # Simulate completing a quiz activity
        with contextlib.suppress(
            TimeoutException
        ):  # Handles in case quiz was started in previous run
            startQuiz = self.browser.utils.waitUntilQuizLoads()
            self.browser.utils.click(startQuiz)
        maxQuestions = self.webdriver.execute_script(
            "return _w.rewardsQuizRenderInfo.maxQuestions"
        )
        numberOfOptions = self.webdriver.execute_script(
            "return _w.rewardsQuizRenderInfo.numberOfOptions"
        )
        while True:
            correctlyAnsweredQuestionCount: int = self.webdriver.execute_script(
                "return _w.rewardsQuizRenderInfo.CorrectlyAnsweredQuestionCount"
            )

            if correctlyAnsweredQuestionCount == maxQuestions:
                return

            self.browser.utils.waitUntilQuestionRefresh()

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
                        element = self.webdriver.find_element(
                            By.ID, f"rqAnswerOption{i}"
                        )
                        self.browser.utils.click(element)
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
        with contextlib.suppress(
            TimeoutException
        ):  # Handles in case quiz was started in previous run
            startQuiz = self.browser.utils.waitUntilQuizLoads()
            self.browser.utils.click(startQuiz)
        self.browser.utils.waitUntilQuestionRefresh()
        for _ in range(10):
            correctAnswerCode = self.webdriver.execute_script(
                "return _w.rewardsQuizRenderInfo.correctAnswer"
            )
            answer1, answer1Code = self.getAnswerAndCode("rqAnswerOption0")
            answer2, answer2Code = self.getAnswerAndCode("rqAnswerOption1")
            answerToClick: WebElement
            if answer1Code == correctAnswerCode:
                answerToClick = answer1
            elif answer2Code == correctAnswerCode:
                answerToClick = answer2

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

    def completeActivity(self, activity: dict, activities: list[dict]) -> None:
        try:
            activityTitle = cleanupActivityTitle(activity["title"])
            logging.debug(f"activityTitle={activityTitle}")
            if activity["complete"] or activity["pointProgressMax"] == 0:
                logging.debug("Already done, returning")
                return
            if not bool(activity["attributes"].get("is_unlocked", True)):
                logging.debug("Activity locked, returning")
                return
            if activityTitle in CONFIG.activities.ignore:
                logging.debug(f"Ignoring {activityTitle}")
                return
            # Open the activity for the activity
            cardId = activities.index(activity)
            isPuzzle = "puzzle" in activityTitle.lower()
            isDailySet = bool(activity["attributes"].get("daily_set_date", False))
            isExploreOnBing = bool(
                activity["attributes"].get("isExploreOnBingTask", False)
            )
            if isPuzzle:
                logging.info(f"Skipping {activityTitle} because it's not supported")
                return
            elif "Windows search" == activityTitle:
                for search in {"what time is it", "what is the weather"}:
                    pyautogui.press("win")
                    sleep(10)
                    pyautogui.write(search)
                    pyautogui.press("enter")
            elif isDailySet:
                self.openDailySetActivity(cardId)
            elif isExploreOnBing:
                self.openExploreOnBing(cardId)
            else:
                self.openMorePromotionsActivity(cardId)
            with contextlib.suppress(TimeoutException):
                searchbar = self.browser.utils.waitUntilClickable(By.ID, "sb_form_q")
                self.browser.utils.click(searchbar)
                searchbar.clear()
            if activityTitle in CONFIG.activities.search:
                searchbar.send_keys(CONFIG.activities.search[activityTitle])
                sleep(2)
                searchbar.submit()
            elif "poll" in activityTitle:
                # Complete survey for a specific scenario
                self.completeSurvey()
            elif activity["promotionType"] == "urlreward":
                # Complete search for URL reward
                self.completeSearch()
            elif activity["promotionType"] == "quiz":
                # Complete different types of quizzes based on point progress max
                if activity["pointProgressMax"] == 10:
                    self.completeABC()
                elif activity["pointProgressMax"] in [30, 40]:
                    self.completeQuiz()
                elif activity["pointProgressMax"] == 50:
                    self.completeThisOrThat()
            else:
                # Default to completing search
                self.completeSearch()
            logging.debug("Done")
        except Exception:
            logging.error(f"[ACTIVITY] Error doing {activityTitle}", exc_info=True)
            logging.debug(f"activity={activity}")
            return
        finally:
            self.browser.utils.resetTabs()
        cooldown()

    def completeActivities(self):
        logging.info("[DAILY SET] " + "Trying to complete the Daily Set...")
        dailySetPromotions = self.browser.utils.getDailySetPromotions()
        self.browser.utils.goToRewards()
        for activity in dailySetPromotions:
            self.completeActivity(activity, dailySetPromotions)
        logging.info("[DAILY SET] Done")

        logging.info("[MORE PROMOS] " + "Trying to complete More Promotions...")
        morePromotions: list[dict] = self.browser.utils.getMorePromotions()
        self.browser.utils.goToRewards()
        for activity in morePromotions:
            self.completeActivity(activity, morePromotions)
        logging.info("[MORE PROMOS] Done")

        # todo Send one email for all accounts?
        # fixme This is falsely considering some activities incomplete when complete
        if CONFIG.get("apprise.notify.incomplete-activity"):
            incompleteActivities: list[str] = []
            for activity in (
                self.browser.utils.getDailySetPromotions()
                + self.browser.utils.getMorePromotions()
            ):  # Have to refresh
                activityTitle = cleanupActivityTitle(activity["title"])
                if (
                    activityTitle not in CONFIG.activities.ignore
                    and activity["pointProgress"] < activity["pointProgressMax"]
                    and bool(activity["attributes"].get("is_unlocked", True))
                ):
                    incompleteActivities.append(activityTitle)
            if incompleteActivities:
                logging.info(f"incompleteActivities: {incompleteActivities}")
                sendNotification(
                    f"We found some incomplete activities for {self.browser.email}",
                    '"' + '", "'.join(incompleteActivities) + '"\n' + REWARDS_URL,
                )


def cleanupActivityTitle(activityTitle: str) -> str:
    return activityTitle.replace("\u200b", "").replace("\xa0", " ")
