import contextlib
import json
import locale as pylocale
import logging
import re
import time
from argparse import Namespace
from datetime import date
from pathlib import Path
from types import MappingProxyType
from typing import Any

import requests
import yaml
from apprise import Apprise
from requests import Session
from requests.adapters import HTTPAdapter
from selenium.common import (
    NoSuchElementException,
    TimeoutException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from urllib3 import Retry

from .constants import REWARDS_URL
from .constants import SEARCH_URL

DEFAULT_CONFIG: MappingProxyType = MappingProxyType(
    {
        "apprise": {
            "notify": {
                "incomplete-activity": {"enabled": True, "ignore-safeguard-info": True},
                "uncaught-exception": {"enabled": True},
            },
            "summary": "ON_ERROR",
        },
        "default": {"geolocation": "US"},
        "logging": {"level": "INFO"},
        "retries": {
            "base_delay_in_seconds": 120,
            "max": 4,
            "strategy": "EXPONENTIAL",
        },
    }
)
DEFAULT_PRIVATE_CONFIG: MappingProxyType = MappingProxyType(
    {
        "apprise": {
            "urls": [],
        },
    }
)


class Utils:
    args: Namespace

    def __init__(self, webdriver: WebDriver):
        self.webdriver = webdriver
        with contextlib.suppress(Exception):
            locale = pylocale.getdefaultlocale()[0]
            pylocale.setlocale(pylocale.LC_NUMERIC, locale)

        # self.config = self.loadConfig()

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

    # Prefer getBingInfo if possible
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

    def getDailySetPromotions(self) -> list[dict]:
        return self.getDashboardData()["dailySetPromotions"][
            date.today().strftime("%m/%d/%Y")
        ]

    def getMorePromotions(self) -> list[dict]:
        return self.getDashboardData()["morePromotions"]

    # Not reliable
    def getBingInfo(self) -> Any:
        session = makeRequestsSession()

        for cookie in self.webdriver.get_cookies():
            session.cookies.set(cookie["name"], cookie["value"])

        response = session.get("https://www.bing.com/rewards/panelflyout/getuserinfo")

        assert response.status_code == requests.codes.ok
        # fixme Add more asserts
        # todo Add fallback to src.utils.Utils.getDashboardData (slower but more reliable)
        return response.json()

    def isLoggedIn(self) -> bool:
        if self.getBingInfo()["isRewardsUser"]:  # faster, if it works
            return True
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
        return self.getDashboardData()["userStatus"]["availablePoints"]

    def getGoalPoints(self) -> int:
        return self.getDashboardData()["userStatus"]["redeemGoal"]["price"]

    def getGoalTitle(self) -> str:
        return self.getDashboardData()["userStatus"]["redeemGoal"]["title"]

    def tryDismissAllMessages(self) -> None:
        byValues = [
            (By.ID, "iLandingViewAction"),
            (By.ID, "iShowSkip"),
            (By.ID, "iNext"),
            (By.ID, "iLooksGood"),
            (By.ID, "idSIButton9"),
            (By.ID, "bnp_btn_accept"),
            (By.ID, "acceptButton"),
            (By.CSS_SELECTOR, ".dashboardPopUpPopUpSelectButton"),
        ]
        for byValue in byValues:
            dismissButtons = []
            with contextlib.suppress(NoSuchElementException):
                dismissButtons = self.webdriver.find_elements(
                    by=byValue[0], value=byValue[1]
                )
            for dismissButton in dismissButtons:
                dismissButton.click()
        with contextlib.suppress(NoSuchElementException):
            self.webdriver.find_element(By.ID, "cookie-banner").find_element(
                By.TAG_NAME, "button"
            ).click()

    def switchToNewTab(self, timeToWait: float = 15, closeTab: bool = False) -> None:
        time.sleep(timeToWait)
        self.webdriver.switch_to.window(window_name=self.webdriver.window_handles[1])
        if closeTab:
            self.closeCurrentTab()

    def closeCurrentTab(self) -> None:
        self.webdriver.close()
        time.sleep(0.5)
        self.webdriver.switch_to.window(window_name=self.webdriver.window_handles[0])
        time.sleep(0.5)

    def click(self, element: WebElement) -> None:
        try:
            WebDriverWait(self.webdriver, 10).until(
                expected_conditions.element_to_be_clickable(element)
            )
            element.click()
        except (ElementClickInterceptedException, ElementNotInteractableException):
            self.tryDismissAllMessages()
            WebDriverWait(self.webdriver, 10).until(
                expected_conditions.element_to_be_clickable(element)
            )
            element.click()


def getProjectRoot() -> Path:
    return Path(__file__).parent.parent


def loadYaml(path: Path) -> dict:
    with open(path, "r") as file:
        yamlContents = yaml.safe_load(file)
        if not yamlContents:
            logging.info(f"{yamlContents} is empty")
            yamlContents = {}
        return yamlContents


def loadConfig(
    configFilename="config.yaml", defaultConfig=DEFAULT_CONFIG
) -> MappingProxyType:
    configFile = getProjectRoot() / configFilename
    try:
        return MappingProxyType(defaultConfig | loadYaml(configFile))
    except OSError:
        logging.info(f"{configFile} doesn't exist, returning defaults")
        return defaultConfig


def loadPrivateConfig() -> MappingProxyType:
    return loadConfig("config-private.yaml", DEFAULT_PRIVATE_CONFIG)


def sendNotification(title: str, body: str, e: Exception = None) -> None:
    if Utils.args.disable_apprise or (
        e
        and not CONFIG.get("apprise")
        .get("notify")
        .get("uncaught-exception")
        .get("enabled")
    ):
        return
    apprise = Apprise()
    urls: list[str] = PRIVATE_CONFIG.get("apprise").get("urls")
    if not urls:
        logging.debug("No urls found, not sending notification")
        return
    for url in urls:
        apprise.add(url)
    assert apprise.notify(title=str(title), body=str(body))


def getAnswerCode(key: str, string: str) -> str:
    t = sum(ord(string[i]) for i in range(len(string)))
    t += int(key[-2:], 16)
    return str(t)


def formatNumber(number, num_decimals=2) -> str:
    return pylocale.format_string(f"%10.{num_decimals}f", number, grouping=True).strip()


def getBrowserConfig(sessionPath: Path) -> dict | None:
    configFile = sessionPath / "config.json"
    if not configFile.exists():
        return
    with open(configFile, "r") as f:
        return json.load(f)


def saveBrowserConfig(sessionPath: Path, config: dict) -> None:
    configFile = sessionPath / "config.json"
    with open(configFile, "w") as f:
        json.dump(config, f)


def makeRequestsSession(session: Session = requests.session()) -> Session:
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[
            500,
            502,
            503,
            504,
        ],  # todo Use global retries from config
    )
    session.mount(
        "https://", HTTPAdapter(max_retries=retry)
    )  # See https://stackoverflow.com/a/35504626/4164390 to finetune
    session.mount(
        "http://", HTTPAdapter(max_retries=retry)
    )  # See https://stackoverflow.com/a/35504626/4164390 to finetune
    return session


CONFIG = loadConfig()
PRIVATE_CONFIG = loadPrivateConfig()
