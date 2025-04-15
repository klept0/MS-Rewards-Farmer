import contextlib
import json
import locale as pylocale
import logging
import random
import re
import shutil
import sys
import time
from argparse import Namespace, ArgumentParser
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any, Self

import psutil
import requests
import yaml
from apprise import Apprise
from requests import Session, JSONDecodeError
from requests.adapters import HTTPAdapter
from selenium.common import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from urllib3 import Retry

from .constants import REWARDS_URL, SEARCH_URL

PREFER_BING_INFO = True


class Config(dict):
    """
    A class that extends the built-in dict class to provide additional functionality
    (such as nested dictionaries and lists, YAML loading, and attribute access)
    to make it easier to work with configuration data.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, value in self.items():
            if isinstance(value, dict):
                self[key] = self.__class__(value)
            if isinstance(value, list):
                for i, v in enumerate(value):
                    if isinstance(v, dict):
                        value[i] = self.__class__(v)

    def __or__(self, other):
        new = deepcopy(self)
        for key in other:
            if key in new:
                if isinstance(new[key], dict) and isinstance(other[key], dict):
                    new[key] = new[key] | other[key]
                    continue
            if isinstance(other[key], dict):
                new[key] = self.__class__(other[key])
                continue
            if isinstance(other[key], list):
                new[key] = self.configifyList(other[key])
                continue
            new[key] = other[key]
        return new

    def __getattribute__(self, item):
        if item in self:
            return self[item]
        return super().__getattribute__(item)

    def __setattr__(self, key, value):
        if isinstance(value, dict):
            value = self.__class__(value)
        if isinstance(value, list):
            value = self.configifyList(value)
        self[key] = value

    def __getitem__(self, item):
        if not isinstance(item, str) or not "." in item:
            return super().__getitem__(item)
        item: str
        items = item.split(".")
        found = super().__getitem__(items[0])
        for child_items in items[1:]:
            found = found.__getitem__(child_items)
        return found

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            value = self.__class__(value)
        if isinstance(value, list):
            value = self.configifyList(value)
        if not isinstance(key, str) or not "." in key:
            super().__setitem__(key, value)
            return
        item: str
        items = key.split(".")
        found = super().__getitem__(items[0])
        for item in items[1:-1]:
            found = found.__getitem__(item)
        found.__setitem__(items[-1], value)

    @classmethod
    def fromYaml(cls, path: Path) -> Self:
        if not path.exists() or not path.is_file():
            return cls()
        with open(path, encoding="utf-8") as f:
            yamlContents = yaml.safe_load(f)
            if not yamlContents:
                return cls()
            return cls(yamlContents)

    @classmethod
    def configifyList(cls, listToConvert: list) -> list:
        new = [None] * len(listToConvert)
        for index, item in enumerate(listToConvert):
            if isinstance(item, dict):
                new[index] = cls(item)
                continue
            if isinstance(item, list):
                new[index] = cls.configifyList(item)
                continue
            new[index] = item
        return new

    @classmethod
    def dictifyList(cls, listToConvert: list) -> list:
        new = [None] * len(listToConvert)
        for index, item in enumerate(listToConvert):
            if isinstance(item, cls):
                new[index] = item.toDict()
                continue
            if isinstance(item, list):
                new[index] = cls.dictifyList(item)
                continue
            new[index] = item
        return new

    def get(self, item, default=None):
        if not isinstance(item, str) or not "." in item:
            return super().get(item, default)
        item: str
        keys = item.split(".")
        found = super().get(keys[0], default)
        for key in keys[1:]:
            found = found.get(key, default)
        return found

    def toDict(self) -> dict:
        new = {}
        for key, value in self.items():
            if isinstance(value, self.__class__):
                new[key] = value.toDict()
                continue
            if isinstance(value, list):
                new[key] = self.dictifyList(value)
                continue
            new[key] = value
        return new


DEFAULT_CONFIG: Config = Config(
    {
        "apprise": {
            "enabled": True,
            "notify": {
                "incomplete-activity": True,
                "uncaught-exception": True,
                "login-code": True,
            },
            "summary": "ON_ERROR",
            "urls": [],
        },
        "browser": {
            "geolocation": None,
            "language": None,
            "visible": False,
            "proxy": None,
        },
        "rtfr": False,
        "activities": {
            "ignore": [
                "Bing app search",
                "Chrome extension search",
                "Get 50 entries plus 1000 points!",
                "Get 100 points with search bar",
                "Safeguard your family's info",
            ],
            "search": {
                "Black Friday shopping": "black friday deals",
                "Discover open job roles": "jobs at microsoft",
                "Expand your vocabulary": "define demure",
                "Feeling symptoms?": "covid symptoms",
                "Find deals on Bing": "65 inch tv deals",
                "Find places to stay": "hotels rome italy",
                "Find somewhere new to explore": "directions to new york",
                "Gaming time": "vampire survivors video game",
                "Get your shopping done faster": "new iphone",
                "Houses near you": "apartments manhattan",
                "How's the economy?": "sp 500",
                "Learn to cook a new recipe": "how cook pierogi",
                "Learn a new recipe": "how cook pierogi",
                "Learn song lyrics": "hook blues traveler lyrics",
                "Lights, camera, action!": "lord of the rings fellowship of the bing",
                "Let's watch that movie again!": "aliens movie",
                "Plan a quick getaway": "flights nyc to paris",
                "Prepare for the weather": "weather tomorrow",
                "Quickly convert your money": "convert 374 usd to yen",
                "Search the lyrics of a song": "black sabbath supernaut lyrics",
                "Stay on top of the elections": "election news latest",
                "Too tired to cook tonight?": "Pizza Hut near me",
                "Too tired to cook?": "Pizza Hut near me",
                "Translate anything": "translate pencil sharpener to spanish",
                "What time is it?": "china time",
                "What's for Thanksgiving dinner?": "pumpkin pie recipe",
                "Who won?": "braves score",
                "You can track your package": "usps tracking",
                "Quickly convert money": "usd to euro",
            },
        },
        "logging": {
            "format": "%(asctime)s [%(levelname)s] %(message)s",
            "level": "INFO",
        },
        "retries": {"backoff-factor": 120, "max": 4, "strategy": "EXPONENTIAL"},
        "cooldown": {"min": 300, "max": 600},
        "search": {"type": "both"},
        "accounts": [],
    }
)


class Utils:
    """
    A class that provides utility functions for Selenium WebDriver interactions.
    """

    def __init__(self, webdriver: WebDriver):
        self.webdriver = webdriver
        with contextlib.suppress(Exception):
            locale = pylocale.getlocale()[0]
            pylocale.setlocale(pylocale.LC_NUMERIC, locale)

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

    # Prefer getBingInfo if possible
    def getDashboardData(self) -> dict:
        self.goToRewards()
        time.sleep(5)  # fixme Avoid busy wait (if this works)
        return self.webdriver.execute_script("return dashboard")

    def getDailySetPromotions(self) -> list[dict]:
        return self.getDashboardData()["dailySetPromotions"][
            date.today().strftime("%m/%d/%Y")
        ]

    def getMorePromotions(self) -> list[dict]:
        return self.getDashboardData()["morePromotions"]

    def getActivities(self) -> list[dict]:
        return self.getDailySetPromotions() + self.getMorePromotions()

    def getBingInfo(self) -> Any:
        session = makeRequestsSession()
        retries = CONFIG.retries.max
        backoff_factor = CONFIG.get("retries.backoff-factor")

        for cookie in self.webdriver.get_cookies():
            session.cookies.set(cookie["name"], cookie["value"])

        for attempt in range(retries):
            try:
                response = session.get("https://www.bing.com/rewards/panelflyout/getuserinfo")
                assert response.status_code == requests.codes.ok  # pylint: disable=no-member
                return response.json()
            except (JSONDecodeError, AssertionError) as e:
                logging.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    sleep_time = backoff_factor * (2 ** attempt)
                    logging.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    # noinspection PyUnboundLocalVariable
                    logging.debug(response)
                    raise

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
        if PREFER_BING_INFO:
            return self.getBingInfo()["userInfo"]["balance"]
        return self.getDashboardData()["userStatus"]["availablePoints"]

    def getGoalPoints(self) -> int:
        if PREFER_BING_INFO:
            return self.getBingInfo()["flyoutResult"]["userGoal"]["price"]
        return self.getDashboardData()["userStatus"]["redeemGoal"]["price"]

    def getGoalTitle(self) -> str:
        if PREFER_BING_INFO:
            return self.getBingInfo()["flyoutResult"]["userGoal"]["title"]
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
            (By.CLASS_NAME, "dashboardPopUpPopUpSelectButton"),
            (By.CSS_SELECTOR, "#cookie-banner button:first-child"),
            (By.CSS_SELECTOR, "#wcpConsentBannerCtrl button:first-child"),
        ]
        dismissButtons = []
        for by, value in byValues:
            with contextlib.suppress(NoSuchElementException):
                dismissButtons.extend(self.webdriver.find_elements(by=by, value=value))
        for dismissButton in dismissButtons:
            logging.debug(f"[DISMISS] Dismissing an element by clicking on {dismissButton}")
            dismissButton.click()

    def switchToNewTab(self, timeToWait: float = 10, closeTab: bool = False) -> None:
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
            ).click()
        except (
            TimeoutException,
            ElementClickInterceptedException,
            ElementNotInteractableException,
        ):
            self.tryDismissAllMessages()
            with contextlib.suppress(TimeoutException):
                WebDriverWait(self.webdriver, 10).until(
                    expected_conditions.element_to_be_clickable(element)
                )
            element.click()


def argumentParser() -> Namespace:
    parser = ArgumentParser(
        description="A simple bot that uses Selenium to farm M$ Rewards in Python",
        epilog="At least one account should be specified,"
        " either using command line arguments or a configuration file."
        "\nAll specified arguments will override the configuration file values.",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default=None,
        help="Specify the configuration file path",
    )
    parser.add_argument(
        "-C",
        "--create-config",
        action="store_true",
        help="Create a fillable configuration file with basic settings"
        " and given ones if none exists",
    )
    parser.add_argument(
        "-v",
        "--visible",
        action="store_true",
        help="Visible browser (Disable headless mode)",
    )
    parser.add_argument(
        "-l",
        "--lang",
        type=str,
        default=None,
        help="Language (ex: en)"
        "\nsee https://serpapi.com/google-languages for options",
    )
    parser.add_argument(
        "-g",
        "--geo",
        type=str,
        default=None,
        help="Searching geolocation (ex: US)"
        "\nsee https://serpapi.com/google-trends-locations for options (should be uppercase)",
    )
    parser.add_argument(
        "-em",
        "--email",
        type=str,
        default=None,
        help="Email address of the account to run. Only used if a password is given.",
    )
    parser.add_argument(
        "-pw",
        "--password",
        type=str,
        default=None,
        help="Password of the account to run. Only used if an email is given.",
    )
    parser.add_argument(
        "-p",
        "--proxy",
        type=str,
        default=None,
        help="Global Proxy, supports http/https/socks4/socks5"
        " (overrides config per-account proxies)"
        "\n`(ex: http://user:pass@host:port)`",
    )
    parser.add_argument(
        "-t",
        "--searchtype",
        choices=["desktop", "mobile", "both"],
        default=None,
        help="Set to search in either desktop, mobile or both (default: both)",
    )
    parser.add_argument(
        "-da",
        "--disable-apprise",
        action="store_true",
        help="Disable Apprise notifications, useful when developing",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Set the logging level to DEBUG",
    )
    parser.add_argument(
        "-r",
        "--reset",
        action="store_true",
        help="Delete the session folder and temporary files and kill"
        " all chrome processes. Can help resolve issues.",
    )
    return parser.parse_args()


def getProjectRoot() -> Path:
    return Path(__file__).parent.parent


def commandLineArgumentsAsConfig(args: Namespace) -> Config:
    config = Config()
    if args.visible:
        config.browser = Config()
        config.browser.visible = True
    if args.lang:
        if "browser" not in config:
            config.browser = Config()
        config.browser.language = args.lang
    if args.geo:
        if "browser" not in config:
            config.browser = Config()
        config.browser.geolocation = args.geo
    if args.proxy:
        if "browser" not in config:
            config.browser = Config()
        config.browser.proxy = args.proxy
    if args.disable_apprise:
        config.apprise = Config()
        config.apprise.enabled = False
    if args.debug:
        config.logging = Config()
        config.logging.level = "DEBUG"
    if args.searchtype:
        config.search = Config()
        config.search.type = args.searchtype
    if args.email and args.password:
        config.accounts = [
            Config(
                email=args.email,
                password=args.password,
            )
        ]

    return config


def setupAccounts(config: Config) -> Config:
    def validEmail(email: str) -> bool:
        """Validate Email."""
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return bool(re.match(pattern, email))

    loadedAccounts = []
    for account in config.accounts:
        if (
            "email" not in account
            or not isinstance(account.email, str)
            or not validEmail(account.email)
        ):
            logging.warning(
                f"[CREDENTIALS] Invalid email '{account.get('email', 'No email provided')}',"
                f" skipping this account"
            )
            continue
        if "password" not in account or not isinstance(account["password"], str):
            logging.warning("[CREDENTIALS] Invalid password, skipping this account")
            continue
        logging.info(f"[CREDENTIALS] Account loaded {account.email}")
        loadedAccounts.append(account)

    if not loadedAccounts:
        noAccountsNotice = """
        [ACCOUNT] No valid account provided.
        [ACCOUNT] Please provide a valid account, either using command line arguments or a configuration file.
        [ACCOUNT] For command line, please use the following arguments (change the email and password):
        [ACCOUNT]   `--email youremail@domain.com --password yourpassword` 
        [ACCOUNT] For configuration file, please generate a configuration file using the `-C` argument,
        [ACCOUNT]   then edit the generated file by replacing the email and password using yours. 
        """
        logging.error(noAccountsNotice)
        sys.exit(1)

    random.shuffle(loadedAccounts)
    config.accounts = loadedAccounts
    return config


def createEmptyConfig(configPath: Path, config: Config) -> None:
    if configPath.is_file():
        logging.error(f"[CONFIG] A file already exists at '{configPath}'")
        sys.exit(1)

    emptyConfig = Config(
        {
            "apprise": {"urls": ["discord://{WebhookID}/{WebhookToken}"]},
            "accounts": [
                {
                    "email": "Your Email 1",
                    "password": "Your Password 1",
                    "totp": "0123 4567 89ab cdef",
                    "proxy": "http://user:pass@host1:port",
                },
                {
                    "email": "Your Email 2",
                    "password": "Your Password 2",
                    "totp": "0123 4567 89ab cdef",
                    "proxy": "http://user:pass@host2:port",
                },
            ],
        }
    )
    with open(configPath, "w", encoding="utf-8") as configFile:
        yaml.dump((emptyConfig | config).toDict(), configFile)
    print(f"A configuration file was created at '{configPath}'")
    sys.exit()


def resetBot():
    """
    Delete the session folder and temporary files and kill all chrome processes.
    """

    sessionPath = getProjectRoot() / "sessions"
    if sessionPath.exists():
        print(f"Deleting sessions folder '{sessionPath}'")
        shutil.rmtree(sessionPath)

    filesToDeletePaths = (
        getProjectRoot() / "google_trends.bak",
        getProjectRoot() / "google_trends.dat",
        getProjectRoot() / "google_trends.dir",
        getProjectRoot() / "logs" / "previous_points_data.json",
    )
    for path in filesToDeletePaths:
        print(f"Deleting file '{path}'")
        path.unlink(missing_ok=True)

    for proc in psutil.process_iter(["pid", "name"]):
        if proc.info["name"] == "chrome.exe":
            proc.kill()

    print("All chrome processes killed")
    sys.exit()


def loadConfig(configFilename="config.yaml") -> Config:
    args = argumentParser()
    if args.config:
        configFile = Path(args.config)
    else:
        configFile = getProjectRoot() / configFilename

    args_config = commandLineArgumentsAsConfig(args)

    if args.create_config:
        createEmptyConfig(configFile, args_config)

    if args.reset:
        resetBot()

    config = DEFAULT_CONFIG | Config.fromYaml(configFile) | args_config

    if config.rtfr:
        print("Please read the README.md file before using this script. Exiting.")
        sys.exit()

    return config


def initApprise() -> Apprise:
    apprise = Apprise()

    urls = []
    if CONFIG.apprise.enabled:
        urls: list[str] = CONFIG.apprise.urls
        if not urls:
            logging.info("No apprise urls found, not sending notification")

    apprise.add(urls)
    return apprise


def getAnswerCode(key: str, string: str) -> str:
    t = sum(ord(string[i]) for i in range(len(string)))
    t += int(key[-2:], 16)
    return str(t)


def formatNumber(number, num_decimals=2) -> str:
    return pylocale.format_string(f"%10.{num_decimals}f", number, grouping=True).strip()


def getBrowserConfig(sessionPath: Path) -> dict | None:
    configFile = sessionPath / "config.json"
    if not configFile.exists():
        return None
    with open(configFile, encoding="utf-8") as f:
        return json.load(f)


def saveBrowserConfig(sessionPath: Path, config: dict) -> None:
    configFile = sessionPath / "config.json"
    with open(configFile, "w", encoding="utf-8") as f:
        json.dump(config, f)


def makeRequestsSession(session: Session = requests.session()) -> Session:
    retry = Retry(
        total=CONFIG.retries.max,
        backoff_factor=CONFIG.get("retries.backoff-factor"),
        status_forcelist=[
            500,
            502,
            503,
            504,
        ],
    )
    session.mount(
        "https://", HTTPAdapter(max_retries=retry)
    )  # See https://stackoverflow.com/a/35504626/4164390 to finetune
    session.mount(
        "http://", HTTPAdapter(max_retries=retry)
    )  # See https://stackoverflow.com/a/35504626/4164390 to finetune
    return session


def cooldown() -> None:
    cooldownTime = random.randint(CONFIG.cooldown.min, CONFIG.cooldown.max)
    logging.info(f"[COOLDOWN] Waiting for {cooldownTime} seconds")
    time.sleep(cooldownTime)


CONFIG = loadConfig()
APPRISE = initApprise()
