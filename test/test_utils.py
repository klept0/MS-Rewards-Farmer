from argparse import Namespace
from unittest import TestCase

from src.utils import Utils


class TestUtils(TestCase):
    def test_send_notification(self):
        Utils.args = Namespace()
        Utils.args.disable_apprise = False
        Utils.sendNotification("title", "body")
