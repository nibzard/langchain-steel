#!/usr/bin/env python3

import os
import asyncio
from dotenv import load_dotenv
from steel import AsyncSteel

load_dotenv()

async def get_hackernews_top_posts():
    """Get top posts from Hacker News using Steel SDK directly."""
    
    # Check for required environment variables
    if not os.getenv('STEEL_API_KEY'):
        print("Error: STEEL_API_KEY environment variable is required")
        return
    
    print("Scraping Hacker News for top posts...")
    
    try:
        # Initialize AsyncSteel client
        client = AsyncSteel(steel_api_key=os.getenv('STEEL_API_KEY'))
        
        # Scrape Hacker News
        response = await client.scrape(
            url="https://news.ycombinator.com"
        )
        
        print("\nHacker News Response Debug:")
        print("=" * 50)
        
        # Debug: Print response structure
        print(f"Response type: {type(response)}")
        print(f"Response attributes: {dir(response) if hasattr(response, '__dict__') else 'N/A'}")
        
        if response:
            print(f"Response: {response}")
            
            # Try different attributes
            if hasattr(response, 'content'):
                print(f"Content: {response.content}")
                if hasattr(response.content, 'markdown'):
                    content = response.content.markdown
                    if content:
                        print(f"\nMarkdown content (first 1000 chars):\n{content[:1000]}")
                        
                        # Look for top posts
                        lines = content.split('\n')
                        post_count = 0
                        
                        print(f"\nTop 3 Hacker News Posts Today:")
                        print("-" * 40)
                        
                        for line in lines:
                            stripped = line.strip()
                            # Look for numbered items (1., 2., 3., etc.) or other patterns
                            if stripped and (stripped[0].isdigit() or 'http' in stripped):
                                if post_count < 3:
                                    print(f"{post_count + 1}. {stripped}")
                                    post_count += 1
                                if post_count >= 3:
                                    break
                    else:
                        print("No markdown content found")
                else:
                    print(f"No markdown attribute, content attributes: {dir(response.content)}")
            else:
                print("No content attribute found")
        else:
            print("Response is None or empty")
            
    except Exception as e:
        print(f"Error scraping posts: {e}")

if __name__ == "__main__":
    asyncio.run(get_hackernews_top_posts())