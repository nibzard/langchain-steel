#!/usr/bin/env python3

import os
import asyncio
from dotenv import load_dotenv
from langchain_steel import SteelScrapeTool

load_dotenv()

async def get_top_3_hackernews_posts():
    """Get the top 3 posts from Hacker News using Steel scraping."""
    
    # Initialize the Steel Scrape Tool
    scraper = SteelScrapeTool()
    
    # Scrape Hacker News front page
    result = await scraper._arun(
        url="https://news.ycombinator.com",
        format="markdown",
        extract_links=True
    )
    
    return result

async def main():
    # Check for required environment variables
    if not os.getenv('STEEL_API_KEY'):
        print("Error: STEEL_API_KEY environment variable is required")
        return
    
    print("Scraping Hacker News for top posts...")
    try:
        content = await get_top_3_hackernews_posts()
        print("\nHacker News Content:")
        print("=" * 50)
        
        # Extract top 3 posts from the scraped content
        lines = content.split('\n')
        post_count = 0
        current_post = ""
        
        for line in lines:
            if line.strip():
                # Look for numbered posts or titles
                if any(char.isdigit() for char in line[:5]) and ('http' in line or len(line) > 20):
                    if post_count < 3:
                        print(f"\n{post_count + 1}. {line.strip()}")
                        post_count += 1
                    else:
                        break
        
        if post_count == 0:
            print("Raw content preview:")
            print(content[:1000] + "..." if len(content) > 1000 else content)
            
    except Exception as e:
        print(f"Error scraping posts: {e}")

if __name__ == "__main__":
    asyncio.run(main())