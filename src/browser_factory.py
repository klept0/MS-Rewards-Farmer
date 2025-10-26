"""
Browser factory module for creating browser instances based on configuration.
"""
import logging
from typing import Union, TYPE_CHECKING

if TYPE_CHECKING:
    from src.browser import Browser
    from src.camoufox_browser import CamoufoxBrowser

from src.utils import CONFIG


def create_browser(mobile: bool, account) -> Union["Browser", "CamoufoxBrowser"]:
    """
    Factory function to create a browser instance based on configuration.
    
    Args:
        mobile: Whether to create a mobile browser instance
        account: Account configuration object
        
    Returns:
        Browser instance (either Chrome-based Browser or CamoufoxBrowser)
    """
    browser_type = CONFIG.browser.type.lower()
    
    logging.info(f"Creating {browser_type} browser instance (mobile: {mobile})")
    
    if browser_type == "camoufox":
        from src.camoufox_browser import CamoufoxBrowser
        return CamoufoxBrowser(mobile=mobile, account=account)
    elif browser_type == "chrome":
        from src.browser import Browser
        return Browser(mobile=mobile, account=account)
    else:
        logging.warning(f"Unknown browser type: {browser_type}, defaulting to Chrome")
        from src.browser import Browser
        return Browser(mobile=mobile, account=account)