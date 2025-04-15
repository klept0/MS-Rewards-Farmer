from unittest import TestCase

# noinspection PyPackageRequirements
from parameterized import parameterized

from src.utils import CONFIG, APPRISE, isValidCountryCode, isValidLanguageCode


class TestUtils(TestCase):
    def test_send_notification(self):
        CONFIG.apprise.enabled = True
        APPRISE.notify("body", "title")

    @parameterized.expand(
        [
            ("US", True),
            ("US-GA", True),
            ("XX", False),
            ("US-XX", False),
        ]
    )
    def test_isValidCountryCode(self, code, expected):
        self.assertEqual(isValidCountryCode(code), expected)

    @parameterized.expand(
        [
            ("en", True),
            ("en-US", True),
            ("xx", False),
            ("en-XX", False),
        ]
    )
    def test_isValidLanguageCode(self, code, expected):
        self.assertEqual(isValidLanguageCode(code), expected)

    def test_load_localized_activities_with_valid_language(self):
        from src.utils import load_localized_activities

        localized_activities = load_localized_activities("en")
        self.assertTrue(
            localized_activities.title_to_query,
            "localized_activities.title_to_query should not be empty",
        )
        self.assertTrue(
            localized_activities.ignore,
            "localized_activities.ignore should not be empty",
        )

    def test_load_localized_activities_with_invalid_language(self):
        from src.utils import load_localized_activities

        with self.assertRaises(FileNotFoundError):
            load_localized_activities("foo")
