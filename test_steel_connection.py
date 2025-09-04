#!/usr/bin/env python3
"""Test Steel connection independently to diagnose browser session issues."""

import os
import sys
import logging
import time
from getpass import getpass

# Add the langchain-steel directory to the path
sys.path.insert(0, 'langchain-steel')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_steel_connection():
    """Test basic Steel session creation and browser connection."""
    
    # Ensure API key is available
    if not os.getenv("STEEL_API_KEY"):
        steel_api_key = getpass("Enter your Steel API key: ")
        os.environ["STEEL_API_KEY"] = steel_api_key
    
    try:
        from steel import Steel
        print("✅ Steel import successful")
        
        # Create Steel client
        client = Steel()
        print("✅ Steel client created")
        
        # Test basic session creation
        print("\n🔧 Testing basic Steel session creation...")
        session = client.sessions.create(
            dimensions={"width": 1024, "height": 768},
            block_ads=True,
            api_timeout=60000,  # 1 minute for testing
            use_proxy=False
        )
        print(f"✅ Steel session created: {session.id}")
        print(f"📍 Session viewer URL: {session.session_viewer_url}")
        print(f"🔗 WebSocket URL: {session.websocket_url}")
        
        # Keep session alive for a bit
        print("\n⏰ Keeping session alive for 10 seconds...")
        time.sleep(10)
        
        # Try to release the session
        print("\n🧹 Releasing session...")
        client.sessions.release(session.id)
        print("✅ Session released successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Steel connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_playwright_connection():
    """Test Playwright connection to Steel session."""
    
    if not os.getenv("STEEL_API_KEY"):
        steel_api_key = getpass("Enter your Steel API key: ")
        os.environ["STEEL_API_KEY"] = steel_api_key
    
    try:
        from steel import Steel
        from playwright.sync_api import sync_playwright
        
        print("\n🔧 Testing Playwright connection to Steel...")
        
        # Create Steel session
        client = Steel()
        session = client.sessions.create(
            dimensions={"width": 1024, "height": 768},
            block_ads=True,
            api_timeout=120000,  # 2 minutes
            use_proxy=False
        )
        print(f"✅ Steel session created: {session.id}")
        
        # Connect with Playwright
        playwright = sync_playwright().start()
        steel_api_key = os.getenv("STEEL_API_KEY")
        
        print("🔗 Connecting to browser via CDP...")
        browser = playwright.chromium.connect_over_cdp(
            f"{session.websocket_url}&apiKey={steel_api_key}",
            timeout=30000
        )
        print("✅ Browser connected")
        
        # Get page
        context = browser.contexts[0]
        if len(context.pages) == 0:
            page = context.new_page()
        else:
            page = context.pages[0]
        print("✅ Page obtained")
        
        # Test basic page operations
        print("📸 Taking screenshot...")
        screenshot_data = page.screenshot()
        print(f"✅ Screenshot captured: {len(screenshot_data)} bytes")
        
        # Navigate somewhere
        print("🌐 Testing navigation...")
        page.goto("https://example.com", wait_until="domcontentloaded")
        print(f"✅ Navigation successful: {page.url}")
        
        # Take another screenshot
        print("📸 Taking second screenshot...")
        screenshot_data2 = page.screenshot()
        print(f"✅ Second screenshot: {len(screenshot_data2)} bytes")
        
        # Cleanup
        browser.close()
        playwright.stop()
        client.sessions.release(session.id)
        print("✅ All cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Playwright connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Steel Connection Diagnostics")
    print("=" * 50)
    
    # Test 1: Basic Steel connection
    success1 = test_steel_connection()
    
    # Test 2: Playwright connection (only if basic test passed)
    if success1:
        print("\n" + "=" * 50)
        success2 = test_playwright_connection()
        
        if success1 and success2:
            print("\n✅ All Steel connection tests passed!")
            print("   The issue may be in the Claude Computer Use integration.")
        else:
            print("\n❌ Steel connection issues detected.")
    else:
        print("\n❌ Basic Steel connection failed - check API key and network.")
    
    print("\n💡 If tests pass, try your notebook again.")
    print("   If they fail, there may be Steel API issues.")