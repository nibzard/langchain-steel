#!/usr/bin/env python3
"""Test script for the refactored Steel browser agent."""

import os
import asyncio
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


async def test_browser_agent_langchain():
    """Test the browser agent through LangChain interface."""
    from langchain_steel import SteelBrowserAgent
    
    # Initialize agent
    agent = SteelBrowserAgent()
    
    # Test tasks
    test_tasks = [
        # Simple navigation and data extraction
        {
            "task": "Go to Hacker News and get the titles of the top 5 posts",
            "max_steps": 20
        },
        # Search task
        {
            "task": "Go to Google, search for 'Python web scraping', and get the first 3 results",
            "max_steps": 25
        },
        # GitHub exploration
        {
            "task": "Go to github.com/anthropics and list the first 5 repository names you see",
            "max_steps": 20
        }
    ]
    
    for i, test_case in enumerate(test_tasks, 1):
        print(f"\n{'='*60}")
        print(f"Test Case {i}: {test_case['task'][:50]}...")
        print('='*60)
        
        try:
            # Run the task
            result = await agent._arun(
                task=test_case["task"],
                max_steps=test_case.get("max_steps", 20)
            )
            
            print(f"\nResult:\n{result}")
            
        except Exception as e:
            print(f"Error: {e}")
            logger.exception("Test failed")


async def test_direct_computer_use():
    """Test the computer use module directly."""
    from langchain_steel.agents.computer_use import run_browser_task
    
    # Get API keys
    steel_api_key = os.getenv("STEEL_API_KEY")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not steel_api_key or not anthropic_api_key:
        print("ERROR: Missing required API keys")
        return
    
    # Test task
    result = await run_browser_task(
        steel_api_key=steel_api_key,
        anthropic_api_key=anthropic_api_key,
        task="Go to example.com and tell me what the main heading says",
        max_steps=10
    )
    
    print("\n" + "="*60)
    print("Direct Computer Use Test")
    print("="*60)
    print(f"Success: {result.get('success')}")
    print(f"Result: {result.get('result')}")
    print(f"Steps: {result.get('steps')}")
    print(f"Session URL: {result.get('session_url')}")


async def test_with_proxy_and_captcha():
    """Test browser agent with proxy and CAPTCHA solving enabled."""
    from langchain_steel import SteelBrowserAgent
    
    agent = SteelBrowserAgent()
    
    print("\n" + "="*60)
    print("Testing with Proxy and CAPTCHA Solving")
    print("="*60)
    
    result = await agent._arun(
        task="Go to httpbin.org/ip and tell me what IP address is shown",
        max_steps=15,
        use_proxy=True,
        solve_captcha=True
    )
    
    print(f"\nResult:\n{result}")


async def main():
    """Run all tests."""
    print("Starting Browser Agent Tests")
    print("="*80)
    
    # Test 1: Direct computer use
    print("\n[Test 1] Direct Computer Use Module")
    try:
        await test_direct_computer_use()
    except Exception as e:
        logger.error(f"Direct test failed: {e}")
    
    # Test 2: LangChain interface
    print("\n[Test 2] LangChain Browser Agent")
    try:
        await test_browser_agent_langchain()
    except Exception as e:
        logger.error(f"LangChain test failed: {e}")
    
    # Test 3: Proxy and CAPTCHA features
    print("\n[Test 3] Advanced Features (Proxy/CAPTCHA)")
    try:
        await test_with_proxy_and_captcha()
    except Exception as e:
        logger.error(f"Advanced features test failed: {e}")
    
    print("\n" + "="*80)
    print("All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())