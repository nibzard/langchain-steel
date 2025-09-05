#!/usr/bin/env python3

import os
import asyncio
from dotenv import load_dotenv
from langchain_steel import SteelBrowserAgent

load_dotenv()

async def find_nintendo_switch_2_price():
    """Simple search for Nintendo Switch 2 pricing in Croatia."""
    
    # Check for required environment variables
    if not os.getenv('STEEL_API_KEY'):
        print("❌ Error: STEEL_API_KEY environment variable is required")
        return
    
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ Error: ANTHROPIC_API_KEY environment variable is required") 
        return
    
    print("🎮 Searching for Nintendo Switch 2 pricing in Croatia...")
    
    try:
        # Initialize the Steel Browser Agent
        agent = SteelBrowserAgent()
        
        # Single focused task
        search_query = """
        Go to Google and search for "Nintendo Switch 2 price Croatia 2025". 
        Look for recent news, retail prices, or availability information for Nintendo Switch 2 in Croatia. 
        Provide a summary of what you find including any prices in Croatian Kuna (HRK) or Euros (EUR).
        """
        
        print("🔍 Searching...")
        result = await agent.arun(search_query)
        
        print("\n🎯 Results:")
        print("=" * 50)
        print(result)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
        # Provide manual alternatives
        print("\n💡 Manual search alternatives:")
        print("1. Google.hr: Search 'Nintendo Switch 2 cijena Hrvatska'")
        print("2. Links.hr - Croatian electronics retailer")
        print("3. Sancta-Domenica.hr - Croatian tech store")
        print("4. Gaming forums: Bug.hr, GameZoom.net")

if __name__ == "__main__":
    asyncio.run(find_nintendo_switch_2_price())