#!/usr/bin/env python3

import os
import asyncio
from dotenv import load_dotenv
from langchain_steel import SteelBrowserAgent

load_dotenv()

async def find_nintendo_switch_2_price_croatia():
    """Find Nintendo Switch 2 pricing in Croatia using Steel Browser Agent."""
    
    # Check for required environment variables
    if not os.getenv('STEEL_API_KEY'):
        print("❌ Error: STEEL_API_KEY environment variable is required")
        return
    
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ Error: ANTHROPIC_API_KEY environment variable is required")
        return
    
    print("🎮 Searching for Nintendo Switch 2 pricing in Croatia...")
    print("=" * 60)
    
    try:
        # Initialize the Steel Browser Agent
        agent = SteelBrowserAgent()
        
        # Search strategy: Check multiple Croatian retail sites
        search_tasks = [
            "Go to https://www.google.hr and search for 'Nintendo Switch 2 cijena Hrvatska' (Nintendo Switch 2 price Croatia). Find current pricing information from Croatian retailers.",
            
            "Visit Croatian electronics retailers like Links.hr, Sancta Domenica, or other major Croatian tech stores to find Nintendo Switch 2 pricing and availability.",
            
            "Check if Nintendo Switch 2 is available for pre-order or purchase in Croatia, and gather pricing information in Croatian Kuna (HRK) or Euros (EUR)."
        ]
        
        print("🔍 Task 1: Google search for Nintendo Switch 2 prices in Croatia")
        print("-" * 50)
        
        result1 = await agent.arun(search_tasks[0])
        print("📋 Result:")
        print(result1)
        print("\n" + "="*60 + "\n")
        
        print("🏪 Task 2: Check Croatian electronics retailers")
        print("-" * 50)
        
        result2 = await agent.arun(search_tasks[1])
        print("📋 Result:")
        print(result2)
        print("\n" + "="*60 + "\n")
        
        print("💰 Task 3: Check availability and pricing details")
        print("-" * 50)
        
        result3 = await agent.arun(search_tasks[2])
        print("📋 Result:")
        print(result3)
        
        print("\n" + "🎯 SUMMARY" + "\n" + "="*60)
        print("Search completed! Check the results above for Nintendo Switch 2 pricing in Croatia.")
        
    except Exception as e:
        print(f"❌ Error during search: {e}")
        
        # If there's a rate limit, provide fallback information
        if "rate_limit" in str(e).lower():
            print("\n💡 Rate limit encountered. Here's what you can try manually:")
            print("1. Visit https://www.links.hr - Major Croatian electronics retailer")
            print("2. Check https://www.sancta-domenica.hr - Another major Croatian tech store")
            print("3. Search Google.hr for 'Nintendo Switch 2 cijena' for current pricing")
            print("4. Check Croatian gaming forums for latest pricing discussions")

async def main():
    await find_nintendo_switch_2_price_croatia()

if __name__ == "__main__":
    asyncio.run(main())