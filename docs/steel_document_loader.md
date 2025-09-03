# Steel Document Loader

[Steel.dev](https://steel.dev) is a browser automation platform designed for AI applications. You can use `SteelDocumentLoader` to load web content into LangChain documents with AI-optimized extraction.

## Installation

```bash
pip install langchain-steel
```

Get your API key from [steel.dev](https://steel.dev) and set it:

```python
import os
os.environ["STEEL_API_KEY"] = "your-api-key"
```

## Basic Usage

```python
from langchain_steel import SteelDocumentLoader

# Load single page
loader = SteelDocumentLoader(urls=["https://docs.python.org/3/"])
documents = loader.load()

print(f"Loaded {len(documents)} documents")
print(f"Content: {documents[0].page_content[:200]}...")
```

## Configuration Options

```python
# Multiple URLs with optimizations
loader = SteelDocumentLoader(
    urls=["https://example.com/page1", "https://example.com/page2"],
    format="markdown",     # Better for AI processing (80% fewer tokens)
    session_reuse=True,    # Faster for multiple pages
    extract_images=True,   # Include image metadata
    extract_links=True,    # Include link information
    wait_for_selector=".main-content",  # Wait for specific element
    delay_ms=2000          # Wait before extraction
)

documents = loader.load()
```

## Loading Methods

### Synchronous Loading

```python
# Load all documents at once
documents = loader.load()

# Memory-efficient lazy loading
for document in loader.lazy_load():
    process_document(document)
```

### Asynchronous Loading

```python
import asyncio

# Async loading for better performance
documents = await loader.aload()

# Async lazy loading
async for document in loader.alazy_load():
    await process_document_async(document)
```

## Parameters

- `urls` (Sequence[str]): List of URLs to load
- `format` (str): Output format - "markdown", "html", "text" (default: "markdown")
- `session_reuse` (bool): Reuse browser session for efficiency (default: True)
- `extract_images` (bool): Include image metadata (default: False)
- `extract_links` (bool): Include link information (default: False)
- `wait_for_selector` (str): CSS selector to wait for
- `delay_ms` (int): Delay before content extraction
- `custom_headers` (dict): Custom HTTP headers
- `config` (SteelConfig): Advanced configuration options

## Advanced Configuration

```python
from langchain_steel import SteelConfig

config = SteelConfig(
    api_key="your-key",
    session_timeout=600,    # 10 minutes
    use_proxy=True,
    solve_captcha=True,
    stealth_mode=True,
    default_format="markdown"
)

loader = SteelDocumentLoader(
    urls=["https://complex-site.com"],
    config=config
)
```

## Document Metadata

Each loaded document includes rich metadata:

```python
documents = loader.load()
doc = documents[0]

print(f"Source: {doc.metadata['source']}")
print(f"Title: {doc.metadata.get('title')}")
print(f"Content Type: {doc.metadata.get('content_type')}")
print(f"Load Time: {doc.metadata.get('load_time')}ms")
print(f"Status Code: {doc.metadata.get('status_code')}")
```

## Common Patterns

### RAG Pipeline

```python
from langchain_steel import SteelDocumentLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Load documentation
loader = SteelDocumentLoader(
    urls=["https://docs.example.com/api", "https://docs.example.com/guides"],
    format="markdown",
    session_reuse=True
)
docs = loader.load()

# Split and create vector store
splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
splits = splitter.split_documents(docs)
vectorstore = FAISS.from_documents(splits, OpenAIEmbeddings())

# Query
retriever = vectorstore.as_retriever()
relevant_docs = retriever.get_relevant_documents("How to authenticate?")
```

### Batch Processing

```python
import asyncio
from typing import List

async def process_url_batches(url_batches: List[List[str]]):
    tasks = []
    for batch in url_batches:
        loader = SteelDocumentLoader(urls=batch, session_reuse=True)
        tasks.append(loader.aload())
    
    results = await asyncio.gather(*tasks)
    
    # Flatten results
    all_documents = []
    for batch_docs in results:
        all_documents.extend(batch_docs)
    
    return all_documents

# Process multiple batches concurrently
url_batches = [
    ["https://site1.com/page1", "https://site1.com/page2"],
    ["https://site2.com/page1", "https://site2.com/page2"],
    ["https://site3.com/page1", "https://site3.com/page2"]
]

documents = asyncio.run(process_url_batches(url_batches))
```

## Error Handling

```python
from langchain_steel.utils.errors import SteelError, SteelContentError

try:
    documents = loader.load()
except SteelContentError as e:
    print(f"Content extraction failed for {e.url}: {e.message}")
    # Try with different format
    loader_fallback = SteelDocumentLoader(
        urls=[e.url], 
        format="html"  # Fallback format
    )
    documents = loader_fallback.load()
    
except SteelError as e:
    print(f"Steel API error: {e.message}")
    if e.details:
        print(f"Details: {e.details}")
```

## Performance Tips

### Token Optimization

Steel's markdown format significantly reduces token usage compared to raw HTML:

```python
# Efficient for AI processing
loader = SteelDocumentLoader(
    urls=["https://example.com"],
    format="markdown"  # Optimized for LLMs
)

# Analyze token efficiency
from tiktoken import encoding_for_model
enc = encoding_for_model("gpt-3.5-turbo")

markdown_tokens = len(enc.encode(markdown_content))
print(f"Optimized content uses: {markdown_tokens} tokens")
print(f"Characters per token: {len(markdown_content) / markdown_tokens:.1f}")
```

### Session Reuse

```python
# Automatic session reuse (recommended)
loader = SteelDocumentLoader(
    urls=multiple_urls,
    session_reuse=True  # Default: True
)

# Manual session management for fine control
from langchain_steel.utils.client import SteelClient

client = SteelClient()
with client.session_context() as session:
    for url in urls:
        result = client.scrape(url=url, session=session, format="markdown")
        documents.append(create_document(result, url))
```

## API Reference

For detailed API documentation:
- [Steel Python SDK](https://docs.steel.dev/python)
- [PyPI Package](https://pypi.org/project/langchain-steel/)
- [GitHub Repository](https://github.com/steel-dev/langchain-steel)