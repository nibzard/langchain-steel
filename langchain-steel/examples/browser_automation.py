#!/usr/bin/env python3
"""
Browser Automation Example using Steel-LangChain Integration

This example demonstrates complex browser automation using SteelBrowserAgent.
It shows how to perform multi-step web interactions using natural language.

Requirements:
- Set STEEL_API_KEY environment variable
- Install langchain-steel package
"""

import os
import sys
import json
from typing import Optional, Dict, Any

# Add the parent directory to sys.path so we can import langchain_steel
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from langchain_steel import SteelBrowserAgent, SteelConfig


def basic_browser_automation_example():
    """Demonstrate basic browser automation with natural language and optimized navigation."""
    print("🔧 Basic Browser Automation Example (Optimized)")
    print("=" * 60)
    
    # Check for API key
    api_key = os.environ.get('STEEL_API_KEY')
    if not api_key:
        print("⚠️  Warning: STEEL_API_KEY not set. Showing mock behavior.")
        print("   Set STEEL_API_KEY environment variable for live automation.")
    
    # Initialize browser agent with optimized settings
    try:
        browser_agent = SteelBrowserAgent()
        print("✅ SteelBrowserAgent initialized successfully with optimization features")
    except Exception as e:
        print(f"❌ Failed to initialize SteelBrowserAgent: {e}")
        return
    
    # Example automation tasks showcasing optimized navigation
    automation_tasks = [
        "Navigate to https://www.google.com and search for 'Steel.dev browser automation'",
        "Go to https://example.com and extract the main heading text",
        "Visit https://httpbin.org and get information about the current request headers"
    ]
    
    for i, task in enumerate(automation_tasks, 1):
        print(f"\n🤖 Task {i}: {task}")
        print("-" * 40)
        
        try:
            # Execute the automation task
            result = browser_agent.invoke({"task": task})
            
            if isinstance(result, str):
                # Truncate long results for display
                display_result = result[:600] + "..." if len(result) > 600 else result
                print(f"✅ Task completed successfully")
                print(f"📄 Result:\n{display_result}\n")
            else:
                print(f"⚠️  Unexpected result type: {type(result)}")
                print(f"📄 Result: {result}")
                
        except Exception as e:
            print(f"❌ Task failed: {e}")
    
    print("\n🎯 Basic browser automation examples completed!")


def advanced_browser_automation_example():
    """Demonstrate advanced browser automation with session management."""
    print("\n🔧 Advanced Browser Automation Example")
    print("=" * 50)
    
    # Initialize with advanced configuration
    try:
        config = SteelConfig(
            session_timeout=120,
            default_format="json"
        )
        browser_agent = SteelBrowserAgent(config=config)
        print("✅ Advanced SteelBrowserAgent initialized")
    except Exception as e:
        print(f"❌ Failed to initialize advanced agent: {e}")
        return
    
    # Complex multi-step task
    complex_task = """
    Navigate to a news website, find the top 3 headlines, 
    extract their titles and URLs, and return the information in JSON format.
    """
    
    print(f"\n🎯 Complex automation task:")
    print(f"   {complex_task}")
    
    try:
        result = browser_agent.invoke({
            "task": complex_task,
            "max_steps": 20,
            "return_format": "json",
            "session_options": {
                "stealth_mode": True,
                "solve_captcha": True
            }
        })
        
        print(f"✅ Complex automation successful")
        
        # Try to parse JSON result
        try:
            if isinstance(result, str):
                # Look for JSON in the result
                import re
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    json_data = json.loads(json_match.group())
                    print(f"📊 Parsed JSON result:")
                    print(json.dumps(json_data, indent=2))
                else:
                    print(f"📄 Text result:\n{result}")
            else:
                print(f"📄 Result:\n{result}")
        except json.JSONDecodeError:
            print(f"📄 Non-JSON result:\n{result}")
            
    except Exception as e:
        print(f"❌ Complex automation failed: {e}")
    
    print("\n🎯 Advanced browser automation example completed!")


