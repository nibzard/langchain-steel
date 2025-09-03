# Steel Web Scraping Tools

[Steel.dev](https://steel.dev) provides specialized web scraping tools for LangChain agents. These tools enable AI agents to extract content and structured data from web pages with AI-optimized output formats.

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

### SteelScrapeTool

Extracts content from individual web pages.

```python
from langchain_steel import SteelScrapeTool

tool = SteelScrapeTool()

# Basic usage
content = tool.run("https://news.ycombinator.com")
print(content)

# With parameters
result = tool.run({
    "url": "https://example.com/article",
    "format": "markdown",
    "wait_for_selector": ".article-content",
    "delay_ms": 2000
})
```

### SteelExtractTool

Extracts structured data using Pydantic schemas.

```python
from langchain_steel import SteelExtractTool
from pydantic import BaseModel, Field
from typing import List

class Product(BaseModel):
    name: str = Field(description="Product name")
    price: str = Field(description="Product price") 
    rating: float = Field(description="Average rating")
    availability: str = Field(description="Stock status")

class ProductCatalog(BaseModel):
    products: List[Product] = Field(description="List of products")

tool = SteelExtractTool()
result = tool.run({
    "url": "https://store.example.com/category/electronics",
    "schema": ProductCatalog.model_json_schema(),
    "instructions": "Extract all products with their pricing and availability"
})

print(f"Found {len(result['products'])} products")
```

### SteelCrawlTool

Crawls multiple pages with depth control and filtering.

```python
from langchain_steel import SteelCrawlTool

tool = SteelCrawlTool()

result = tool.run({
    "start_url": "https://docs.example.com",
    "max_pages": 25,
    "max_depth": 3,
    "include_patterns": ["*/docs/*", "*/api/*"],
    "exclude_patterns": ["*/blog/*", "*/news/*"],
    "format": "markdown"
})

print(f"Crawled {len(result['pages'])} pages")
```

### SteelScreenshotTool

Captures visual content and metadata.

```python
from langchain_steel import SteelScreenshotTool

tool = SteelScreenshotTool()

result = tool.run({
    "url": "https://dashboard.example.com",
    "viewport_size": {"width": 1920, "height": 1080},
    "full_page": True,
    "wait_for_selector": ".dashboard-loaded",
    "element_selector": ".main-chart"  # Focus on specific element
})

# Returns base64 encoded image and metadata
print(f"Screenshot size: {result['metadata']['file_size']} bytes")
```

## Agent Integration

### Single Tool Usage

```python
from langchain_steel import SteelScrapeTool
from langchain.agents import initialize_agent, AgentType
from langchain_openai import OpenAI

tool = SteelScrapeTool()

agent = initialize_agent(
    tools=[tool],
    llm=OpenAI(temperature=0),
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

result = agent.run("Scrape https://example.com and summarize the main content")
```

### Multi-Tool Agent

```python
from langchain_steel import SteelScrapeTool, SteelExtractTool, SteelScreenshotTool

tools = [
    SteelScrapeTool(name="web_scraper"),
    SteelExtractTool(name="data_extractor"),
    SteelScreenshotTool(name="screenshot_taker")
]

agent = initialize_agent(
    tools=tools,
    llm=OpenAI(temperature=0),
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION
)

# Complex analysis task
result = agent.run("""
Analyze competitor pricing at https://competitor.com/pricing:
1. First scrape the page content
2. Extract structured pricing data with features
3. Take a screenshot for visual reference
4. Provide competitive analysis summary
""")
```

## Tool Parameters

### SteelScrapeTool Parameters

```python
{
    "url": str,                    # Required: URL to scrape
    "format": str,                 # "markdown", "html", "text" (default: "markdown")
    "wait_for_selector": str,      # CSS selector to wait for
    "delay_ms": int,               # Delay before scraping in milliseconds  
    "screenshot": bool,            # Capture screenshot (default: False)
    "extract_images": bool,        # Include image metadata (default: False)
    "extract_links": bool,         # Include link information (default: False)
    "custom_headers": dict         # Custom HTTP headers
}
```

### SteelExtractTool Parameters

```python
{
    "url": str,                    # Required: URL to extract from
    "schema": dict,                # Required: Pydantic schema as JSON
    "instructions": str,           # Extraction instructions for AI
    "format": str,                 # Input format preference
    "wait_for_selector": str,      # Wait for element before extraction
    "extract_from_content": str    # Pre-loaded content instead of URL
}
```

### SteelCrawlTool Parameters

```python
{
    "start_url": str,              # Required: Starting URL
    "max_pages": int,              # Maximum pages to crawl (default: 10)
    "max_depth": int,              # Maximum crawl depth (default: 2)
    "include_patterns": list,      # URL patterns to include
    "exclude_patterns": list,      # URL patterns to exclude  
    "format": str,                 # Output format for each page
    "respect_robots_txt": bool,    # Follow robots.txt (default: True)
    "delay_between_requests": int  # Delay between requests in ms
}
```

## Real-World Examples

### E-commerce Product Research

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class ProductDetails(BaseModel):
    name: str = Field(description="Product name")
    current_price: str = Field(description="Current selling price")
    original_price: Optional[str] = Field(description="Original price if on sale")
    discount_percentage: Optional[str] = Field(description="Discount percentage")
    rating: Optional[float] = Field(description="Average customer rating")
    review_count: Optional[int] = Field(description="Number of reviews")
    availability: str = Field(description="In stock, out of stock, limited")
    key_features: List[str] = Field(description="Main product features")

class CompetitiveAnalysis(BaseModel):
    products: List[ProductDetails]
    page_title: str = Field(description="Page title")
    total_products_found: int = Field(description="Number of products on page")

def analyze_competitor_products():
    extract_tool = SteelExtractTool()
    
    result = extract_tool.run({
        "url": "https://competitor.com/category/laptops?sort=popularity",
        "schema": CompetitiveAnalysis.model_json_schema(),
        "instructions": """
        Extract all laptop products visible on this page. 
        Focus on pricing, ratings, and key specifications.
        Include sale prices and original prices where available.
        """
    })
    
    return result

# Usage
analysis = analyze_competitor_products()
print(f"Found {len(analysis['products'])} competitor products")
```

### Content Research Pipeline

```python
def research_topic(topic: str, sources: List[str]):
    scrape_tool = SteelScrapeTool()
    crawl_tool = SteelCrawlTool()
    
    research_data = []
    
    for source_url in sources:
        # First, get the main page content
        main_content = scrape_tool.run({
            "url": source_url,
            "format": "markdown",
            "extract_links": True
        })
        
        # Then crawl related pages
        crawl_result = crawl_tool.run({
            "start_url": source_url,
            "max_pages": 10,
            "max_depth": 2,
            "include_patterns": [f"*/{topic.lower()}/*", "*/{topic.lower().replace(' ', '-')}/*"],
            "format": "markdown"
        })
        
        research_data.append({
            "source": source_url,
            "main_content": main_content,
            "related_pages": crawl_result["pages"]
        })
    
    return research_data

# Research AI tools across multiple sources
sources = [
    "https://docs.openai.com",
    "https://docs.anthropic.com", 
    "https://ai.google.dev"
]

research = research_topic("API authentication", sources)
```

### News Monitoring

```python
class NewsArticle(BaseModel):
    headline: str = Field(description="Article headline")
    summary: str = Field(description="Brief article summary")
    publish_date: str = Field(description="Publication date")
    author: Optional[str] = Field(description="Article author")
    category: str = Field(description="News category")
    sentiment: str = Field(description="Overall sentiment: positive, negative, neutral")

class NewsPage(BaseModel):
    articles: List[NewsArticle] = Field(description="List of news articles")
    last_updated: str = Field(description="Page last updated time")

def monitor_industry_news():
    extract_tool = SteelExtractTool()
    screenshot_tool = SteelScreenshotTool()
    
    # Monitor multiple news sources
    sources = [
        "https://techcrunch.com/category/artificial-intelligence/",
        "https://www.theverge.com/ai-artificial-intelligence",
        "https://venturebeat.com/ai/"
    ]
    
    all_articles = []
    
    for source in sources:
        # Extract structured news data
        news_data = extract_tool.run({
            "url": source,
            "schema": NewsPage.model_json_schema(),
            "instructions": "Extract recent AI/ML news articles with sentiment analysis"
        })
        
        # Take screenshot for reference
        screenshot = screenshot_tool.run({
            "url": source,
            "viewport_size": {"width": 1280, "height": 720}
        })
        
        all_articles.extend(news_data["articles"])
    
    return all_articles

# Set up periodic monitoring
articles = monitor_industry_news()
print(f"Found {len(articles)} AI-related articles")
```

## Advanced Configuration

### Custom Steel Configuration

```python
from langchain_steel import SteelConfig, SteelScrapeTool

config = SteelConfig(
    api_key="your-key",
    session_timeout=600,
    use_proxy=True,
    solve_captcha=True,
    stealth_mode=True,
    max_retries=3,
    retry_delay=2.0
)

tool = SteelScrapeTool(config=config)
```

### Session Reuse for Performance

```python
from langchain_steel.utils.client import SteelClient

# Manual session management for related scraping tasks
client = SteelClient()
scrape_tool = SteelScrapeTool()

urls = [
    "https://site.com/page1",
    "https://site.com/page2", 
    "https://site.com/page3"
]

with client.session_context() as session:
    results = []
    for url in urls:
        result = client.scrape(
            url=url,
            session=session,
            format="markdown"
        )
        results.append(result)
```

## Error Handling

```python
from langchain_steel.utils.errors import SteelError, SteelContentError

def robust_scraping(url: str, max_retries: int = 3):
    tool = SteelScrapeTool()
    
    for attempt in range(max_retries):
        try:
            result = tool.run({
                "url": url,
                "format": "markdown",
                "wait_for_selector": ".main-content"
            })
            return result
            
        except SteelContentError as e:
            print(f"Content error attempt {attempt + 1}: {e.message}")
            if attempt == max_retries - 1:
                # Final attempt with different strategy
                return tool.run({
                    "url": url,
                    "format": "html",
                    "delay_ms": 5000
                })
                
        except SteelError as e:
            print(f"API error attempt {attempt + 1}: {e.message}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise

# Usage
content = robust_scraping("https://difficult-site.com")
```

## Performance Optimization

### Token-Efficient Extraction

```python
# Use markdown format for token optimization
result = tool.run({
    "url": "https://long-article.com",
    "format": "markdown",           # Optimized for LLMs
    "wait_for_selector": ".content" # Focus on main content only
})

# Compare with HTML extraction
html_result = tool.run({"url": url, "format": "html"})
markdown_result = tool.run({"url": url, "format": "markdown"})

print(f"Content length: {len(markdown_result)} characters")
print(f"Token count: {len(markdown_result)} tokens (approximate)")
print("Optimized markdown format provides efficient AI processing")
```

### Concurrent Processing

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

def scrape_url(url):
    tool = SteelScrapeTool()
    return tool.run({"url": url, "format": "markdown"})

async def scrape_multiple_urls(urls: List[str]):
    with ThreadPoolExecutor(max_workers=5) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, scrape_url, url)
            for url in urls
        ]
        results = await asyncio.gather(*tasks)
    return results

# Scrape multiple URLs concurrently
urls = ["https://site1.com", "https://site2.com", "https://site3.com"]
results = asyncio.run(scrape_multiple_urls(urls))
```

## API Reference

For detailed API documentation:
- [Steel Python SDK](https://docs.steel.dev/python)
- [PyPI Package](https://pypi.org/project/langchain-steel/)
- [GitHub Repository](https://github.com/steel-dev/langchain-steel)