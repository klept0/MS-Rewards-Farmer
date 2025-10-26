#!/usr/bin/env python3
"""
Simple test script to verify Camoufox integration works
"""

import logging
import sys
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

def test_camoufox_simple():
    """Simple Camoufox test"""
    
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
        CONFIG.browser.visible = True  # Make it visible for testing
        
        with create_browser(mobile=False, account=account) as browser:
            logging.info(f"✅ Browser created successfully: {type(browser).__name__}")
            
            # Test basic navigation
            if hasattr(browser, 'webdriver') and browser.webdriver:
                logging.info("✅ WebDriver wrapper is available")
                browser.webdriver.get("https://www.example.com")
                logging.info(f"✅ Navigated to: {browser.webdriver.current_url}")
                
                # Test page source
                page_source = browser.webdriver.page_source
                if "Example Domain" in page_source:
                    logging.info("✅ Successfully loaded example.com content")
                else:
                    logging.warning("⚠️  Page content doesn't match expected")
                    
                # Test some utils functionality
                if hasattr(browser, 'utils') and browser.utils:
                    logging.info("✅ Utils are available")
                else:
                    logging.warning("⚠️  Utils not available")
                    
            else:
                logging.error("❌ Browser webdriver not available")
                return False
                
        logging.info("🎉 Camoufox integration test completed successfully!")
        return True
        
    except Exception as e:
        logging.error(f"❌ Camoufox test failed: {e}")
        logging.exception("Full error details:")
        return False

if __name__ == "__main__":
    logging.info("🚀 Starting Camoufox integration test...")
    
    success = test_camoufox_simple()
    
    if success:
        logging.info("🎉 Test passed! Camoufox integration is working!")
        print("\n" + "="*50)
        print("✅ CAMOUFOX INTEGRATION SUCCESS!")
        print("="*50)
        print("You can now use Camoufox in your MS-Rewards-Farmer by:")
        print("1. Setting browser.type to 'camoufox' in your config")
        print("2. Or using --browser camoufox command line argument")
        print("="*50)
        sys.exit(0)
    else:
        logging.error("❌ Test failed")
        sys.exit(1)