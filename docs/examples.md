# Steel LangChain Integration Examples

This document contains practical examples of using Steel with LangChain for various use cases.

## Basic Web Scraping

### Simple Page Scraping

```python
from langchain_steel import SteelScrapeTool

tool = SteelScrapeTool()

# Get content from a news site
content = tool.run("https://news.ycombinator.com")
print(content)

# With specific parameters
content = tool.run({
    "url": "https://example.com/article",
    "format": "markdown",
    "wait_for_selector": ".article-content"
})
```

### Batch Document Loading

```python
from langchain_steel import SteelDocumentLoader

# Load multiple documentation pages
urls = [
    "https://docs.python.org/3/library/os.html",
    "https://docs.python.org/3/library/sys.html",
    "https://docs.python.org/3/library/json.html"
]

loader = SteelDocumentLoader(urls=urls, format="markdown")
documents = loader.load()

print(f"Loaded {len(documents)} documents")
for doc in documents[:3]:  # Show first 3
    print(f"Source: {doc.metadata['source']}")
    print(f"Title: {doc.metadata.get('title', 'N/A')}")
    print(f"Length: {len(doc.page_content)} chars\n")
```

## RAG (Retrieval Augmented Generation)

### Documentation Q&A System

```python
from langchain_steel import SteelDocumentLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain.chains import RetrievalQA

# Load documentation
loader = SteelDocumentLoader(
    urls=[
        "https://docs.langchain.com/docs/get_started/introduction",
        "https://docs.langchain.com/docs/modules/model_io",
        "https://docs.langchain.com/docs/modules/data_connection"
    ],
    format="markdown",
    session_reuse=True
)

documents = loader.load()

# Split documents
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
texts = text_splitter.split_documents(documents)

# Create vector store
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(texts, embeddings)

# Create QA chain
qa = RetrievalQA.from_chain_type(
    llm=OpenAI(temperature=0),
    chain_type="stuff",
    retriever=vectorstore.as_retriever()
)

# Ask questions
answer = qa.run("How do I create a custom tool in LangChain?")
print(answer)
```

### Multi-Source Knowledge Base

```python
import asyncio
from langchain_steel import SteelDocumentLoader

async def build_knowledge_base():
    # Different documentation sources
    source_batches = [
        ["https://fastapi.tiangolo.com/", "https://fastapi.tiangolo.com/tutorial/"],
        ["https://docs.pydantic.dev/latest/", "https://docs.pydantic.dev/latest/usage/"],
        ["https://docs.python.org/3/tutorial/", "https://docs.python.org/3/library/"]
    ]
    
    # Load all sources concurrently
    loaders = [
        SteelDocumentLoader(urls=batch, format="markdown")
        for batch in source_batches
    ]
    
    results = await asyncio.gather(*[loader.aload() for loader in loaders])
    
    # Flatten results
    all_documents = []
    for doc_batch in results:
        all_documents.extend(doc_batch)
    
    return all_documents

# Usage
documents = asyncio.run(build_knowledge_base())
print(f"Loaded {len(documents)} total documents")
```

## Agent Workflows

### Research Agent

```python
from langchain_steel import SteelScrapeTool, SteelExtractTool
from langchain.agents import initialize_agent, AgentType
from langchain_openai import OpenAI

tools = [
    SteelScrapeTool(name="web_scraper"),
    SteelExtractTool(name="data_extractor")
]

agent = initialize_agent(
    tools=tools,
    llm=OpenAI(temperature=0),
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# Research a company
research_query = """
Research the company at https://example-company.com:
1. Get their main product information
2. Find their pricing details  
3. Extract key team members
4. Summarize their business model
"""

result = agent.run(research_query)
print(result)
```

### Competitive Analysis Agent

```python
from langchain_steel import SteelScrapeTool
from langchain.agents import initialize_agent
from pydantic import BaseModel, Field
from typing import List

class CompetitorInfo(BaseModel):
    company_name: str = Field(description="Company name")
    pricing_tiers: List[str] = Field(description="Available pricing plans")
    key_features: List[str] = Field(description="Main product features")
    target_market: str = Field(description="Target customer segment")

def analyze_competitors():
    tool = SteelScrapeTool()
    
    competitors = [
        "https://competitor1.com/pricing",
        "https://competitor2.com/features",
        "https://competitor3.com/about"
    ]
    
    analysis = []
    for url in competitors:
        content = tool.run({
            "url": url,
            "format": "markdown",
            "extract_links": True
        })
        
        # Process content for competitive intelligence
        analysis.append({
            "url": url,
            "content": content,
            "analysis_date": "2024-01-15"
        })
    
    return analysis

# Run analysis
competitive_data = analyze_competitors()
```

## Structured Data Extraction

### E-commerce Product Scraping

```python
from langchain_steel import SteelExtractTool
from pydantic import BaseModel, Field
from typing import List, Optional

class Product(BaseModel):
    name: str = Field(description="Product name")
    price: str = Field(description="Current price")
    original_price: Optional[str] = Field(description="Original price if on sale")
    rating: Optional[float] = Field(description="Average customer rating")
    reviews_count: Optional[int] = Field(description="Number of reviews")
    availability: str = Field(description="Stock status")

class ProductCatalog(BaseModel):
    products: List[Product] = Field(description="List of products on the page")
    page_info: dict = Field(description="Page metadata")

# Extract product data
extractor = SteelExtractTool()

result = extractor.run({
    "url": "https://store.example.com/electronics/headphones",
    "schema": ProductCatalog.model_json_schema(),
    "instructions": "Extract all products with their pricing and rating information"
})

print(f"Found {len(result['products'])} products")
```

