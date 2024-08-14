import random
import time

from selenium.webdriver.common.by import By

from src.browser import Browser


class Activities:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver

    def openDailySetActivity(self, cardId: int):
        # Open the Daily Set activity for the given cardId
        element = self.webdriver.find_element(By.XPATH,
                                              f'//*[@id="daily-sets"]/mee-card-group[1]/div/mee-card[{cardId}]/div/card-content/mee-rewards-daily-set-item-content/div/a', )
        self.browser.utils.click(element)
        self.browser.utils.switchToNewTab(timeToWait=8)

    def openMorePromotionsActivity(self, cardId: int):
        # Open the More Promotions activity for the given cardId
        element = self.webdriver.find_element(By.CSS_SELECTOR,
                                              f"#more-activities > .m-card-group > .ng-scope:nth-child({cardId + 1}) .ds-card-sec")
        self.browser.utils.click(element)
        self.browser.utils.switchToNewTab(timeToWait=5)

    def completeSearch(self):
        # Simulate completing a search activity
        time.sleep(random.randint(10, 15))
        self.browser.utils.closeCurrentTab()

    def completeSurvey(self):
        # Simulate completing a survey activity
        # noinspection SpellCheckingInspection
        self.webdriver.find_element(By.ID, f"btoption{random.randint(0, 1)}").click()
        time.sleep(random.randint(10, 15))
        self.browser.utils.closeCurrentTab()

    def completeQuiz(self):
        # Simulate completing a quiz activity
        startQuiz = self.browser.utils.waitUntilQuizLoads()
        startQuiz.click()
        self.browser.utils.waitUntilVisible(
            By.XPATH, '//*[@id="currentQuestionContainer"]/div/div[1]', 5
        )
        time.sleep(random.randint(10, 15))
        numberOfQuestions = self.webdriver.execute_script(
            "return _w.rewardsQuizRenderInfo.maxQuestions"
        )
        numberOfOptions = self.webdriver.execute_script(
            "return _w.rewardsQuizRenderInfo.numberOfOptions"
        )
        for question in range(numberOfQuestions):
            if numberOfOptions == 8:
                answers = []
                for i in range(numberOfOptions):
                    isCorrectOption = self.webdriver.find_element(
                        By.ID, f"rqAnswerOption{i}"
                    ).get_attribute("iscorrectoption")
                    if isCorrectOption and isCorrectOption.lower() == "true":
                        answers.append(f"rqAnswerOption{i}")
                for answer in answers:
                    self.webdriver.find_element(By.ID, answer).click()
                    time.sleep(random.randint(10, 15))
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
                        self.webdriver.find_element(By.ID, f"rqAnswerOption{i}").click()
                        time.sleep(random.randint(10, 15))

                        self.browser.utils.waitUntilQuestionRefresh()
                        break
            if question + 1 != numberOfQuestions:
                time.sleep(random.randint(10, 15))
        time.sleep(random.randint(10, 15))
        self.browser.utils.closeCurrentTab()

    def completeABC(self):
        # Simulate completing an ABC activity
        counter = self.webdriver.find_element(
            By.XPATH, '//*[@id="QuestionPane0"]/div[2]'
        ).text[:-1][1:]
        numberOfQuestions = max(int(s) for s in counter.split() if s.isdigit())
        for question in range(numberOfQuestions):
            self.webdriver.find_element(
                By.ID, f"questionOptionChoice{question}{random.randint(0, 2)}"
            ).click()
            time.sleep(random.randint(10, 15))
            self.webdriver.find_element(By.ID, f"nextQuestionbtn{question}").click()
            time.sleep(random.randint(10, 15))
        time.sleep(random.randint(1, 7))
        self.browser.utils.closeCurrentTab()

    def completeThisOrThat(self):
        # Simulate completing a This or That activity
        startQuiz = self.browser.utils.waitUntilQuizLoads()
        startQuiz.click()
        self.browser.utils.waitUntilVisible(
            By.XPATH, '//*[@id="currentQuestionContainer"]/div/div[1]', 10
        )
        time.sleep(random.randint(10, 15))
        for _ in range(10):
            correctAnswerCode = self.webdriver.execute_script(
                "return _w.rewardsQuizRenderInfo.correctAnswer"
            )
            answer1, answer1Code = self.getAnswerAndCode("rqAnswerOption0")
            answer2, answer2Code = self.getAnswerAndCode("rqAnswerOption1")
            if answer1Code == correctAnswerCode:
                answer1.click()
                time.sleep(random.randint(10, 15))
            elif answer2Code == correctAnswerCode:
                answer2.click()
                time.sleep(random.randint(10, 15))

        time.sleep(random.randint(10, 15))
        self.browser.utils.closeCurrentTab()

    def getAnswerAndCode(self, answerId: str) -> tuple:
        # Helper function to get answer element and its code
        answerEncodeKey = self.webdriver.execute_script("return _G.IG")
        answer = self.webdriver.find_element(By.ID, answerId)
        answerTitle = answer.get_attribute("data-option")
        if answerTitle is not None:
            return (
                answer,
                self.browser.utils.getAnswerCode(answerEncodeKey, answerTitle),
            )
        else:
            # todo - throw exception?
            return answer, None
