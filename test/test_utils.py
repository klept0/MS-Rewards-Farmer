from unittest import TestCase

from src.utils import CONFIG, APPRISE


class TestUtils(TestCase):
    def test_send_notification(self):
        CONFIG.apprise.enabled = True
        APPRISE.notify("body", "title")
