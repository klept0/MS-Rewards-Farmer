from unittest import TestCase

from src.utils import CONFIG, sendNotification


class TestUtils(TestCase):
    def test_send_notification(self):
        CONFIG.apprise.enabled = True
        sendNotification("title", "body")