### Job Listings Extraction

```python
class JobListing(BaseModel):
    title: str = Field(description="Job title")
    company: str = Field(description="Company name")
    location: str = Field(description="Job location")
    salary_range: Optional[str] = Field(description="Salary information")
    job_type: str = Field(description="Full-time, part-time, contract, etc.")
    requirements: List[str] = Field(description="Key job requirements")
    posted_date: Optional[str] = Field(description="When the job was posted")

class JobBoard(BaseModel):
    jobs: List[JobListing] = Field(description="Job listings on the page")

# Extract job data
result = extractor.run({
    "url": "https://jobs.example.com/search?q=python+developer",
    "schema": JobBoard.model_json_schema(),
    "instructions": "Extract all job listings with complete information"
})
```

## Advanced Automation

### Multi-step Browser Automation

```python
from langchain_steel import SteelBrowserAgent

agent = SteelBrowserAgent()

# Complex GitHub research workflow
github_task = """
1. Navigate to GitHub.com
2. Search for repositories with 'langchain' AND 'agents'
3. Filter results to show repositories with >100 stars
4. Sort by 'Most stars'
5. For the top 5 repositories, collect:
   - Repository name and owner
   - Star count and fork count
   - Primary programming language
   - Latest release tag (if available)
   - Brief description
6. Return as structured JSON data
"""

result = agent.run(github_task)
print(result)
```

### E-commerce Monitoring

```python
def monitor_product_prices():
    agent = SteelBrowserAgent()
    
    monitoring_task = """
    1. Go to the product page: https://store.example.com/product/12345
    2. Check if the product is in stock
    3. Get the current price
    4. Check for any active promotions or discounts
    5. Capture a screenshot of the product page
    6. Return pricing and availability data
    """
    
    result = agent.run(monitoring_task)
    return result

# Set up periodic monitoring
import schedule
import time

schedule.every(1).hours.do(monitor_product_prices)

# Run scheduler (in production, use proper task queue)
while True:
    schedule.run_pending()
    time.sleep(60)
```

## Performance Optimization

### Efficient Session Management

```python
from langchain_steel.utils.client import SteelClient

# Manual session management for multiple operations
client = SteelClient()

urls_to_scrape = [
    "https://site1.com/page1",
    "https://site1.com/page2", 
    "https://site1.com/page3"
]

# Use single session for related pages
with client.session_context() as session:
    results = []
    for url in urls_to_scrape:
        result = client.scrape(
            url=url,
            session=session,
            format="markdown"
        )
        results.append(result)

print(f"Scraped {len(results)} pages using one session")
```

### Async Batch Processing

```python
import asyncio
from langchain_steel import SteelDocumentLoader

async def process_large_dataset():
    # Break large URL list into batches
    all_urls = [f"https://docs.example.com/page{i}" for i in range(100)]
    batch_size = 10
    
    batches = [
        all_urls[i:i + batch_size] 
        for i in range(0, len(all_urls), batch_size)
    ]
    
    # Process batches concurrently
    tasks = []
    for batch in batches:
        loader = SteelDocumentLoader(urls=batch, session_reuse=True)
        tasks.append(loader.aload())
    
    results = await asyncio.gather(*tasks)
    
    # Flatten results
    all_documents = []
    for batch_docs in results:
        all_documents.extend(batch_docs)
    
    return all_documents

# Run async processing
documents = asyncio.run(process_large_dataset())
print(f"Processed {len(documents)} documents")
```

## Error Handling and Resilience

### Robust Scraping with Fallbacks

```python
from langchain_steel import SteelScrapeTool
from langchain_steel.utils.errors import SteelError, SteelContentError
import time
import random

def robust_scrape(url, max_retries=3):
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
            print(f"Content error on attempt {attempt + 1}: {e.message}")
            if attempt == max_retries - 1:
                # Final attempt with different strategy
                return tool.run({
                    "url": url,
                    "format": "html",  # Fallback to HTML
                    "delay_ms": 5000   # Wait longer
                })
            
        except SteelError as e:
            print(f"Steel API error on attempt {attempt + 1}: {e.message}")
            if attempt < max_retries - 1:
                # Exponential backoff
                sleep_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(sleep_time)
            else:
                raise
    
    return None

# Usage
result = robust_scrape("https://difficult-site.com")
if result:
    print("Successfully scraped content")
else:
    print("Failed to scrape after all retries")
```

### Monitoring and Logging

```python
import logging
from langchain_steel import SteelConfig, SteelDocumentLoader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enable Steel logging
config = SteelConfig(
    api_key="your-key",
    enable_logging=True
)

def monitored_loading(urls):
    loader = SteelDocumentLoader(urls=urls, config=config)
    
    try:
        start_time = time.time()
        documents = loader.load()
        end_time = time.time()
        
        logger.info(f"Successfully loaded {len(documents)} documents in {end_time - start_time:.2f}s")
        
        # Log document statistics
        total_chars = sum(len(doc.page_content) for doc in documents)
        logger.info(f"Total content: {total_chars} characters")
        
        return documents
        
    except Exception as e:
        logger.error(f"Loading failed: {str(e)}")
        return []

# Usage
urls = ["https://example.com/page1", "https://example.com/page2"]
docs = monitored_loading(urls)
```