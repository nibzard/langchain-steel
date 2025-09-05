#!/usr/bin/env python3

import os
import asyncio
from dotenv import load_dotenv
from steel import AsyncSteel

load_dotenv()

async def search_nintendo_switch_2_croatia():
    """Search for Nintendo Switch 2 pricing in Croatia using Steel scraping."""
    
    if not os.getenv('STEEL_API_KEY'):
        print("❌ Error: STEEL_API_KEY environment variable is required")
        return
    
    print("🎮 Searching for Nintendo Switch 2 pricing in Croatia...")
    print("=" * 60)
    
    try:
        # Initialize AsyncSteel client
        client = AsyncSteel(steel_api_key=os.getenv('STEEL_API_KEY'))
        
        # Croatian retail sites to check
        sites_to_check = [
            {
                "name": "Links.hr",
                "url": "https://www.links.hr",
                "description": "Major Croatian electronics retailer"
            },
            {
                "name": "Sancta Domenica", 
                "url": "https://www.sancta-domenica.hr",
                "description": "Croatian tech and gaming store"
            }
        ]
        
        print("🔍 Checking Croatian retail sites for Nintendo Switch 2...")
        
        for site in sites_to_check:
            print(f"\n📱 Checking {site['name']} ({site['description']})")
            print("-" * 50)
            
            try:
                response = await client.scrape(url=site['url'])
                
                if hasattr(response, 'content') and hasattr(response.content, 'html'):
                    content = response.content.html.lower()
                    
                    # Look for Nintendo Switch 2 related keywords
                    switch_keywords = ['nintendo switch 2', 'switch 2', 'nintendo switch pro']
                    found_keywords = []
                    
                    for keyword in switch_keywords:
                        if keyword in content:
                            found_keywords.append(keyword)
                    
                    if found_keywords:
                        print(f"✅ Found Nintendo Switch 2 references: {', '.join(found_keywords)}")
                        
                        # Look for price patterns (HRK or EUR)
                        import re
                        price_patterns = [
                            r'(\d{1,4}[.,]\d{2})\s*(?:hrk|kn|kuna)',  # Croatian Kuna
                            r'(\d{1,4}[.,]\d{2})\s*(?:eur|€)',        # Euros
                            r'(\d{1,4})\s*(?:hrk|kn|kuna)',           # Kuna without decimals
                            r'(\d{1,4})\s*(?:eur|€)'                  # Euros without decimals
                        ]
                        
                        prices_found = []
                        for pattern in price_patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            prices_found.extend(matches)
                        
                        if prices_found:
                            print(f"💰 Potential prices found: {', '.join(set(prices_found))}")
                        else:
                            print("💰 No specific prices found on homepage")
                    else:
                        print("❌ No Nintendo Switch 2 references found on homepage")
                
            except Exception as e:
                print(f"❌ Error checking {site['name']}: {e}")
        
        # Provide manual search guidance
        print(f"\n💡 Manual Search Recommendations:")
        print("=" * 60)
        print("Since Nintendo Switch 2 may not be officially released yet, try:")
        print("1. 🔍 Google.hr: 'Nintendo Switch 2 cijena Hrvatska 2025'")
        print("2. 📰 Gaming news sites: GameZoom.net, Bug.hr")
        print("3. 🛒 Check major retailers directly:")
        print("   • Links.hr - Search for Nintendo products")
        print("   • Sancta-Domenica.hr - Gaming section") 
        print("   • Konzum.hr - Electronics department")
        print("4. 💬 Croatian gaming forums for pre-order discussions")
        print("\n📅 Note: Nintendo Switch 2 may not be officially announced/released yet.")
        
    except Exception as e:
        print(f"❌ General error: {e}")

if __name__ == "__main__":
    asyncio.run(search_nintendo_switch_2_croatia())