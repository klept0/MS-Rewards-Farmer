#!/usr/bin/env python3
"""
Test script to verify Camoufox integration with MS-Rewards-Farmer
"""

import logging
import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.browser_factory import create_browser
from src.utils import CONFIG

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

def test_camoufox_browser():
    """Test basic Camoufox browser functionality"""
    
    # Create a mock account object for testing
    class MockAccount:
        def __init__(self):
            self.email = "test@example.com"
            self.password = "test_password"
            
        def get(self, key, default=None):
            return default
    
    account = MockAccount()
    
    try:
        logging.info("Testing Camoufox browser creation...")
        
        # Force browser type to camoufox for this test
        CONFIG.browser.type = "camoufox"
        
        with create_browser(mobile=False, account=account) as browser:
            logging.info(f"Browser created successfully: {type(browser).__name__}")
            
            # Test basic navigation
            if hasattr(browser, 'webdriver') and browser.webdriver:
                browser.webdriver.get("https://www.example.com")
                logging.info(f"Navigated to: {browser.webdriver.current_url}")
                
                # Test page source
                page_source = browser.webdriver.page_source
                if "Example Domain" in page_source:
                    logging.info("✅ Successfully loaded example.com")
                else:
                    logging.warning("⚠️  Page content doesn't match expected")
            else:
                logging.error("❌ Browser webdriver not available")
                
        logging.info("✅ Camoufox test completed successfully!")
        return True
        
    except Exception as e:
        logging.error(f"❌ Camoufox test failed: {e}")
        logging.exception("Full error details:")
        return False

def test_chrome_browser():
    """Test Chrome browser functionality for comparison"""
    
    class MockAccount:
        def __init__(self):
            self.email = "test@example.com"
            self.password = "test_password"
            
        def get(self, key, default=None):
            return default
    
    account = MockAccount()
    
    try:
        logging.info("Testing Chrome browser creation...")
        
        # Force browser type to chrome for this test
        CONFIG.browser.type = "chrome"
        
        with create_browser(mobile=False, account=account) as browser:
            logging.info(f"Browser created successfully: {type(browser).__name__}")
            
            # Test basic navigation
            if hasattr(browser, 'webdriver') and browser.webdriver:
                browser.webdriver.get("https://www.example.com")
                logging.info(f"Navigated to: {browser.webdriver.current_url}")
                
                # Test page source
                page_source = browser.webdriver.page_source
                if "Example Domain" in page_source:
                    logging.info("✅ Successfully loaded example.com")
                else:
                    logging.warning("⚠️  Page content doesn't match expected")
            else:
                logging.error("❌ Browser webdriver not available")
                
        logging.info("✅ Chrome test completed successfully!")
        return True
        
    except Exception as e:
        logging.error(f"❌ Chrome test failed: {e}")
        logging.exception("Full error details:")
        return False

if __name__ == "__main__":
    logging.info("🚀 Starting browser integration tests...")
    
    # Test both browsers
    camoufox_success = test_camoufox_browser()
    chrome_success = test_chrome_browser()
    
    if camoufox_success and chrome_success:
        logging.info("🎉 All tests passed!")
        sys.exit(0)
    else:
        logging.error("❌ Some tests failed")
        sys.exit(1)