#!/usr/bin/env python3
"""Demo: Get top Hacker News posts using the refactored Steel browser agent."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def demo_hacker_news():
    """Demo task: Get top posts from Hacker News."""
    from langchain_steel.agents.computer_use import run_browser_task
    
    print("🚀 Demo: Getting top 5 Hacker News posts")
    print("=" * 60)
    
    result = await run_browser_task(
        steel_api_key=os.getenv("STEEL_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        task="Go to Hacker News (news.ycombinator.com) and get the titles and points of the top 5 posts",
        max_steps=20
    )
    
    print(f"\n📊 Results:")
    print(f"Success: {result.get('success')}")
    print(f"Steps taken: {result.get('steps')}")
    print(f"\n📄 Content extracted:")
    print(result.get('result', '').replace('TASK_COMPLETED:', '').strip())
    print(f"\n🔗 Session replay: {result.get('session_url')}")
    
    return result


async def demo_langchain_interface():
    """Demo using the LangChain interface."""
    from langchain_steel import SteelBrowserAgent
    
    print("\n" + "=" * 60)
    print("🔗 Demo: Using LangChain Interface")
    print("=" * 60)
    
    agent = SteelBrowserAgent()
    
    result = await agent._arun(
        task="Go to GitHub trending page (github.com/trending) and get the names of the top 3 trending Python repositories",
        max_steps=25
    )
    
    print(f"\n📋 LangChain Result:")
    print(result)


if __name__ == "__main__":
    asyncio.run(demo_hacker_news())
    asyncio.run(demo_langchain_interface())