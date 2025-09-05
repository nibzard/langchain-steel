#!/usr/bin/env python3

import os
import asyncio
from dotenv import load_dotenv
from langchain_steel import SteelBrowserAgent

load_dotenv()

async def get_top_3_hackernews_posts():
    """Get the top 3 posts from Hacker News today."""
    
    # Initialize the Steel Browser Agent
    agent = SteelBrowserAgent()
    
    # Navigate to Hacker News
    result = await agent.arun("Go to https://news.ycombinator.com and get the titles and URLs of the top 3 posts")
    
    return result

async def main():
    # Check for required environment variables
    if not os.getenv('STEEL_API_KEY'):
        print("Error: STEEL_API_KEY environment variable is required")
        return
    
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("Error: ANTHROPIC_API_KEY environment variable is required")
        return
    
    print("Fetching top 3 Hacker News posts...")
    try:
        posts = await get_top_3_hackernews_posts()
        print("\nTop 3 Hacker News Posts Today:")
        print("=" * 50)
        print(posts)
    except Exception as e:
        print(f"Error fetching posts: {e}")

if __name__ == "__main__":
    asyncio.run(main())