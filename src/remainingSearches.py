from typing import NamedTuple


class RemainingSearches(NamedTuple):
    desktop: int
    mobile: int

    def getTotal(self) -> int:
        return self.desktop + self.mobile
