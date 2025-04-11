import contextlib
import logging
from random import randint
from time import sleep

from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from src.browser import Browser
from src.constants import REWARDS_URL
from src.utils import (
    CONFIG,
    APPRISE,
    getAnswerCode,
    cooldown,
    ACTIVITY_TITLES_TO_QUERIES,
    IGNORED_ACTIVITIES,
)


class Activities:
    """
    Class to handle activities in MS Rewards.
    """

    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver

    def completeSearch(self):
        # Simulate completing a search activity
        pass

    def completeSurvey(self):
        # Simulate completing a survey activity
        # noinspection SpellCheckingInspection
        self.browser.utils.waitUntilClickable(By.ID, f"btoption{randint(0, 1)}").click()

    def completeQuiz(self):
        # Simulate completing a quiz activity
        with contextlib.suppress(
            TimeoutException
        ):  # Handles in case quiz was started in previous run
            startQuiz = self.browser.utils.waitUntilQuizLoads()
            self.browser.utils.click(startQuiz)
        self.browser.utils.waitUntilVisible(By.ID, "overlayPanel", 5)
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
                        correctAnswer = self.browser.utils.waitUntilClickable(
                            By.ID, f"rqAnswerOption{i}"
                        )
                        self.browser.utils.click(correctAnswer)
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

    def completeActivity(self, activity: dict) -> None:
        try:
            activityTitle = cleanupActivityTitle(activity["title"])
            logging.debug(f"activityTitle={activityTitle}")
            if activity["complete"] or activity["pointProgressMax"] == 0:
                logging.debug("Already done, returning")
                return
            if activity["attributes"].get("is_unlocked", "True") != "True":
                logging.debug("Activity locked, returning")
                if activityTitle not in ACTIVITY_TITLES_TO_QUERIES:
                    logging.warning(
                        f"Add activity title '{activityTitle}' to search mapping in relevant language file in localized_activities")
                return
            if activityTitle in IGNORED_ACTIVITIES:
                logging.debug(f"Ignoring {activityTitle}")
                return
            # Open the activity for the activity
            if "puzzle" in activityTitle.lower():
                logging.info(f"Skipping {activityTitle} because it's not supported")
                return
            if "Windows search" == activityTitle:
                # for search in {"what time is it in dublin", "what is the weather"}:
                #     pyautogui.press("win")
                #     sleep(1)
                #     pyautogui.write(search)
                #     sleep(5)
                #     pyautogui.press("enter")
                #     sleep(5)
                # pyautogui.hotkey("alt", "f4") # Close Edge
                return
            activityElement = self.browser.utils.waitUntilClickable(
                By.XPATH, f'//*[contains(text(), "{activity["title"]}")]', timeToWait=20
            )
            self.browser.utils.click(activityElement)
            self.browser.utils.switchToNewTab()
            with contextlib.suppress(TimeoutException):
                searchbar = self.browser.utils.waitUntilClickable(
                    By.ID, "sb_form_q", timeToWait=30
                )
                self.browser.utils.click(searchbar)
                searchbar.clear()
            if activityTitle in ACTIVITY_TITLES_TO_QUERIES:
                searchbar.send_keys(ACTIVITY_TITLES_TO_QUERIES[activityTitle])
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
        logging.info("[ACTIVITIES] " + "Trying to complete all activities...")
        for activity in self.browser.utils.getActivities():
            self.completeActivity(activity)
        logging.info("[ACTIVITIES] " + "Done")

        # todo Send one email for all accounts?
        if CONFIG.get("apprise.notify.incomplete-activity"):  # todo Use fancy new way
            incompleteActivities: list[str] = []
            for activity in self.browser.utils.getActivities():  # Have to refresh
                activityTitle = cleanupActivityTitle(activity["title"])
                if (
                    activityTitle not in IGNORED_ACTIVITIES
                    and activity["pointProgress"] < activity["pointProgressMax"]
                    and activity["attributes"].get("is_unlocked", "True") == "True"
                    # todo Add check whether activity was in original set, in case added in between
                ):
                    incompleteActivities.append(activityTitle)
            if incompleteActivities:
                logging.info(f"incompleteActivities: {incompleteActivities}")
                APPRISE.notify(
                    '"' + '", "'.join(incompleteActivities) + '"\n' + REWARDS_URL,
                    f"We found some incomplete activities for {self.browser.email}",
                )


def cleanupActivityTitle(activityTitle: str) -> str:
    return activityTitle.replace("\u200b", "").replace("\xa0", " ")
