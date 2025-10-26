import logging
import random
from pathlib import Path
from types import TracebackType
from typing import Type

from camoufox.sync_api import Camoufox
from playwright._impl._page import Page
from playwright.sync_api import Browser as PlaywrightBrowser

from src import RemainingSearches
from src.utils import (
    CONFIG,
    Utils,
    getBrowserConfig,
    getProjectRoot,
    saveBrowserConfig,
    PREFER_BING_INFO, LANGUAGE, COUNTRY,
)


class CamoufoxBrowser:
    """Camoufox wrapper class that mirrors the Browser interface."""

    browser: PlaywrightBrowser
    page: Page

    def __init__(self, mobile: bool, account) -> None:
        # Initialize Camoufox browser instance
        logging.debug("in CamoufoxBrowser.__init__")
        self.mobile = mobile
        self.browserType = "mobile" if mobile else "desktop"
        self.headless = not CONFIG.browser.visible
        self.email = account.email
        self.password = account.password
        self.totp = account.get("totp")
        self.localeLang, self.localeGeo = LANGUAGE, COUNTRY
        self.proxy = CONFIG.browser.proxy
        if not self.proxy and account.get("proxy"):
            self.proxy = account.proxy
        self.userDataDir = self.setupProfiles()
        self.browserConfig = getBrowserConfig(self.userDataDir)
        
        # Prepare Camoufox options - we'll initialize in __enter__
        self.camoufox_options = self.getCamoufoxOptions()
        self.camoufox = None
        self.page = None
        
        # These will be set in __enter__
        self.webdriver = None
        self.utils = None
        logging.debug("out CamoufoxBrowser.__init__")

    def __enter__(self):
        logging.debug("in CamoufoxBrowser.__enter__")
        # Initialize Camoufox context manager
        self.camoufox_context = Camoufox(**self.camoufox_options)
        self.camoufox = self.camoufox_context.__enter__()
        # The page should be created automatically in Camoufox
        self.page = self.camoufox.new_page()
        
        # Create WebDriver wrapper and utils
        self.webdriver = CamoufoxWebDriverWrapper(self.page)
        self.utils = Utils(self.webdriver)
        
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ):
        # Cleanup actions when exiting the browser context
        logging.debug(
            f"in CamoufoxBrowser.__exit__ exc_type={exc_type} exc_value={exc_value} traceback={traceback}"
        )
        if self.page:
            self.page.close()
        if hasattr(self, 'camoufox_context'):
            self.camoufox_context.__exit__(exc_type, exc_value, traceback)

    def getCamoufoxOptions(self) -> dict:
        # Configure Camoufox browser options
        camoufox_options = {
            "headless": self.headless,
            "os": self.getOSForFingerprint(),
            "geoip": True if self.proxy else False,
            "locale": self.localeLang,
            "humanize": True,  # Enable human-like cursor movement
            "block_images": True,  # Save bandwidth, similar to Chrome blink-settings
            "i_know_what_im_doing": True,  # Acknowledge the image blocking warning
        }
        
        if self.proxy:
            # Parse proxy format: http://user:pass@host:port
            proxy_parts = self.proxy.replace("http://", "").replace("https://", "")
            if "@" in proxy_parts:
                auth_parts, host_port = proxy_parts.split("@")
                username, password = auth_parts.split(":")
                host, port = host_port.split(":")
                camoufox_options["proxy"] = {
                    "server": f"http://{host}:{port}",
                    "username": username,
                    "password": password,
                }
            else:
                host, port = proxy_parts.split(":")
                camoufox_options["proxy"] = {
                    "server": f"http://{host}:{port}",
                }

        # Configure screen/window size
        if self.browserConfig and self.browserConfig.get("sizes"):
            deviceHeight = self.browserConfig["sizes"]["height"]
            deviceWidth = self.browserConfig["sizes"]["width"]
        else:
            if self.mobile:
                deviceHeight = random.randint(568, 1024)
                deviceWidth = random.randint(320, min(576, int(deviceHeight * 0.7)))
            else:
                deviceWidth = random.randint(1024, 2560)
                deviceHeight = random.randint(768, min(1440, int(deviceWidth * 0.8)))
            
            if not self.browserConfig:
                self.browserConfig = {}
            self.browserConfig["sizes"] = {
                "height": deviceHeight,
                "width": deviceWidth,
            }
            saveBrowserConfig(self.userDataDir, self.browserConfig)

        # Set window size for Camoufox
        camoufox_options["window"] = (deviceWidth, deviceHeight)
        
        logging.info(f"Device size: {deviceWidth}x{deviceHeight}")
        
        # Set user data directory
        camoufox_options["user_data_dir"] = str(self.userDataDir)
        camoufox_options["persistent_context"] = True

        return camoufox_options

    def getOSForFingerprint(self) -> str:
        """Determine OS for fingerprint generation based on current platform"""
        import platform
        current_os = platform.system().lower()
        if current_os == "darwin":
            return "macos"
        elif current_os == "windows":
            return "windows"
        else:
            return "linux"

    def setupProfiles(self) -> Path:
        """
        Sets up the sessions profile for the Camoufox browser.
        Uses the email to create a unique profile for the session.

        Returns:
            Path
        """
        sessionsDir = getProjectRoot() / "sessions"

        # Concatenate email and browser type for a plain text session ID
        sessionid = f"{self.email}"

        sessionsDir = sessionsDir / sessionid
        sessionsDir.mkdir(parents=True, exist_ok=True)
        return sessionsDir

    def getRemainingSearches(
        self, desktopAndMobile: bool = False
    ) -> RemainingSearches | int:
        if PREFER_BING_INFO:
            bingInfo = self.utils.getBingInfo()
        else:
            try:
                bingInfo = self.utils.getDashboardData()
            except Exception:
                logging.info("Dashboard Error: Forcing Searches Remaining to 1")
                return RemainingSearches(desktop=1, mobile=1)
        
        searchPoints = 1
        if PREFER_BING_INFO:
            counters = bingInfo["flyoutResult"]["userStatus"]["counters"]
        else:
            counters = bingInfo["userStatus"]["counters"]
        pcSearch: dict = counters["PCSearch" if PREFER_BING_INFO else "pcSearch"][0]
        pointProgressMax: int = pcSearch["pointProgressMax"]

        searchPoints: int
        if pointProgressMax in [30, 90, 102]:
            searchPoints = 3
        elif pointProgressMax in [50, 150] or pointProgressMax >= 170:
            searchPoints = 5
        pcPointsRemaining = pcSearch["pointProgressMax"] - pcSearch["pointProgress"]
        assert pcPointsRemaining % searchPoints == 0
        remainingDesktopSearches: int = int(pcPointsRemaining / searchPoints)

        if PREFER_BING_INFO:
            activeLevel = bingInfo["userInfo"]["profile"]["attributes"]["level"]
        else:
            activeLevel = bingInfo["userStatus"]["levelInfo"]["activeLevel"]
        remainingMobileSearches: int = 0
        if activeLevel == "Level2":
            mobileSearch: dict = counters[
                "MobileSearch" if PREFER_BING_INFO else "mobileSearch"
            ][0]
            mobilePointsRemaining = (
                mobileSearch["pointProgressMax"] - mobileSearch["pointProgress"]
            )
            assert mobilePointsRemaining % searchPoints == 0
            remainingMobileSearches = int(mobilePointsRemaining / searchPoints)
        elif activeLevel == "Level1":
            pass
        else:
            raise AssertionError(f"Unknown activeLevel: {activeLevel}")

        if desktopAndMobile:
            return RemainingSearches(
                desktop=remainingDesktopSearches, mobile=remainingMobileSearches
            )
        if self.mobile:
            return remainingMobileSearches
        return remainingDesktopSearches