def session_persistence_example():
    """Demonstrate session persistence across multiple tasks."""
    print("\n🔧 Session Persistence Example")
    print("=" * 50)
    
    browser_agent = SteelBrowserAgent()
    
    # Sequential tasks that build on each other
    session_tasks = [
        {
            "task": "Go to httpbin.org and remember the homepage content",
            "description": "Initial navigation"
        },
        {
            "task": "Navigate to the /json endpoint and extract the data",
            "description": "API endpoint interaction"
        },
        {
            "task": "Go back to the homepage and compare with what you remembered",
            "description": "Session state verification"
        }
    ]
    
    session_id = "demo_session_001"
    
    for i, task_info in enumerate(session_tasks, 1):
        task = task_info["task"]
        description = task_info["description"]
        
        print(f"\n📝 Step {i}: {description}")
        print(f"🤖 Task: {task}")
        print("-" * 40)
        
        try:
            result = browser_agent.invoke({
                "task": task,
                "session_id": session_id,
                "max_steps": 10
            })
            
            if isinstance(result, str):
                display_result = result[:400] + "..." if len(result) > 400 else result
                print(f"✅ Step {i} completed")
                print(f"📄 Result: {display_result}")
            else:
                print(f"📄 Step {i} result: {result}")
                
        except Exception as e:
            print(f"❌ Step {i} failed: {e}")
            break  # Don't continue if a step fails
    
    print(f"\n🎯 Session persistence example completed!")
    print(f"   Session ID used: {session_id}")


def data_extraction_example():
    """Demonstrate structured data extraction from web pages."""
    print("\n🔧 Data Extraction Example")
    print("=" * 50)
    
    browser_agent = SteelBrowserAgent()
    
    # Data extraction tasks
    extraction_tasks = [
        {
            "task": "Go to quotes.toscrape.com and extract all quotes with their authors",
            "expected": "List of quotes and authors"
        },
        {
            "task": "Visit httpbin.org/forms/post and extract all form fields",
            "expected": "Form field information"
        }
    ]
    
    for i, task_info in enumerate(extraction_tasks, 1):
        task = task_info["task"]
        expected = task_info["expected"]
        
        print(f"\n📊 Extraction {i}: {expected}")
        print(f"🤖 Task: {task}")
        print("-" * 40)
        
        try:
            result = browser_agent.invoke({
                "task": task,
                "return_format": "structured",
                "max_steps": 15
            })
            
            print(f"✅ Extraction {i} completed")
            
            if isinstance(result, str):
                display_result = result[:500] + "..." if len(result) > 500 else result
                print(f"📄 Extracted data:\n{display_result}")
            else:
                print(f"📄 Extracted data: {result}")
                
        except Exception as e:
            print(f"❌ Extraction {i} failed: {e}")
    
    print("\n🎯 Data extraction examples completed!")


def interactive_automation_example():
    """Demonstrate interactive automation with user input simulation."""
    print("\n🔧 Interactive Automation Example")
    print("=" * 50)
    
    browser_agent = SteelBrowserAgent()
    
    # Simulate form interactions
    form_tasks = [
        "Go to httpbin.org/forms/post and fill out the form with test data",
        "Navigate to a search form and perform a search for 'automation'",
        "Find any login form and inspect its structure without logging in"
    ]
    
    for i, task in enumerate(form_tasks, 1):
        print(f"\n🔄 Interactive Task {i}: {task}")
        print("-" * 40)
        
        try:
            result = browser_agent.invoke({
                "task": task,
                "max_steps": 25,
                "session_options": {
                    "wait_for_selector": True,
                    "handle_popups": True
                }
            })
            
            if isinstance(result, str):
                display_result = result[:400] + "..." if len(result) > 400 else result
                print(f"✅ Interactive task {i} completed")
                print(f"📄 Result: {display_result}")
            else:
                print(f"📄 Task {i} result: {result}")
                
        except Exception as e:
            print(f"❌ Interactive task {i} failed: {e}")
    
    print("\n🎯 Interactive automation examples completed!")


