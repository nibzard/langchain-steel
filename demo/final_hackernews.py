#!/usr/bin/env python3

import os
import re
import asyncio
from dotenv import load_dotenv
from steel import AsyncSteel

load_dotenv()

async def get_top_3_hackernews_posts():
    """Get top 3 posts from Hacker News using Steel SDK."""
    
    if not os.getenv('STEEL_API_KEY'):
        print("Error: STEEL_API_KEY environment variable is required")
        return
    
    try:
        # Initialize AsyncSteel client
        client = AsyncSteel(steel_api_key=os.getenv('STEEL_API_KEY'))
        
        # Scrape Hacker News
        response = await client.scrape(url="https://news.ycombinator.com")
        
        if hasattr(response, 'content') and hasattr(response.content, 'html'):
            html_content = response.content.html
            
            # Extract posts using regex
            # Look for the pattern: <span class="rank">1.</span>...title...
            rank_pattern = r'<span class="rank">(\d+)\.</span>.*?<span class="titleline"><a href="([^"]*)"[^>]*>([^<]+)</a>'
            
            matches = re.findall(rank_pattern, html_content, re.DOTALL)
            
            print("\n🚀 Top 3 Hacker News Posts Today:")
            print("=" * 60)
            
            for i in range(min(3, len(matches))):
                rank, url, title = matches[i]
                print(f"\n{int(rank)}. {title}")
                print(f"   🔗 {url}")
            
            if len(matches) == 0:
                print("No posts found in the expected format")
            
        else:
            print("Unexpected response format from Steel")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(get_top_3_hackernews_posts())