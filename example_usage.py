#!/usr/bin/env python3
"""Example usage of the refactored Steel browser agent for LangChain."""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def example_simple_task():
    """Example: Simple web scraping task."""
    from langchain_steel import SteelBrowserAgent
    
    agent = SteelBrowserAgent()
    
    # Task: Get top posts from Hacker News
    result = await agent._arun(
        task="Go to Hacker News and get the titles of the top 5 posts",
        max_steps=20
    )
    
    print("Hacker News Top Posts:")
    print(result)
    return result


async def example_search_task():
    """Example: Perform a search and extract results."""
    from langchain_steel import SteelBrowserAgent
    
    agent = SteelBrowserAgent()
    
    # Task: Search and extract information
    result = await agent._arun(
        task="Go to DuckDuckGo, search for 'LangChain tutorial', and get the first 3 search results",
        max_steps=25
    )
    
    print("Search Results:")
    print(result)
    return result


async def example_with_langchain():
    """Example: Use browser agent in a LangChain chain."""
    from langchain_steel import SteelBrowserAgent
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain_anthropic import ChatAnthropic
    from langchain.prompts import PromptTemplate
    
    # Initialize browser agent
    browser_tool = SteelBrowserAgent()
    
    # Create a simple chain that uses the browser
    llm = ChatAnthropic(model="claude-3-sonnet-20240229")
    
    # Direct tool usage
    result = browser_tool.run({
        "task": "Go to python.org and tell me what the latest Python version is",
        "max_steps": 15
    })
    
    print("Python.org Information:")
    print(result)
    return result


async def example_data_extraction():
    """Example: Extract structured data from a website."""
    from langchain_steel import SteelBrowserAgent
    
    agent = SteelBrowserAgent()
    
    # Task: Extract structured data
    result = await agent._arun(
        task=(
            "Go to github.com/langchain-ai/langchain and extract: "
            "1) The number of stars, "
            "2) The number of forks, "
            "3) The main programming language"
        ),
        max_steps=20
    )
    
    print("GitHub Repository Information:")
    print(result)
    return result


async def example_form_interaction():
    """Example: Interact with forms on a website."""
    from langchain_steel import SteelBrowserAgent
    
    agent = SteelBrowserAgent()
    
    # Task: Form interaction (using a test site)
    result = await agent._arun(
        task=(
            "Go to httpbin.org/forms/post and: "
            "1) Fill the customer name field with 'Test User', "
            "2) Fill the telephone field with '555-1234', "
            "3) Fill the email field with 'test@example.com', "
            "4) Tell me what fields are on the form"
        ),
        max_steps=25
    )
    
    print("Form Interaction Result:")
    print(result)
    return result


async def example_with_proxy():
    """Example: Use browser agent with proxy enabled."""
    from langchain_steel import SteelBrowserAgent
    
    agent = SteelBrowserAgent()
    
    # Task: Check IP with proxy
    result = await agent._arun(
        task="Go to httpbin.org/ip and tell me what IP address is displayed",
        max_steps=10,
        use_proxy=True  # Enable proxy
    )
    
    print("IP Check with Proxy:")
    print(result)
    return result


def run_sync_example():
    """Example: Run browser agent synchronously."""
    from langchain_steel import SteelBrowserAgent
    
    agent = SteelBrowserAgent()
    
    # Synchronous execution
    result = agent.run({
        "task": "Go to example.com and tell me what the page says",
        "max_steps": 10
    })
    
    print("Synchronous Result:")
    print(result)
    return result


async def main():
    """Run various examples."""
    print("=" * 80)
    print("Steel Browser Agent Examples")
    print("=" * 80)
    
    examples = [
        ("Simple Web Scraping", example_simple_task),
        ("Search Task", example_search_task),
        ("Data Extraction", example_data_extraction),
        ("Form Interaction", example_form_interaction),
        ("Proxy Usage", example_with_proxy),
    ]
    
    for name, example_func in examples:
        print(f"\n{'='*60}")
        print(f"Example: {name}")
        print('='*60)
        
        try:
            await example_func()
        except Exception as e:
            print(f"Error in {name}: {e}")
        
        print("\n")
    
    # Run synchronous example
    print(f"\n{'='*60}")
    print("Example: Synchronous Execution")
    print('='*60)
    try:
        run_sync_example()
    except Exception as e:
        print(f"Error in sync example: {e}")


if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("STEEL_API_KEY"):
        print("ERROR: STEEL_API_KEY environment variable not set")
        print("Please set it in your .env file or environment")
        exit(1)
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Please set it in your .env file or environment")
        exit(1)
    
    # Run examples
    asyncio.run(main())