import unittest

from parameterized import parameterized

from src.browser import isValidCountryCode, isValidLanguageCode


class MyTestCase(unittest.TestCase):

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


if __name__ == "__main__":
    unittest.main()
