# Steel Browser Agent Tools

[Steel.dev](https://steel.dev) provides advanced browser automation tools that enable AI agents to perform complex, multi-step web interactions. These tools go beyond simple scraping to enable interactive workflows, form filling, navigation, and authenticated sessions.

## Installation

```bash
pip install langchain-steel
```

Get your API key from [steel.dev](https://steel.dev) and set it:

```python
import os
os.environ["STEEL_API_KEY"] = "your-api-key"
```

## Available Tools

### SteelBrowserAgent

High-level browser automation with natural language task descriptions.

```python
from langchain_steel import SteelBrowserAgent

agent = SteelBrowserAgent()

# Complex multi-step automation
result = agent.run("""
1. Navigate to GitHub.com
2. Search for 'langchain' repositories
3. Sort results by stars (descending)  
4. Get details from the top 3 repositories:
   - Repository name and description
   - Star count and primary language
   - Last update date
5. Return as structured JSON
""")

print(result)
```

### SteelNavigateTool

Programmatic page navigation and interaction.

```python
from langchain_steel import SteelNavigateTool

nav_tool = SteelNavigateTool()

result = nav_tool.run({
    "url": "https://example.com/search",
    "actions": [
        {"type": "fill_form", "selector": "input[name='q']", "value": "artificial intelligence"},
        {"type": "click", "selector": "button[type='submit']"},
        {"type": "wait_for", "selector": ".search-results"},
        {"type": "scroll", "direction": "down", "pixels": 500}
    ]
})
```

### SteelFormTool  

Specialized form filling and submission.

```python
from langchain_steel import SteelFormTool

form_tool = SteelFormTool()

result = form_tool.run({
    "url": "https://forms.example.com/contact",
    "form_data": {
        "name": "John Doe",
        "email": "john@example.com",
        "subject": "Product Inquiry",
        "message": "I'm interested in your enterprise solutions."
    },
    "submit": True,
    "wait_for_confirmation": True
})
```

### SteelInteractionTool

Low-level browser interactions (clicks, typing, scrolling).

```python
from langchain_steel import SteelInteractionTool

interaction_tool = SteelInteractionTool()

result = interaction_tool.run({
    "url": "https://dashboard.example.com",
    "interactions": [
        {"action": "click", "selector": ".menu-toggle"},
        {"action": "type", "selector": "#search-input", "text": "quarterly report"},
        {"action": "key_press", "key": "Enter"},
        {"action": "wait", "milliseconds": 3000},
        {"action": "screenshot"}
    ]
})
```

## Agent Integration

### Single Agent Workflow

```python
from langchain_steel import SteelBrowserAgent
from langchain.agents import initialize_agent, AgentType
from langchain_openai import OpenAI

browser_agent = SteelBrowserAgent()

agent = initialize_agent(
    tools=[browser_agent],
    llm=OpenAI(temperature=0),
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

result = agent.run("""
Go to LinkedIn, search for AI engineers in San Francisco,
and get contact information for the first 5 profiles.
Handle any login requirements automatically.
""")
```

### Multi-Tool Automation

```python
from langchain_steel import (
    SteelBrowserAgent, 
    SteelNavigateTool, 
    SteelFormTool,
    SteelInteractionTool
)

tools = [
    SteelBrowserAgent(name="browser_automator"),
    SteelNavigateTool(name="navigator"), 
    SteelFormTool(name="form_filler"),
    SteelInteractionTool(name="interactor")
]

agent = initialize_agent(
    tools=tools,
    llm=OpenAI(temperature=0),
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION
)

# Complex e-commerce workflow
result = agent.run("""
1. Navigate to the online store
2. Search for wireless headphones under $200
3. Filter by customer rating > 4 stars
4. Add the top-rated item to cart
5. Fill in shipping information
6. Capture order summary before checkout
""")
```

## Advanced Use Cases

### E-commerce Automation

```python
class EcommerceBot:
    def __init__(self):
        self.browser_agent = SteelBrowserAgent()
        self.form_tool = SteelFormTool()
        self.nav_tool = SteelNavigateTool()
    
    def monitor_product_price(self, product_url: str, target_price: float):
        """Monitor product and purchase if price drops below target."""
        
        task = f"""
        1. Go to {product_url}
        2. Extract current price and availability
        3. If price <= ${target_price} and in stock:
           - Add to cart
           - Proceed to checkout
           - Stop before payment confirmation
        4. Return price monitoring report
        """
        
        result = self.browser_agent.run(task)
        return result
    
    def compare_products(self, search_term: str, max_price: float):
        """Compare products across multiple retailers."""
        
        retailers = [
            "https://amazon.com",
            "https://bestbuy.com", 
            "https://target.com"
        ]
        
        comparisons = []
        
        for retailer in retailers:
            task = f"""
            1. Go to {retailer}
            2. Search for '{search_term}'
            3. Filter by price under ${max_price}
            4. Get top 3 results with:
               - Product name and price
               - Customer rating
               - Availability status
            5. Return structured product data
            """
            
            result = self.browser_agent.run(task)
            comparisons.append({
                "retailer": retailer,
                "products": result
            })
        
        return comparisons

# Usage
bot = EcommerceBot()
comparison = bot.compare_products("wireless mouse", 50.0)
```

### Social Media Automation

```python
def automate_social_research(topic: str, platforms: list):
    """Research topic across multiple social platforms."""
    
    browser_agent = SteelBrowserAgent()
    results = {}
    
    for platform in platforms:
        if platform == "twitter":
            task = f"""
            1. Go to twitter.com/search
            2. Search for '{topic}' 
            3. Filter by 'Latest' tweets
            4. Collect first 20 tweets with:
               - Tweet content
               - Author handle
               - Engagement metrics
               - Timestamp
            5. Return as structured data
            """
            
        elif platform == "reddit":
            task = f"""
            1. Go to reddit.com/search
            2. Search for '{topic}'
            3. Sort by 'Hot' posts
            4. Get top 10 posts with:
               - Title and content
               - Upvotes and comments count
               - Subreddit name
            5. Return structured post data
            """
        
        elif platform == "linkedin":
            task = f"""
            1. Go to linkedin.com
            2. Search for '{topic}' in posts
            3. Get top 15 professional posts with:
               - Post content
               - Author name and title
               - Company information
               - Engagement metrics
            4. Return structured data
            """
        
        results[platform] = browser_agent.run(task)
    
    return results

# Research AI trends across platforms
research = automate_social_research(
    "artificial intelligence trends 2024",
    ["twitter", "reddit", "linkedin"]
)
```

### Lead Generation Automation

```python
class LeadGenerationBot:
    def __init__(self):
        self.browser_agent = SteelBrowserAgent()
        self.form_tool = SteelFormTool()
    
    def find_company_contacts(self, company_name: str, role: str):
        """Find contact information for specific roles at companies."""
        
        # Search on LinkedIn
        linkedin_task = f"""
        1. Go to LinkedIn
        2. Use advanced search to find people at '{company_name}'
        3. Filter by role containing '{role}'
        4. Extract from first 10 results:
           - Full name and title
           - Company department
           - Location
           - Profile URL
           - Mutual connections count
        5. Return structured contact data
        """
        
        linkedin_results = self.browser_agent.run(linkedin_task)
        
        # Verify on company website
        company_task = f"""
        1. Search Google for '{company_name} team' OR '{company_name} about us'
        2. Visit company website team/about pages
        3. Cross-reference names from LinkedIn results
        4. Extract additional contact information:
           - Official email patterns
           - Direct phone numbers
           - Team structure
        5. Return verified contact details
        """
        
        company_results = self.browser_agent.run(company_task)
        
        # Combine and deduplicate results
        return {
            "linkedin_data": linkedin_results,
            "company_data": company_results,
            "combined_leads": self._merge_contact_data(linkedin_results, company_results)
        }
    
    def _merge_contact_data(self, linkedin_data, company_data):
        """Merge and deduplicate contact information."""
        # Implementation for combining data sources
        pass

# Generate leads for AI companies
bot = LeadGenerationBot()
contacts = bot.find_company_contacts("OpenAI", "Machine Learning Engineer")
```

## Session Management

### Persistent Sessions

```python
from langchain_steel import SteelConfig, SteelBrowserAgent

# Configure session persistence
config = SteelConfig(
    api_key="your-key",
    session_timeout=1800,  # 30 minutes
    use_proxy=True,
    stealth_mode=True
)

agent = SteelBrowserAgent(config=config)

# Maintain session across multiple tasks
session_id = None

# Task 1: Login
login_result = agent.run(
    task="Login to dashboard.example.com with saved credentials",
    session_id=session_id
)
session_id = login_result.get("session_id")

# Task 2: Navigate and extract data (reuse session)
data_result = agent.run(
    task="Navigate to reports section and download latest analytics",
    session_id=session_id
)

# Task 3: Update settings (same session)
update_result = agent.run(
    task="Go to settings and update notification preferences",
    session_id=session_id
)
```

### Authentication Workflows

```python
def handle_oauth_flow(service: str, redirect_uri: str):
    """Handle OAuth authentication flow."""
    
    agent = SteelBrowserAgent()
    
    oauth_task = f"""
    1. Navigate to {service} OAuth authorization page
    2. Click 'Authorize Application' button
    3. Handle any 2FA prompts if they appear
    4. Wait for redirect to {redirect_uri}
    5. Extract authorization code from redirect URL
    6. Return the authorization code and session cookies
    """
    
    result = agent.run(oauth_task)
    return result

# Handle GitHub OAuth
github_auth = handle_oauth_flow(
    "https://github.com/login/oauth/authorize?client_id=your_client_id",
    "https://yourapp.com/auth/callback"
)
```

## Performance & Configuration

### Advanced Configuration

```python
from langchain_steel import SteelConfig, ProxyConfig

config = SteelConfig(
    api_key="your-key",
    session_timeout=900,     # 15 minutes
    api_timeout=120000,      # 2 minutes
    use_proxy=True,
    solve_captcha=True,
    stealth_mode=True,
    max_retries=3,
    
    # Proxy configuration
    proxy_config=ProxyConfig(
        enabled=True,
        rotate=True,
        country="US",
        sticky_session=True
    ),
    
    # Browser options
    session_options={
        "viewport_width": 1920,
        "viewport_height": 1080,
        "user_agent": "Mozilla/5.0 (compatible; SteelBot/1.0)",
        "javascript_enabled": True,
        "images_enabled": False  # Faster loading
    }
)

agent = SteelBrowserAgent(config=config)
```

### Error Recovery

```python
def robust_automation(task: str, max_retries: int = 3):
    """Automation with error recovery and fallbacks."""
    
    agent = SteelBrowserAgent()
    
    for attempt in range(max_retries):
        try:
            # Primary approach
            result = agent.run(task)
            return result
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            
            if "captcha" in str(e).lower():
                # Enable CAPTCHA solving for retry
                config = SteelConfig(solve_captcha=True, stealth_mode=True)
                agent = SteelBrowserAgent(config=config)
                
            elif "timeout" in str(e).lower():
                # Increase timeout for retry
                config = SteelConfig(api_timeout=180000)  # 3 minutes
                agent = SteelBrowserAgent(config=config)
                
            elif attempt == max_retries - 1:
                # Final attempt with simplified task
                simplified_task = f"Navigate to the main page and extract basic information. Original task was: {task}"
                return agent.run(simplified_task)
    
    return None

# Usage
result = robust_automation("""
Go to complex-site.com, login with credentials,
navigate through multi-step process, and extract final data
""")
```

### Monitoring and Debugging

```python
import logging
from langchain_steel.utils.errors import SteelError

# Enable detailed logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def monitored_automation(task: str):
    """Browser automation with comprehensive monitoring."""
    
    config = SteelConfig(
        api_key="your-key",
        enable_logging=True
    )
    
    agent = SteelBrowserAgent(config=config)
    
    try:
        start_time = time.time()
        
        # Add monitoring wrapper to task
        monitored_task = f"""
        {task}
        
        After completing each major step, provide status update including:
        - Current page URL
        - Step completion status  
        - Any errors encountered
        - Estimated time remaining
        """
        
        result = agent.run(monitored_task)
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"Task completed successfully in {duration:.2f} seconds")
        logger.info(f"Result preview: {str(result)[:200]}...")
        
        return result
        
    except SteelError as e:
        logger.error(f"Steel automation failed: {e.message}")
        if e.details:
            logger.error(f"Error details: {e.details}")
        
        # Take screenshot for debugging
        screenshot_task = "Take a screenshot of current page state for debugging"
        try:
            debug_screenshot = agent.run(screenshot_task)
            logger.info("Debug screenshot captured")
        except:
            pass
        
        raise

# Usage with monitoring
result = monitored_automation("""
Navigate to admin panel, generate monthly report,
and email it to stakeholders
""")
```

## API Reference

For detailed API documentation:
- [Steel Python SDK](https://docs.steel.dev/python)  
- [PyPI Package](https://pypi.org/project/langchain-steel/)
- [GitHub Repository](https://github.com/steel-dev/langchain-steel)