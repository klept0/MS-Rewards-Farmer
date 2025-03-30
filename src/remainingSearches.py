from typing import NamedTuple


class RemainingSearches(NamedTuple):
    """
    Remaining searches for the current account.
    """

    desktop: int
    mobile: int

    def getTotal(self) -> int:
        return self.desktop + self.mobile
