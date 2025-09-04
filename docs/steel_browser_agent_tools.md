# Steel Browser Agent Tools

[Steel.dev](https://steel.dev) provides advanced browser automation tools that enable AI agents to perform complex, multi-step web interactions using Claude Computer Use capabilities.

## Installation

```bash
pip install langchain-steel
```

Get your API key from [steel.dev](https://steel.dev) and set it:

```bash
# .env file
STEEL_API_KEY=your-steel-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
```

## Quick Start

### Simple Direct Usage

```python
from langchain_steel.agents.computer_use import run_browser_task
import os

# Direct function call
result = await run_browser_task(
    steel_api_key=os.getenv("STEEL_API_KEY"),
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    task="Go to Hacker News and get the top 5 posts",
    max_steps=20
)

print(f"Success: {result['success']}")
print(f"Result: {result['result']}")
print(f"Session replay: {result['session_url']}")
```

### LangChain Integration

```python
from langchain_steel import SteelBrowserAgent

# Initialize agent
agent = SteelBrowserAgent()

# Natural language automation
result = agent.run({
    "task": "Go to GitHub trending and get the top 3 Python repositories",
    "max_steps": 25
})

print(result)
```

## Core Features

### 🤖 Natural Language Automation
Use plain English to describe complex browser tasks:

```python
task = """
1. Navigate to GitHub.com
2. Search for 'langchain' repositories
3. Sort results by stars (descending)  
4. Get details from the top 3 repositories:
   - Repository name and description
   - Star count and primary language
   - Last update date
5. Return as structured information
"""

result = await run_browser_task(
    steel_api_key="your-key",
    anthropic_api_key="your-key",
    task=task
)
```

### ⚡ Clean Architecture
The refactored implementation uses a clean, simple architecture:

- **SteelBrowser**: Manages browser sessions and actions
- **ClaudeAgent**: Handles Claude Computer Use integration
- **run_browser_task()**: Main entry point for direct usage
- **SteelBrowserAgent**: LangChain tool wrapper

### 🔧 Advanced Configuration

```python
# Enable proxy and CAPTCHA solving
result = await run_browser_task(
    steel_api_key="your-key",
    anthropic_api_key="your-key",
    task="Navigate to a protected site and extract data",
    max_steps=30,
    use_proxy=True,      # Enable proxy rotation
    solve_captcha=True   # Enable CAPTCHA solving
)
```

## Steel Plan Compatibility

### Hobby Plan (Free/Entry Level)
- ✅ Basic browser automation
- ✅ Natural language task execution
- ✅ Session replay URLs
- ❌ CAPTCHA solving (requires upgrade)
- ❌ Proxy usage (requires upgrade)

### Professional/Enterprise Plans
- ✅ All hobby plan features
- ✅ Automatic CAPTCHA solving (`solve_captcha=True`)
- ✅ Proxy rotation (`use_proxy=True`)
- ✅ Higher rate limits and concurrent sessions

## Usage Examples

### Web Scraping

```python
# Extract data from a website
task = "Go to example.com and tell me what the main heading says"

result = await run_browser_task(
    steel_api_key=os.getenv("STEEL_API_KEY"),
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    task=task,
    max_steps=10
)
```

### Form Interaction

```python
# Fill and submit forms
task = """
1. Go to httpbin.org/forms/post
2. Fill the customer name field with 'Test User'
3. Fill the telephone field with '555-1234' 
4. Fill the email field with 'test@example.com'
5. Tell me what fields are available on the form
"""

result = await run_browser_task(
    steel_api_key="your-key",
    anthropic_api_key="your-key",
    task=task,
    max_steps=20
)
```

### Search and Data Extraction

```python
# Complex search task
task = """
1. Go to DuckDuckGo
2. Search for 'LangChain tutorial'
3. Get the titles and URLs of the first 3 search results
4. Return the information in a structured format
"""

result = await run_browser_task(
    steel_api_key="your-key",
    anthropic_api_key="your-key", 
    task=task,
    max_steps=25
)
```

## LangChain Agent Integration

### Single Agent Setup

```python
from langchain_steel import SteelBrowserAgent
from langchain.agents import initialize_agent, AgentType
from langchain_anthropic import ChatAnthropic

# Initialize tools
browser_agent = SteelBrowserAgent()

# Create agent
agent = initialize_agent(
    tools=[browser_agent],
    llm=ChatAnthropic(model="claude-3-sonnet-20240229"),
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# Execute complex task
result = agent.run("""
Research the top 3 AI companies by analyzing their websites 
and extract key information about their products and services.
""")
```

### Async Usage

```python
from langchain_steel import SteelBrowserAgent

agent = SteelBrowserAgent()

# Async execution
result = await agent._arun(
    task="Go to GitHub trending and get repository information",
    max_steps=20,
    use_proxy=False,
    solve_captcha=False
)
```

## Advanced Use Cases

### E-commerce Price Monitoring

```python
async def monitor_product_price(product_url: str, target_price: float):
    """Monitor product price and get alerts."""
    
    task = f"""
    1. Go to {product_url}
    2. Extract the current price and product availability
    3. Check if price is <= ${target_price}
    4. Get product details: name, current price, rating, availability
    5. Return structured price monitoring data
    """
    
    result = await run_browser_task(
        steel_api_key=os.getenv("STEEL_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        task=task,
        max_steps=15
    )
    
    return result

# Monitor a product
price_data = await monitor_product_price(
    "https://example-store.com/product/123", 
    99.99
)
```

### Social Media Research

```python
async def research_trending_topics(platform: str, topic: str):
    """Research trending topics on social platforms."""
    
    if platform == "twitter":
        task = f"""
        1. Go to twitter.com/search
        2. Search for '{topic}'
        3. Get the first 10 recent tweets about this topic
        4. Extract tweet content, author, and engagement metrics
        5. Return structured data
        """
    elif platform == "reddit":
        task = f"""
        1. Go to reddit.com/search
        2. Search for '{topic}'
        3. Get top 10 posts with titles, upvotes, and comments
        4. Return structured post data
        """
    
    result = await run_browser_task(
        steel_api_key=os.getenv("STEEL_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        task=task,
        max_steps=25,
        use_proxy=True  # Use proxy for social media
    )
    
    return result

# Research AI trends
twitter_data = await research_trending_topics("twitter", "artificial intelligence")
reddit_data = await research_trending_topics("reddit", "machine learning")
```

### Lead Generation

```python
async def find_company_contacts(company_name: str, role: str):
    """Find contact information for specific roles at companies."""
    
    task = f"""
    1. Go to LinkedIn
    2. Search for people at '{company_name}' with role '{role}'
    3. Get information from the first 5 results:
       - Full name and title
       - Company and department  
       - Location
       - Profile summary
    4. Return structured contact data
    """
    
    result = await run_browser_task(
        steel_api_key=os.getenv("STEEL_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        task=task,
        max_steps=30,
        use_proxy=True,
        solve_captcha=True
    )
    
    return result

# Generate leads
contacts = await find_company_contacts("OpenAI", "Machine Learning Engineer")
```

## Error Handling and Debugging

### Session Replay URLs
Every browser session provides a replay URL for debugging:

```python
result = await run_browser_task(
    steel_api_key="your-key",
    anthropic_api_key="your-key",
    task="Your task here"
)

# View the session replay
print(f"Session replay: {result['session_url']}")
# Example: https://app.steel.dev/sessions/abc123-def456-ghi789
```

### Robust Error Handling

```python
async def robust_automation(task: str, max_retries: int = 3):
    """Browser automation with error recovery."""
    
    for attempt in range(max_retries):
        try:
            result = await run_browser_task(
                steel_api_key=os.getenv("STEEL_API_KEY"),
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
                task=task,
                max_steps=20
            )
            
            if result['success']:
                return result
                
        except Exception as e:
            if "rate_limit" in str(e).lower():
                wait_time = 2 ** attempt  # Exponential backoff
                await asyncio.sleep(wait_time)
            elif attempt == max_retries - 1:
                raise e
    
    return {"success": False, "error": "Max retries exceeded"}

# Usage with error recovery
result = await robust_automation("Complex automation task")
```

### Rate Limit Handling
The implementation includes automatic rate limit handling:

```python
# Rate limits are handled automatically
result = await run_browser_task(
    steel_api_key="your-key",
    anthropic_api_key="your-key", 
    task="Your task",
    max_steps=30  # More steps = more API calls
)

# Check logs for rate limit messages:
# "Rate limit hit, waiting 1.5s..."
```

## Configuration Options

### Basic Configuration

```python
# Simple task
result = await run_browser_task(
    steel_api_key="your-key",
    anthropic_api_key="your-key",
    task="Go to example.com and get the heading",
    max_steps=10                    # Limit automation steps
)
```

### Advanced Configuration

```python
# Advanced task with all options
result = await run_browser_task(
    steel_api_key="your-key",
    anthropic_api_key="your-key",
    task="Complex automation task",
    max_steps=30,                   # Maximum automation steps
    use_proxy=True,                 # Enable proxy (requires paid plan)
    solve_captcha=True              # Enable CAPTCHA solving (requires paid plan)
)
```

### LangChain Tool Configuration

```python
from langchain_steel import SteelBrowserAgent

# Basic agent
agent = SteelBrowserAgent()

# Use with parameters
result = await agent._arun(
    task="Your automation task",
    max_steps=25,
    use_proxy=False,
    solve_captcha=False
)
```

## Testing and Development

### Environment Setup

Create a `.env` file:
```bash
STEEL_API_KEY=your-steel-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
```

### Simple Test Script

```python
#!/usr/bin/env python3
import asyncio
import os
from dotenv import load_dotenv
from langchain_steel.agents.computer_use import run_browser_task

load_dotenv()

async def test_browser_agent():
    result = await run_browser_task(
        steel_api_key=os.getenv("STEEL_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        task="Go to example.com and tell me what you see",
        max_steps=8
    )
    
    print(f"Success: {result['success']}")
    print(f"Result: {result['result']}")
    print(f"Session: {result['session_url']}")

if __name__ == "__main__":
    asyncio.run(test_browser_agent())
```

## Troubleshooting

### Common Issues

**"Steel.__init__() got an unexpected keyword argument 'api_key'" Error**
```
Solution: This was fixed in the refactored version. The Steel client now uses
steel_api_key parameter. Update to the latest version.
```

**"Keyboard.press: Unknown key" Error**
```
Solution: Key mapping issue fixed in the refactored version. The implementation
now handles all common key combinations properly.
```

**Rate Limit Errors**
```
Solution: The implementation includes automatic rate limit handling with
exponential backoff. If you hit limits frequently, consider:
- Reducing max_steps 
- Adding delays between tasks
- Upgrading your Anthropic plan
```

**"Target page, context or browser has been closed" Error**
```
Solution: Session management issue. The refactored implementation includes
better session handling and cleanup. This error should be rare.
```

### Plan Compatibility

**Hobby Plan Users:**
- Use default settings (`use_proxy=False`, `solve_captcha=False`)
- Limited to basic browser automation
- Session replay URLs available for debugging

**Paid Plan Users:**
- Enable advanced features (`use_proxy=True`, `solve_captcha=True`)
- Higher rate limits and concurrent sessions
- Advanced stealth and proxy features

## API Reference

### Core Function

```python
async def run_browser_task(
    steel_api_key: str,
    anthropic_api_key: str,
    task: str,
    max_steps: int = 30,
    use_proxy: bool = False,
    solve_captcha: bool = False
) -> Dict[str, Any]:
    """
    Run a browser automation task.
    
    Returns:
        {
            "success": bool,
            "result": str,
            "steps": int,
            "session_url": str
        }
    """
```

### LangChain Tool

```python
class SteelBrowserAgent(BaseSteelTool):
    """
    LangChain tool for browser automation.
    
    Methods:
        run(input: dict) -> str
        _arun(task: str, max_steps: int = 30, ...) -> str
    """
```

For more information:
- [Steel API Documentation](https://docs.steel.dev)
- [Anthropic Claude Computer Use](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/computer-use-tool)
- [LangChain Tools](https://docs.langchain.com/docs/components/agents/tools/)