def rate_limiting_resilience_example():
    """Demonstrate rate limiting resilience and optimization features."""
    print("\n🔧 Rate Limiting Resilience Example")
    print("=" * 50)
    
    browser_agent = SteelBrowserAgent()
    
    # Tasks that would normally trigger rate limits with rapid execution
    rapid_tasks = [
        "Navigate to https://news.ycombinator.com",
        "Scroll down to see more posts",
        "Click on the first story link",
        "Go back to the main page",
        "Search for 'Claude AI'"
    ]
    
    print("🚀 Executing rapid sequence of tasks to test throttling...")
    print("   (In the optimized version, this should handle rate limits gracefully)")
    
    for i, task in enumerate(rapid_tasks, 1):
        print(f"\n⚡ Rapid Task {i}: {task}")
        print("-" * 40)
        
        try:
            result = browser_agent.invoke({
                "task": task,
                "max_steps": 8  # Limit steps for demonstration
            })
            
            if isinstance(result, str):
                display_result = result[:300] + "..." if len(result) > 300 else result
                print(f"✅ Task {i} completed successfully")
                print(f"📄 Result: {display_result}")
            else:
                print(f"📄 Task {i} result: {result}")
                
        except Exception as e:
            print(f"✅ Task {i} error handled gracefully: {e}")
    
    print("\n🎯 Rate limiting resilience test completed!")
    print("   Optimizations should have reduced API calls and handled any rate limits.")


def error_handling_example():
    """Demonstrate error handling in browser automation."""
    print("\n🔧 Error Handling Example")
    print("=" * 50)
    
    browser_agent = SteelBrowserAgent()
    
    # Tasks designed to test error scenarios
    error_test_tasks = [
        {
            "task": "Navigate to a non-existent website: https://this-site-definitely-does-not-exist-12345.com",
            "expected_error": "Network or DNS error"
        },
        {
            "task": "Go to example.com and click on a non-existent button with ID 'missing-button'",
            "expected_error": "Element not found error"
        },
        {
            "task": "Perform an impossible task: make the website change colors based on my thoughts",
            "expected_error": "Task cannot be completed error"
        }
    ]
    
    for i, task_info in enumerate(error_test_tasks, 1):
        task = task_info["task"]
        expected_error = task_info["expected_error"]
        
        print(f"\n🧪 Error Test {i}: {expected_error}")
        print(f"🤖 Task: {task}")
        print("-" * 40)
        
        try:
            result = browser_agent.invoke({
                "task": task,
                "max_steps": 5  # Limit steps for error scenarios
            })
            
            # Check if the result indicates an error or limitation
            if isinstance(result, str):
                if any(word in result.lower() for word in ['error', 'failed', 'cannot', 'unable']):
                    print(f"✅ Error handled gracefully: {result[:200]}...")
                else:
                    print(f"⚠️  Unexpected success: {result[:200]}...")
            else:
                print(f"📄 Result: {result}")
                
        except Exception as e:
            print(f"✅ Exception caught and handled: {e}")
    
    print("\n🎯 Error handling examples completed!")


def main():
    """Run all browser automation examples."""
    print("🚀 Steel-LangChain Browser Automation Examples (Optimized)")
    print("=" * 70)
    
    try:
        # Run examples
        basic_browser_automation_example()
        advanced_browser_automation_example()
        session_persistence_example()
        data_extraction_example()
        interactive_automation_example()
        rate_limiting_resilience_example()  # New example
        error_handling_example()
        
        print("\n✅ All browser automation examples completed!")
        print("\n💡 Next steps:")
        print("   - Set STEEL_API_KEY for live automation testing")
        print("   - Try custom automation tasks")
        print("   - Integrate with LangChain agents")
        print("   - Explore session management features")
        
    except KeyboardInterrupt:
        print("\n⚠️  Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Examples failed: {e}")
        raise


if __name__ == "__main__":
    main()