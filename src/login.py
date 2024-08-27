import argparse
import contextlib
import logging
from argparse import Namespace

from pyotp import TOTP
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from undetected_chromedriver import Chrome

from src.browser import Browser


class Login:
    browser: Browser
    args: Namespace
    webdriver: Chrome

    def __init__(self, browser: Browser, args: argparse.Namespace):
        self.browser = browser
        self.webdriver = browser.webdriver
        self.utils = browser.utils
        self.args = args

    def login(self) -> None:
        if self.utils.isLoggedIn():
            logging.info("[LOGIN] Already logged-in")
        else:
            logging.info("[LOGIN] Logging-in...")
            self.executeLogin()
            logging.info("[LOGIN] Logged-in successfully !")

        assert self.utils.isLoggedIn()

    def executeLogin(self) -> None:
        # Email field
        emailField = self.utils.waitUntilVisible(By.ID, "i0116")
        logging.info("[LOGIN] Entering email...")
        emailField.click()
        emailField.send_keys(self.browser.username)
        assert emailField.get_attribute("value") == self.browser.username
        self.utils.waitUntilClickable(By.ID, "idSIButton9").click()

        # Passwordless check
        isPasswordless = False
        with contextlib.suppress(TimeoutException):
            self.utils.waitUntilVisible(By.ID, "displaySign")
            isPasswordless = True
        logging.debug("isPasswordless = %s", isPasswordless)

        if isPasswordless:
            # Passworless login, have user confirm code on phone
            codeField = self.utils.waitUntilVisible(By.ID, "displaySign")
            logging.warning(
                "[LOGIN] Confirm your login with code %s on your phone (you have"
                " one minute)!\a",
                codeField.text,
            )
            self.utils.waitUntilVisible(By.NAME, "kmsiForm", 60)
            logging.info("[LOGIN] Successfully verified!")

        else:
            # Password-based login, enter password from accounts.json
            passwordField = self.utils.waitUntilClickable(By.NAME, "passwd")
            logging.info("[LOGIN] Entering password...")
            passwordField.click()
            passwordField.send_keys(self.browser.password)
            assert passwordField.get_attribute("value") == self.browser.password
            self.utils.waitUntilClickable(By.ID, "idSIButton9").click()

            # Check if 2FA is enabled, both device auth and TOTP are supported
            isDeviceAuthEnabled = False
            with contextlib.suppress(TimeoutException):
                self.utils.waitUntilVisible(By.ID, "idSpan_SAOTCAS_DescSessionID")
                isDeviceAuthEnabled = True
            logging.debug("isDeviceAuthEnabled = %s", isDeviceAuthEnabled)

            isTOTPEnabled = False
            with contextlib.suppress(TimeoutException):
                self.utils.waitUntilVisible(By.ID, "idTxtBx_SAOTCC_OTC", 1)
                isTOTPEnabled = True
            logging.debug("isTOTPEnabled = %s", isTOTPEnabled)

            if isDeviceAuthEnabled:
                # For some reason, undetected chromedriver doesn't receive the confirmation
                # after the user has confirmed the login on their phone.
                raise Exception(
                    "Unfortunatly, device auth is not supported yet. Turn on"
                    " passwordless login in your account settings, use TOTPs or remove"
                    " 2FA altogether."
                )

                # Device auth, have user confirm code on phone
                codeField = self.utils.waitUntilVisible(
                    By.ID, "idSpan_SAOTCAS_DescSessionID"
                )
                logging.warning(
                    "[LOGIN] Confirm your login with code %s on your phone (you have"
                    " one minute)!\a",
                    codeField.text,
                )
                self.utils.waitUntilVisible(By.NAME, "kmsiForm", 60)
                logging.info("[LOGIN] Successfully verified!")

            elif isTOTPEnabled:
                # One-time password required
                if self.browser.totp is not None:
                    # TOTP token provided
                    logging.info("[LOGIN] Entering OTP...")
                    otp = TOTP(self.browser.totp.replace(" ", "")).now()
                    otpField = self.utils.waitUntilClickable(By.ID, "idTxtBx_SAOTCC_OTC")
                    otpField.send_keys(otp)
                    assert otpField.get_attribute("value") == otp
                    self.utils.waitUntilClickable(By.ID, "idSubmit_SAOTCC_Continue").click()

                else:
                    # TOTP token not provided, manual intervention required
                    assert self.args.visible, (
                        "[LOGIN] 2FA detected, provide token in accounts.json or run in"
                        " visible mode to handle login."
                    )
                    print(
                        "[LOGIN] 2FA detected, handle prompts and press enter when on"
                        " keep me signed in page."
                    )
                    input()

        self.utils.waitUntilVisible(By.NAME, "kmsiForm")
        self.utils.waitUntilClickable(By.ID, "acceptButton").click()

        # TODO: This should probably instead be checked with an element's id,
        # as the hardcoded text might be different in other languages
        isAskingToProtect = self.utils.checkIfTextPresentAfterDelay(
            "protect your account", 5
        )
        logging.debug("isAskingToProtect = %s", isAskingToProtect)

        if isAskingToProtect:
            assert (
                self.args.visible
            ), "Account protection detected, run in visible mode to handle login"
            print(
                "Account protection detected, handle prompts and press enter when on rewards page"
            )
            input()

        self.utils.waitUntilVisible(
            By.CSS_SELECTOR, 'html[data-role-name="RewardsPortal"]'
        )
