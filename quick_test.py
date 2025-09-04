#!/usr/bin/env python3
"""Quick test of the refactored Steel browser agent with provided API keys."""

import os
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


async def quick_test():
    """Quick test to verify the browser agent works."""
    
    # Check API keys are loaded
    steel_key = os.getenv("STEEL_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not steel_key or not anthropic_key:
        print("❌ ERROR: API keys not found in environment")
        return False
    
    print("✅ API keys loaded successfully")
    print(f"   Steel key: {steel_key[:20]}...")
    print(f"   Anthropic key: {anthropic_key[:20]}...")
    
    try:
        # Test the direct computer use function
        from langchain_steel.agents.computer_use import run_browser_task
        
        print("\n🚀 Testing direct browser automation...")
        result = await run_browser_task(
            steel_api_key=steel_key,
            anthropic_api_key=anthropic_key,
            task="Go to example.com and tell me what the main heading says",
            max_steps=10
        )
        
        print(f"\n📊 Results:")
        print(f"Success: {result.get('success')}")
        print(f"Steps: {result.get('steps')}")
        print(f"Result: {result.get('result')}")
        print(f"Session URL: {result.get('session_url')}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False


async def test_langchain_interface():
    """Test the LangChain interface."""
    try:
        from langchain_steel import SteelBrowserAgent
        
        print("\n🔗 Testing LangChain interface...")
        agent = SteelBrowserAgent()
        
        result = await agent._arun(
            task="Go to httpbin.org/user-agent and tell me what browser user agent is shown",
            max_steps=10
        )
        
        print(f"\n📋 LangChain Result:")
        print(result)
        return True
        
    except Exception as e:
        print(f"❌ LangChain test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 Quick Test - Steel Browser Agent")
    print("=" * 60)
    
    # Test 1: Direct function
    success1 = await quick_test()
    
    # Test 2: LangChain interface  
    success2 = await test_langchain_interface()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 ALL TESTS PASSED! Browser agent is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())