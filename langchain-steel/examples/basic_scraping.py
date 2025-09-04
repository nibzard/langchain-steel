#!/usr/bin/env python3
"""
Basic Web Scraping Example using Steel-LangChain Integration

This example demonstrates basic web scraping functionality using SteelScrapeTool.
It shows how to scrape content from web pages with different formats and options.

Requirements:
- Set STEEL_API_KEY environment variable
- Install langchain-steel package
"""

import os
import sys
from typing import Optional

# Add the parent directory to sys.path so we can import langchain_steel
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from langchain_steel import SteelScrapeTool, SteelConfig


def basic_scraping_example():
    """Demonstrate basic web scraping with Steel."""
    print("🔧 Basic Scraping Example")
    print("=" * 50)
    
    # Check for API key
    api_key = os.environ.get('STEEL_API_KEY')
    if not api_key:
        print("⚠️  Warning: STEEL_API_KEY not set. Using mock configuration.")
        print("   Set STEEL_API_KEY environment variable for live testing.")
        # Set a mock API key for testing
        os.environ['STEEL_API_KEY'] = 'mock-api-key-for-testing'
        api_key = 'mock-api-key-for-testing'
    
    # Initialize the scraping tool
    try:
        scraper = SteelScrapeTool()
        print("✅ SteelScrapeTool initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize SteelScrapeTool: {e}")
        return
    
    # Example URLs for testing
    test_urls = [
        "https://example.com",
        "https://httpbin.org/html",  # Returns simple HTML
        "https://quotes.toscrape.com/",  # Static content
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n🌐 Example {i}: Scraping {url}")
        print("-" * 40)
        
        try:
            # Basic scraping with markdown format
            result = scraper.invoke({"url": url, "format": "markdown"})
            
            if isinstance(result, str):
                # Truncate long content for display
                display_content = result[:500] + "..." if len(result) > 500 else result
                print(f"✅ Successfully scraped {len(result)} characters")
                print(f"📄 Content preview:\n{display_content}\n")
            else:
                print(f"⚠️  Unexpected result type: {type(result)}")
                print(f"📄 Result: {result}")
                
        except Exception as e:
            print(f"❌ Scraping failed for {url}: {e}")
    
    print("\n🎯 Basic scraping examples completed!")


def advanced_scraping_example():
    """Demonstrate advanced scraping options."""
    print("\n🔧 Advanced Scraping Example")
    print("=" * 50)
    
    # Ensure mock API key is set
    if not os.environ.get('STEEL_API_KEY'):
        os.environ['STEEL_API_KEY'] = 'mock-api-key-for-testing'
    
    # Initialize with configuration
    try:
        config = SteelConfig(
            api_key='mock-api-key-for-testing',
            default_format="markdown",
            session_timeout=30
        )
        scraper = SteelScrapeTool(config=config)
        print("✅ SteelScrapeTool with config initialized")
    except Exception as e:
        print(f"❌ Failed to initialize with config: {e}")
        return
    
    # Advanced scraping with multiple options
    url = "https://quotes.toscrape.com/"
    print(f"\n🎯 Advanced scraping of {url}")
    
    try:
        result = scraper.invoke({
            "url": url,
            "format": "markdown",
            "extract_links": True,
            "extract_images": True,
            "custom_headers": {
                "User-Agent": "Steel-LangChain-Example/1.0"
            }
        })
        
        if isinstance(result, str):
            print(f"✅ Advanced scraping successful")
            print(f"📊 Content length: {len(result)} characters")
            
            # Look for metadata section
            if "--- Metadata ---" in result:
                print("📋 Metadata extraction detected")
            
            # Display preview
            preview = result[:800] + "..." if len(result) > 800 else result
            print(f"📄 Content with metadata:\n{preview}")
        else:
            print(f"⚠️  Unexpected result: {result}")
            
    except Exception as e:
        print(f"❌ Advanced scraping failed: {e}")
    
    print("\n🎯 Advanced scraping example completed!")


def format_comparison_example():
    """Compare different output formats."""
    print("\n🔧 Format Comparison Example")
    print("=" * 50)
    
    # Ensure mock API key is set
    if not os.environ.get('STEEL_API_KEY'):
        os.environ['STEEL_API_KEY'] = 'mock-api-key-for-testing'
    
    scraper = SteelScrapeTool()
    url = "https://example.com"
    formats = ["html", "markdown", "text"]
    
    for format_type in formats:
        print(f"\n📝 Testing format: {format_type}")
        print("-" * 30)
        
        try:
            result = scraper.invoke({
                "url": url,
                "format": format_type
            })
            
            if isinstance(result, str):
                preview = result[:300] + "..." if len(result) > 300 else result
                print(f"✅ {format_type.upper()} format:")
                print(f"   Length: {len(result)} characters")
                print(f"   Preview: {preview}")
            else:
                print(f"⚠️  {format_type} result: {result}")
                
        except Exception as e:
            print(f"❌ {format_type} format failed: {e}")
    
    print("\n🎯 Format comparison completed!")


def main():
    """Run all basic scraping examples."""
    print("🚀 Steel-LangChain Basic Scraping Examples")
    print("=" * 60)
    
    try:
        # Run examples
        basic_scraping_example()
        advanced_scraping_example()
        format_comparison_example()
        
        print("\n✅ All basic scraping examples completed successfully!")
        print("\n💡 Next steps:")
        print("   - Set STEEL_API_KEY for live testing")
        print("   - Try different URLs and formats")
        print("   - Explore the browser automation examples")
        
    except KeyboardInterrupt:
        print("\n⚠️  Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Examples failed: {e}")
        raise


if __name__ == "__main__":
    main()