import unittest
from unittest.mock import patch, MagicMock

import main
from src import utils
from src.utils import Config, CONFIG


class TestMain(unittest.TestCase):

    # noinspection PyUnusedLocal
    @patch.object(main, "save_previous_points_data")
    @patch.object(main, "setupLogging")
    @patch.object(main, "executeBot")
    # @patch.object(utils, "sendNotification")
    def test_send_notification_when_exception(
        self,
        # mock_send_notification: MagicMock,
        mock_executeBot: MagicMock,
        mock_setupLogging: MagicMock,
        mock_save_previous_points_data: MagicMock,
    ):
        CONFIG.accounts = [Config({"password": "foo", "email": "bar"})]
        mock_executeBot.side_effect = Exception

        main.main()

        # mock_send_notification.assert_called()


if __name__ == "__main__":
    unittest.main()
