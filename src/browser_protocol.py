"""
Browser protocol defining the interface that all browser implementations should follow.
"""
from typing import Protocol, Union

from src.utils import Utils
from src import RemainingSearches


class BrowserProtocol(Protocol):
    """Protocol defining the interface for browser implementations."""
    
    webdriver: object  # WebDriver-compatible object
    utils: Utils
    mobile: bool
    browserType: str
    email: str
    password: str
    
    def getRemainingSearches(self, desktopAndMobile: bool = False) -> Union[RemainingSearches, int]:
        """Get remaining searches for the account."""
        ...