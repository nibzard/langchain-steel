# Steel

[Steel.dev](https://steel.dev) is a browser automation platform designed for AI applications. Steel provides web scraping and automation capabilities with AI-optimized content extraction that reduces token usage by up to 80%.

## Overview

Steel offers three integration patterns with LangChain:

- **Document Loaders**: Load web content into LangChain documents  
- **Tools**: Individual scraping and automation tasks for agents
- **Browser Agents**: Multi-step browser automation workflows

## Installation

```bash
pip install langchain-steel
```

Get your API key from [steel.dev](https://steel.dev) and set it:

```python
import os
os.environ["STEEL_API_KEY"] = "your-api-key"
```

## Document Loaders

### SteelDocumentLoader

Loads web content with AI-optimized extraction formats.

```python
from langchain_steel import SteelDocumentLoader

# Basic usage
loader = SteelDocumentLoader(urls=["https://docs.python.org/3/"])
documents = loader.load()

# Multiple URLs with configuration
loader = SteelDocumentLoader(
    urls=["https://example.com/page1", "https://example.com/page2"],
    format="markdown",  # Better for AI processing
    session_reuse=True  # Faster for multiple pages
)
documents = loader.load()

print(f"Loaded {len(documents)} documents")
for doc in documents:
    print(f"Title: {doc.metadata.get('title')}")
    print(f"Content: {len(doc.page_content)} characters")
```

### Async loading

```python
# For better performance with many URLs
documents = await loader.aload()

# Memory-efficient for large datasets
for document in loader.lazy_load():
    process_document(document)
```

### Configuration options

```python
loader = SteelDocumentLoader(
    urls=["https://complex-site.com"],
    wait_for_selector=".main-content",  # Wait for specific element
    delay_ms=2000,  # Wait before extraction
    extract_images=True,
    extract_links=True,
    custom_headers={"User-Agent": "MyBot/1.0"}
)
```

## Tools

### SteelScrapeTool

Extracts content from single pages.

```python
from langchain_steel import SteelScrapeTool
from langchain.agents import initialize_agent, AgentType
from langchain_openai import OpenAI

tool = SteelScrapeTool()

# Direct usage
result = tool.run("https://news.ycombinator.com")
print(result)

# With parameters
result = tool.run({
    "url": "https://example.com",
    "format": "markdown",
    "wait_for_selector": ".content"
})
```

### Agent integration

```python
agent = initialize_agent(
    tools=[SteelScrapeTool()],
    llm=OpenAI(temperature=0),
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION
)

result = agent.run("Get the latest news from https://example.com and summarize")
```

### SteelExtractTool

Extracts structured data using schemas.

```python
from langchain_steel import SteelExtractTool
from pydantic import BaseModel, Field
from typing import List

class Product(BaseModel):
    name: str = Field(description="Product name")
    price: str = Field(description="Product price")
    rating: float = Field(description="Average rating")

class ProductList(BaseModel):
    products: List[Product]

tool = SteelExtractTool()
result = tool.run({
    "url": "https://store.example.com",
    "schema": ProductList.model_json_schema(),
    "instructions": "Extract all products with their details"
})
```

### SteelScreenshotTool

Captures page screenshots.

```python
from langchain_steel import SteelScreenshotTool

tool = SteelScreenshotTool()
result = tool.run({
    "url": "https://example.com",
    "viewport_size": {"width": 1280, "height": 720},
    "wait_for_selector": ".page-loaded"
})

# Returns base64 encoded image and metadata
```

## Browser Agents

### SteelBrowserAgent

Handles multi-step automation tasks.

```python
from langchain_steel import SteelBrowserAgent

agent = SteelBrowserAgent()

# Complex workflow
result = agent.run("""
1. Go to GitHub
2. Search for 'langchain' repositories  
3. Get the top 3 results with star counts
4. Return as structured data
""")

# E-commerce example
result = agent.run("""
Search for 'wireless headphones' on the site,
filter by price $50-200,
get first 5 products with prices and ratings
""")
```

## Configuration

### Global configuration

```python
from langchain_steel import SteelConfig

config = SteelConfig(
    api_key="your-key",
    session_timeout=300,  # seconds
    use_proxy=True,
    solve_captcha=True,
    default_format="markdown"
)

# Use with any component
loader = SteelDocumentLoader(urls=["..."], config=config)
tool = SteelScrapeTool(config=config)
```

### Environment variables

```bash
export STEEL_API_KEY="your-key"
export STEEL_USE_PROXY="true"
export STEEL_SOLVE_CAPTCHA="true"
export STEEL_SESSION_TIMEOUT="300"
```

## Performance Tips

### Token optimization

Use markdown format for AI processing:

```python
# More efficient for LLM consumption
loader = SteelDocumentLoader(
    urls=["https://example.com"],
    format="markdown"  # ~80% fewer tokens than HTML
)
```

### Session reuse

Reuse browser sessions for multiple requests:

```python
# Automatic session reuse
loader = SteelDocumentLoader(
    urls=multiple_urls,
    session_reuse=True
)

# Manual session management
from langchain_steel.utils.client import SteelClient

client = SteelClient()
with client.session_context() as session:
    for url in urls:
        result = client.scrape(url=url, session=session)
```

### Error handling

```python
from langchain_steel.utils.errors import SteelError, SteelContentError

try:
    documents = loader.load()
except SteelContentError as e:
    print(f"Content extraction failed for {e.url}: {e.message}")
except SteelError as e:
    print(f"Steel API error: {e.message}")
```

## Common Patterns

### RAG pipeline

```python
from langchain_steel import SteelDocumentLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Load documentation
loader = SteelDocumentLoader(
    urls=["https://docs.example.com/api", "https://docs.example.com/guides"],
    format="markdown"
)
docs = loader.load()

# Create vector store
splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
splits = splitter.split_documents(docs)
vectorstore = FAISS.from_documents(splits, OpenAIEmbeddings())

# Query
retriever = vectorstore.as_retriever()
relevant_docs = retriever.get_relevant_documents("How to authenticate?")
```

### Multi-tool agent

```python
from langchain_steel import SteelScrapeTool, SteelExtractTool
from langchain.agents import initialize_agent

tools = [
    SteelScrapeTool(name="scraper"),
    SteelExtractTool(name="extractor")
]

agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION)

result = agent.run("""
Scrape https://competitor.com/pricing and extract pricing tiers 
with features as structured data
""")
```

### Async processing

```python
import asyncio
from langchain_steel import SteelDocumentLoader

async def process_urls(urls):
    loader = SteelDocumentLoader(urls=urls)
    documents = await loader.aload()
    return documents

# Process multiple URL sets concurrently
url_batches = [batch1, batch2, batch3]
tasks = [process_urls(batch) for batch in url_batches]
results = await asyncio.gather(*tasks)
```

## API Reference

- **SteelDocumentLoader**: Load web content into documents
- **SteelScrapeTool**: Single page content extraction  
- **SteelExtractTool**: Structured data extraction
- **SteelScreenshotTool**: Visual content capture
- **SteelBrowserAgent**: Multi-step automation
- **SteelConfig**: Configuration management

For detailed API docs, see:
- [Steel Python SDK](https://docs.steel.dev/python)
- [PyPI Package](https://pypi.org/project/langchain-steel/)
- [GitHub Repository](https://github.com/steel-dev/langchain-steel)