class CamoufoxWebDriverWrapper:
    """Wrapper to make Playwright Page compatible with existing Selenium WebDriver code"""
    
    def __init__(self, page: Page):
        self.page = page
        self._cookies = []
    
    @property
    def current_url(self) -> str:
        return self.page.url
    
    @property
    def page_source(self) -> str:
        return self.page.content()
    
    @property
    def window_handles(self) -> list[str]:
        # For simplicity, we'll just return the current page
        return ["main"]
    
    @property
    def current_window_handle(self) -> str:
        return "main"
    
    def get(self, url: str) -> None:
        self.page.goto(url)
    
    def execute_script(self, script: str):
        return self.page.evaluate(script)
    
    def get_cookies(self) -> list[dict]:
        cookies = self.page.context.cookies()
        return [
            {
                "name": cookie["name"],
                "value": cookie["value"],
                "domain": cookie.get("domain", ""),
                "path": cookie.get("path", "/"),
            }
            for cookie in cookies
        ]
    
    def find_element(self, by: str, value: str):
        # Convert Selenium locators to Playwright selectors
        if by == "id":
            selector = f"#{value}"
        elif by == "class name":
            selector = f".{value}"
        elif by == "tag name":
            selector = value
        elif by == "css selector":
            selector = value
        elif by == "xpath":
            # For XPath, we need to use Playwright's locator
            return PlaywrightElementWrapper(self.page.locator(f"xpath={value}"))
        else:
            selector = value
        
        return PlaywrightElementWrapper(self.page.locator(selector))
    
    def find_elements(self, by: str, value: str):
        # Similar to find_element but returns all matching elements
        if by == "id":
            selector = f"#{value}"
        elif by == "class name":
            selector = f".{value}"
        elif by == "tag name":
            selector = value
        elif by == "css selector":
            selector = value
        elif by == "xpath":
            selector = f"xpath={value}"
        else:
            selector = value
            
        elements = self.page.locator(selector)
        
        # Return a list of wrapped elements
        count = elements.count()
        return [PlaywrightElementWrapper(elements.nth(i)) for i in range(count)]
    
    def switch_to_window(self, window_name: str) -> None:
        # For multi-tab support, we'd need to implement this properly
        # For now, we'll just pass
        pass
    
    def close(self) -> None:
        # Close current page/tab
        self.page.close()
    
    def quit(self) -> None:
        # Close the browser
        self.page.context.browser.close()


class PlaywrightElementWrapper:
    """Wrapper to make Playwright Locator compatible with Selenium WebElement"""
    
    def __init__(self, locator):
        self.locator = locator
    
    def click(self) -> None:
        self.locator.click()
    
    def send_keys(self, keys: str) -> None:
        self.locator.fill(keys)
    
    def clear(self) -> None:
        self.locator.clear()
    
    @property
    def text(self) -> str:
        return self.locator.text_content() or ""
    
    def get_attribute(self, name: str) -> str:
        return self.locator.get_attribute(name) or ""
    
    def is_displayed(self) -> bool:
        return self.locator.is_visible()
    
    def is_enabled(self) -> bool:
        return self.locator.is_enabled()
    
    def find_element(self, by: str, value: str):
        # Find child element
        if by == "id":
            selector = f"#{value}"
        elif by == "class name":
            selector = f".{value}"
        elif by == "tag name":
            selector = value
        elif by == "css selector":
            selector = value
        elif by == "xpath":
            selector = f"xpath={value}"
        else:
            selector = value
        
        return PlaywrightElementWrapper(self.locator.locator(selector))
