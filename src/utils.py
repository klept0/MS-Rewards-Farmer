import contextlib
import json
import locale as pylocale
import logging
import re
import time
from argparse import Namespace
from pathlib import Path
from typing import Any

import requests
import yaml
from apprise import Apprise
from requests import Session
from requests.adapters import HTTPAdapter
from selenium.common import NoSuchElementException, TimeoutException, ElementClickInterceptedException, \
    ElementNotInteractableException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from urllib3 import Retry

from .constants import REWARDS_URL
from .constants import SEARCH_URL


class Utils:
    args: Namespace

    def __init__(self, webdriver: WebDriver):
        self.webdriver = webdriver
        with contextlib.suppress(Exception):
            locale = pylocale.getdefaultlocale()[0]
            pylocale.setlocale(pylocale.LC_NUMERIC, locale)

        self.config = self.loadConfig()

    @staticmethod
    def getProjectRoot() -> Path:
        return Path(__file__).parent.parent

    @staticmethod
    def loadConfig(config_file=getProjectRoot() / "config.yaml") -> dict:
        with open(config_file, "r") as file:
            return yaml.safe_load(file)

    @staticmethod
    def sendNotification(title, body) -> None:
        if Utils.args.disable_apprise:
            return
        apprise = Apprise()
        urls: list[str] = Utils.loadConfig().get("apprise", {}).get("urls", [])
        for url in urls:
            apprise.add(url)
        apprise.notify(body=body, title=title)

    def waitUntilVisible(
        self, by: str, selector: str, timeToWait: float = 10
    ) -> WebElement:
        return WebDriverWait(self.webdriver, timeToWait).until(
            expected_conditions.visibility_of_element_located((by, selector))
        )

    def waitUntilClickable(
        self, by: str, selector: str, timeToWait: float = 10
    ) -> WebElement:
        return WebDriverWait(self.webdriver, timeToWait).until(
            expected_conditions.element_to_be_clickable((by, selector))
        )

    def checkIfTextPresentAfterDelay(self, text: str, timeToWait: float = 10) -> bool:
        time.sleep(timeToWait)
        text_found = re.search(text, self.webdriver.page_source)
        return text_found is not None

    def waitUntilQuestionRefresh(self) -> WebElement:
        return self.waitUntilVisible(By.CLASS_NAME, "rqECredits", timeToWait=20)

    def waitUntilQuizLoads(self) -> WebElement:
        return self.waitUntilVisible(By.XPATH, '//*[@id="rqStartQuiz"]')

    def resetTabs(self) -> None:
        curr = self.webdriver.current_window_handle

        for handle in self.webdriver.window_handles:
            if handle != curr:
                self.webdriver.switch_to.window(handle)
                time.sleep(0.5)
                self.webdriver.close()
                time.sleep(0.5)

        self.webdriver.switch_to.window(curr)
        time.sleep(0.5)
        self.goToRewards()

    def goToRewards(self) -> None:
        self.webdriver.get(REWARDS_URL)
        assert (
            self.webdriver.current_url == REWARDS_URL
        ), f"{self.webdriver.current_url} {REWARDS_URL}"

    def goToSearch(self) -> None:
        self.webdriver.get(SEARCH_URL)
        # assert (
        #     self.webdriver.current_url == SEARCH_URL
        # ), f"{self.webdriver.current_url} {SEARCH_URL}"  # need regex: AssertionError: https://www.bing.com/?toWww=1&redig=A5B72363182B49DEBB7465AD7520FDAA https://bing.com/

    @staticmethod
    def getAnswerCode(key: str, string: str) -> str:
        t = sum(ord(string[i]) for i in range(len(string)))
        t += int(key[-2:], 16)
        return str(t)

    def getDashboardData(self) -> dict:
        urlBefore = self.webdriver.current_url
        try:
            self.goToRewards()
            return self.webdriver.execute_script("return dashboard")
        finally:
            try:
                self.webdriver.get(urlBefore)
            except TimeoutException:
                self.goToRewards()

    def getBingInfo(self) -> Any:
        session = self.makeRequestsSession()

        for cookie in self.webdriver.get_cookies():
            session.cookies.set(cookie["name"], cookie["value"])

        response = session.get("https://www.bing.com/rewards/panelflyout/getuserinfo")

        assert response.status_code == requests.codes.ok
        return response.json()["userInfo"]

    @staticmethod
    def makeRequestsSession(session: Session = requests.session()) -> Session:
        retry = Retry(
            total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504]
        )
        session.mount(
            "https://", HTTPAdapter(max_retries=retry)
        )  # See https://stackoverflow.com/a/35504626/4164390 to finetune
        session.mount(
            "http://", HTTPAdapter(max_retries=retry)
        )  # See https://stackoverflow.com/a/35504626/4164390 to finetune
        return session

    def isLoggedIn(self) -> bool:
        # return self.getBingInfo()["isRewardsUser"]  # todo For some reason doesn't work, but doesn't involve changing url so preferred
        self.webdriver.get(
            "https://rewards.bing.com/Signin/"
        )  # changed site to allow bypassing when M$ blocks access to login.live.com randomly
        with contextlib.suppress(TimeoutException):
            self.waitUntilVisible(
                By.CSS_SELECTOR, 'html[data-role-name="RewardsPortal"]', 10
            )
            return True
        return False

    def getAccountPoints(self) -> int:
        return self.getBingInfo()["balance"]

    def getGoalPoints(self) -> int:
        return self.getDashboardData()["userStatus"]["redeemGoal"]["price"]

    def getGoalTitle(self) -> str:
        return self.getDashboardData()["userStatus"]["redeemGoal"]["title"]

    def tryDismissAllMessages(self) -> None:
        buttons = [
            (By.ID, "iLandingViewAction"),
            (By.ID, "iShowSkip"),
            (By.ID, "iNext"),
            (By.ID, "iLooksGood"),
            (By.ID, "idSIButton9"),
            (By.ID, "bnp_btn_accept"),
            (By.ID, "acceptButton"),
        ]
        for button in buttons:
            try:
                elements = self.webdriver.find_elements(by=button[0], value=button[1])
            except (NoSuchElementException, ElementNotInteractableException):  # Expected?
                logging.debug("", exc_info=True)
                continue
            for element in elements:
                element.click()
        self.tryDismissCookieBanner()
        self.tryDismissBingCookieBanner()

    def tryDismissCookieBanner(self) -> None:
        with contextlib.suppress(NoSuchElementException, ElementNotInteractableException):  # Expected
            self.webdriver.find_element(By.ID, "cookie-banner").find_element(
                By.TAG_NAME, "button"
            ).click()

    def tryDismissBingCookieBanner(self) -> None:
        with contextlib.suppress(NoSuchElementException, ElementNotInteractableException):  # Expected
            self.webdriver.find_element(By.ID, "bnp_btn_accept").click()

    def switchToNewTab(self, timeToWait: float = 0) -> None:
        time.sleep(0.5)
        self.webdriver.switch_to.window(window_name=self.webdriver.window_handles[1])
        if timeToWait > 0:
            time.sleep(timeToWait)

    def closeCurrentTab(self) -> None:
        self.webdriver.close()
        time.sleep(0.5)
        self.webdriver.switch_to.window(window_name=self.webdriver.window_handles[0])
        time.sleep(0.5)

    def visitNewTab(self, timeToWait: float = 0) -> None:
        self.switchToNewTab(timeToWait)
        self.closeCurrentTab()

    @staticmethod
    def formatNumber(number, num_decimals=2) -> str:
        return pylocale.format_string(
            f"%10.{num_decimals}f", number, grouping=True
        ).strip()

    @staticmethod
    def getBrowserConfig(sessionPath: Path) -> dict | None:
        configFile = sessionPath / "config.json"
        if not configFile.exists():
            return
        with open(configFile, "r") as f:
            return json.load(f)

    @staticmethod
    def saveBrowserConfig(sessionPath: Path, config: dict) -> None:
        configFile = sessionPath / "config.json"
        with open(configFile, "w") as f:
            json.dump(config, f)

    def click(self, element: WebElement) -> None:
        try:
            element.click()
        except ElementClickInterceptedException:
            self.tryDismissAllMessages()
            element.click()
