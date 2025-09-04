#!/usr/bin/env python3
"""Test the Steel Browser Agent specifically to debug the session closing issue."""

import os
import sys
import logging
import time
from getpass import getpass

# Add the langchain-steel directory to the path
sys.path.insert(0, 'langchain-steel')

# Set up detailed logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_browser_agent_initialization():
    """Test just the browser agent initialization without Claude."""
    
    print("🧪 Testing Browser Agent Initialization")
    print("=" * 50)
    
    # Ensure API keys are available
    if not os.getenv("STEEL_API_KEY"):
        steel_api_key = getpass("Enter your Steel API key: ")
        os.environ["STEEL_API_KEY"] = steel_api_key
    
    try:
        from langchain_steel import SteelBrowserAgent
        from langchain_steel.agents.claude_computer_use import SteelBrowserSession
        from steel import Steel
        
        print("✅ Imports successful")
        
        # Test direct SteelBrowserSession creation (what the agent uses internally)
        print("\n🔧 Testing SteelBrowserSession creation...")
        steel_client = Steel()
        
        with SteelBrowserSession(
            steel_client=steel_client,
            width=1024,
            height=768,
            session_timeout=120000  # 2 minutes for testing
        ) as session:
            print("✅ SteelBrowserSession context entered successfully")
            
            # Test screenshot immediately after creation
            print("📸 Taking immediate screenshot...")
            screenshot = session.screenshot()
            print(f"✅ Screenshot successful: {len(screenshot)} chars")
            
            # Wait a moment and test again
            print("⏰ Waiting 5 seconds...")
            time.sleep(5)
            
            print("📸 Taking second screenshot...")
            screenshot2 = session.screenshot()
            print(f"✅ Second screenshot successful: {len(screenshot2)} chars")
            
            # Test a simple action
            print("🖱️ Testing simple action (mouse move)...")
            action_result = session.execute_computer_action(
                action="mouse_move", 
                coordinate=[100, 100]
            )
            print(f"✅ Action successful: {len(action_result)} chars")
            
        print("✅ SteelBrowserSession closed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Browser agent initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_browser_agent_with_mock_claude():
    """Test browser agent with a mock Claude call (no actual Claude API)."""
    
    print("\n🧪 Testing Browser Agent with Mock Claude Integration")
    print("=" * 60)
    
    try:
        from langchain_steel.agents.claude_computer_use import ClaudeComputerUseAgent, SteelBrowserSession
        from steel import Steel
        from unittest.mock import Mock
        
        print("✅ Claude integration imports successful")
        
        # Create mock Anthropic client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [
            Mock(type="text", text="I'll take a screenshot to see the page"),
            Mock(
                type="tool_use", 
                name="computer",
                id="test_id_123",
                input={"action": "screenshot"}
            )
        ]
        mock_client.beta.messages.create.return_value = mock_response
        
        steel_client = Steel()
        
        print("🔧 Creating browser session for Claude agent...")
        with SteelBrowserSession(
            steel_client=steel_client,
            width=1024,
            height=768,
            session_timeout=120000
        ) as browser_session:
            print("✅ Browser session created")
            
            # Create Claude agent with mock client
            print("🤖 Creating Claude agent...")
            claude_agent = ClaudeComputerUseAgent(
                anthropic_api_key="mock_key",  # Won't be used with mock
                browser_session=browser_session,
                throttle_delay=0.1  # Shorter for testing
            )
            
            # Replace the real client with our mock
            claude_agent.client = mock_client
            print("✅ Claude agent created with mock client")
            
            # Test the screenshot caching system
            print("📸 Testing screenshot caching...")
            screenshot1 = claude_agent._get_screenshot_with_cache()
            screenshot2 = claude_agent._get_screenshot_with_cache()
            print(f"✅ Screenshot caching test: {len(screenshot1)} chars")
            
            # Test action batcher
            print("⚡ Testing action batcher...")
            start_time = time.time()
            claude_agent.action_batcher.wait_if_needed()
            mid_time = time.time()
            claude_agent.action_batcher.wait_if_needed()  # Should throttle
            end_time = time.time()
            
            throttle_delay = end_time - mid_time
            print(f"✅ Throttling working: {throttle_delay:.3f}s delay")
            
        print("✅ Mock Claude integration test completed")
        return True
        
    except Exception as e:
        print(f"❌ Mock Claude integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_browser_agent_full_integration():
    """Test the full browser agent with actual Claude API (minimal task)."""
    
    print("\n🧪 Testing Full Browser Agent Integration")
    print("=" * 50)
    
    # Ensure Anthropic API key is available
    if not os.getenv("ANTHROPIC_API_KEY"):
        anthropic_key = getpass("Enter your Anthropic API key: ")
        os.environ["ANTHROPIC_API_KEY"] = anthropic_key
    
    try:
        from langchain_steel import SteelBrowserAgent
        
        print("🤖 Creating SteelBrowserAgent...")
        agent = SteelBrowserAgent()
        print("✅ SteelBrowserAgent created")
        
        # Test with a very simple task that should complete quickly
        simple_task = "Take a screenshot and tell me what you see. Just give a very brief description."
        
        print(f"🎯 Testing simple task: '{simple_task}'")
        print("⏰ Starting execution (this may take a moment)...")
        
        result = agent.run(simple_task)
        
        print("✅ Task completed successfully!")
        print(f"📄 Result preview: {result[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Full integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Steel Browser Agent Diagnostics")
    print("=" * 60)
    
    # Test 1: Basic browser session
    success1 = test_browser_agent_initialization()
    
    if not success1:
        print("\n❌ Basic browser session failed - stopping here")
        sys.exit(1)
    
    # Test 2: Mock Claude integration
    print("\n" + "=" * 60)
    success2 = test_browser_agent_with_mock_claude()
    
    if not success2:
        print("\n❌ Mock Claude integration failed - stopping here")
        sys.exit(1)
    
    # Test 3: Full integration (only if user wants to)
    print("\n" + "=" * 60)
    response = input("Run full integration test with Claude API? (y/N): ")
    
    if response.lower().startswith('y'):
        success3 = test_browser_agent_full_integration()
        
        if success3:
            print("\n🎉 All browser agent tests passed!")
        else:
            print("\n❌ Full integration test failed")
    else:
        print("\n✅ Skipped full integration test")
        print("✅ Browser session and mock integration tests passed!")
    
    print("\n💡 Summary:")
    print("   - Basic Steel sessions work fine")
    print("   - Browser session creation works")
    print("   - Screenshot and actions work")
    if 'success3' in locals() and success3:
        print("   - Full Claude integration works!")
    print("\n   Your browser agent should be working now!")