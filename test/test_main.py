import unittest
from unittest.mock import patch, MagicMock

import main
from src.utils import Config, CONFIG, APPRISE


class TestMain(unittest.TestCase):

    @patch.object(main, "executeBot")
    def test_exit_1_when_exception(
            self,
            mock_executeBot: MagicMock,
    ):
        CONFIG.accounts = [Config({"password": "foo", "email": "bar"})]
        mock_executeBot.side_effect = Exception("Test exception")

        with self.assertRaises(SystemExit):
            main.main()

    @patch.object(APPRISE, "notify")
    @patch.object(main, "executeBot")
    def test_send_notification_when_exception(
        self,
        mock_executeBot: MagicMock,
        mock_notify: MagicMock,
    ):
        CONFIG.accounts = [Config({"password": "foo", "email": "bar"})]
        mock_executeBot.side_effect = Exception("Test exception")

        try:
            main.main()
        except SystemExit:
            pass

        mock_notify.assert_called()


if __name__ == "__main__":
    unittest.main()
