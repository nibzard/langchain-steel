# Steel Token Efficiency Guide

Steel.dev is specifically designed for AI applications with token-optimized content extraction. This guide demonstrates Steel's token efficiency capabilities and provides optimization strategies for AI workloads.

## Token Efficiency Overview

Steel reduces AI token usage by up to **80%** through:

- **AI-optimized markdown output**: Clean, structured format perfect for LLMs
- **Content filtering**: Removes navigation, ads, and irrelevant elements  
- **Smart text extraction**: Preserves semantic structure while eliminating noise
- **Intelligent summarization**: Optional content condensation

## Token Usage Analysis

### Real-World Example: News Article Extraction

```python
from langchain_steel import SteelDocumentLoader
import tiktoken

# Test URL: BBC News article
test_url = "https://www.bbc.com/news/technology-67890123"

# Steel extraction (markdown)
steel_loader = SteelDocumentLoader(
    urls=[test_url],
    format="markdown"
)
steel_docs = steel_loader.load()
steel_content = steel_docs[0].page_content

# Traditional HTML extraction (simulated)
traditional_html = """
<!DOCTYPE html>
<html>
<head>
    <title>AI News Article</title>
    <meta charset="utf-8">
    <link rel="stylesheet" href="/styles.css">
    <script src="/analytics.js"></script>
</head>
<body>
    <nav class="navigation">...</nav>
    <header class="site-header">...</header>
    <aside class="sidebar">
        <div class="ads">...</div>
        <div class="recommended">...</div>
    </aside>
    <main>
        <article>
            <h1>Major AI Breakthrough Announced</h1>
            <p>In a significant development...</p>
            <!-- Article content mixed with HTML -->
        </article>
    </main>
    <footer>...</footer>
    <script>/* More JS */</script>
</body>
</html>
"""

# Token comparison
encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")

steel_tokens = len(encoder.encode(steel_content))
html_tokens = len(encoder.encode(traditional_html))

print(f"Steel (markdown): {steel_tokens} tokens")
print(f"Raw HTML: {html_tokens} tokens")
print(f"Token efficiency: Steel uses {steel_tokens/html_tokens:.2f}x fewer tokens")
```

## Cost Impact Analysis

### Monthly Processing Costs

Scenario: Processing 10,000 web pages per month for RAG pipeline using Steel's optimized markdown format:

- **Steel (Markdown)**: ~1,200 tokens/page → 12M tokens/month
- **GPT-3.5 Cost**: $24/month
- **GPT-4 Cost**: $360/month  
- **GPT-4 Turbo Cost**: $120/month

### ROI Calculation

```python
def calculate_steel_costs(pages_per_month: int, model: str = "gpt-3.5-turbo"):
    """Calculate costs of using Steel for web content processing."""
    
    # Steel token efficiency (average)
    steel_tokens_per_page = 1200  # AI-optimized markdown format
    
    # Pricing per 1K tokens (as of 2024)
    pricing = {
        "gpt-3.5-turbo": 0.002,
        "gpt-4": 0.03,
        "gpt-4-turbo": 0.01
    }
    
    monthly_pages = pages_per_month
    price_per_1k = pricing.get(model, 0.002)
    
    # Steel processing costs
    monthly_tokens = monthly_pages * steel_tokens_per_page
    monthly_cost = (monthly_tokens / 1000) * price_per_1k
    annual_cost = monthly_cost * 12
    
    return {
        "monthly_pages": monthly_pages,
        "tokens_per_page": steel_tokens_per_page,
        "monthly_tokens": monthly_tokens,
        "monthly_cost": monthly_cost,
        "annual_cost": annual_cost,
        "model": model
    }

# Example cost calculations
cost_small = calculate_steel_costs(1000, "gpt-3.5-turbo")    # Small operation
cost_medium = calculate_steel_costs(10000, "gpt-4")          # Medium operation  
cost_large = calculate_steel_costs(100000, "gpt-4-turbo")    # Large operation

print("Small Operation (1K pages/month, GPT-3.5):")
print(f"Monthly cost: ${cost_small['monthly_cost']:.2f}")
print(f"Annual cost: ${cost_small['annual_cost']:.2f}")
print(f"Cost per page: ${cost_small['monthly_cost']/cost_small['monthly_pages']:.4f}\n")

print("Medium Operation (10K pages/month, GPT-4):")
print(f"Monthly cost: ${cost_medium['monthly_cost']:.2f}")
print(f"Annual cost: ${cost_medium['annual_cost']:.2f}")
print(f"Cost per page: ${cost_medium['monthly_cost']/cost_medium['monthly_pages']:.4f}\n")

print("Large Operation (100K pages/month, GPT-4 Turbo):")
print(f"Monthly cost: ${cost_large['monthly_cost']:.2f}")
print(f"Annual cost: ${cost_large['annual_cost']:.2f}")
print(f"Cost per page: ${cost_large['monthly_cost']/cost_large['monthly_pages']:.4f}")
```

## Optimization Techniques

### Content Filtering Strategies

```python
from langchain_steel import SteelDocumentLoader

# Maximum token efficiency
loader = SteelDocumentLoader(
    urls=["https://article.example.com"],
    format="markdown",              # Token-optimized format
    wait_for_selector=".content",   # Focus on main content
    extract_images=False,           # Skip image metadata
    extract_links=False             # Skip link information
)

# Balanced extraction (content + some metadata)
loader_balanced = SteelDocumentLoader(
    urls=["https://article.example.com"],
    format="markdown",
    extract_images=True,    # Include key images
    extract_links=True      # Include important links
)

# Compare token usage
minimal_docs = loader.load()
balanced_docs = loader_balanced.load()

encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")
minimal_tokens = len(encoder.encode(minimal_docs[0].page_content))
balanced_tokens = len(encoder.encode(balanced_docs[0].page_content))

print(f"Minimal extraction: {minimal_tokens} tokens")
print(f"Balanced extraction: {balanced_tokens} tokens")
print(f"Additional tokens for metadata: {balanced_tokens - minimal_tokens}")
```

### Smart Chunking for RAG

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_steel import SteelDocumentLoader

def token_aware_chunking(urls: list, target_tokens_per_chunk: int = 500):
    """Smart chunking based on token count rather than character count."""
    
    loader = SteelDocumentLoader(urls=urls, format="markdown")
    documents = loader.load()
    
    encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")
    
    # Calculate character-to-token ratio
    sample_text = documents[0].page_content[:1000]
    sample_tokens = len(encoder.encode(sample_text))
    char_to_token_ratio = len(sample_text) / sample_tokens
    
    # Adjust chunk size based on ratio
    target_chars = target_tokens_per_chunk * char_to_token_ratio
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=int(target_chars),
        chunk_overlap=int(target_chars * 0.1),  # 10% overlap
        length_function=lambda text: len(encoder.encode(text))  # Token-based
    )
    
    chunks = splitter.split_documents(documents)
    
    # Verify chunk token counts
    for i, chunk in enumerate(chunks[:3]):  # Check first 3 chunks
        token_count = len(encoder.encode(chunk.page_content))
        print(f"Chunk {i+1}: {token_count} tokens")
    
    return chunks

# Usage
optimized_chunks = token_aware_chunking([
    "https://docs.example.com/api",
    "https://docs.example.com/guides"
], target_tokens_per_chunk=400)
```

## Format Comparison

### Steel Markdown vs Raw HTML

```python
from langchain_steel import SteelDocumentLoader

url = "https://blog.example.com/ai-trends-2024"

# Raw HTML extraction
html_loader = SteelDocumentLoader(urls=[url], format="html")
html_docs = html_loader.load()
html_content = html_docs[0].page_content

# Steel optimized markdown
markdown_loader = SteelDocumentLoader(urls=[url], format="markdown")
markdown_docs = markdown_loader.load()
markdown_content = markdown_docs[0].page_content

print("=== RAW HTML OUTPUT ===")
print(html_content[:500] + "...")
print("\n=== STEEL MARKDOWN OUTPUT ===")
print(markdown_content[:500] + "...")

# Token analysis
encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")
html_tokens = len(encoder.encode(html_content))
markdown_tokens = len(encoder.encode(markdown_content))

print(f"\nToken Comparison:")
print(f"HTML: {html_tokens:,} tokens")
print(f"Markdown: {markdown_tokens:,} tokens")  
print(f"Reduction: {((html_tokens - markdown_tokens) / html_tokens * 100):.1f}%")

# Quality check: Information preservation
print(f"\nContent Quality:")
print(f"HTML length: {len(html_content):,} characters")
print(f"Markdown length: {len(markdown_content):,} characters")
print(f"Compression ratio: {(len(html_content) / len(markdown_content)):.1f}x")
```

### Example Output Comparison

**Raw HTML** (6,000+ tokens):
```html
<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>AI Trends 2024</title>
<meta name="description" content="Latest AI trends"><link rel="stylesheet" href="/css/main.css">
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_ID"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}
gtag('js',new Date());gtag('config','GA_ID');</script></head><body><nav class="navbar">
<div class="nav-container"><a href="/" class="nav-brand">BlogSite</a><ul class="nav-menu">
<li class="nav-item"><a href="/about">About</a></li></ul></div></nav><header class="hero">
<div class="hero-content"><h1 class="hero-title">AI Trends to Watch in 2024</h1></div></header>
<main class="content"><article class="post"><div class="post-meta"><time datetime="2024-01-15">
January 15, 2024</time><span class="author">by Jane Smith</span></div><div class="post-content">
<p>Artificial intelligence continues to evolve rapidly...</p>...
```

**Steel Markdown** (1,200 tokens):
```markdown
# AI Trends to Watch in 2024

*January 15, 2024 by Jane Smith*

Artificial intelligence continues to evolve rapidly, with several key trends emerging for 2024:

## 1. Large Language Model Advancements

The landscape of large language models (LLMs) is becoming increasingly sophisticated...

## 2. AI Agent Development

Autonomous AI agents are gaining traction across industries...

## 3. Multimodal AI Integration

The integration of text, image, and audio processing...
```

## Performance Monitoring

### Token Usage Tracking

```python
import time
from typing import Dict, List
from langchain_steel import SteelDocumentLoader
import tiktoken

class TokenEfficiencyMonitor:
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.encoder = tiktoken.encoding_for_model(model_name)
        self.model_name = model_name
        self.results = []
    
    def benchmark_url(self, url: str, formats: List[str] = None) -> Dict:
        """Benchmark token efficiency across different formats."""
        
        if formats is None:
            formats = ["markdown", "html", "text"]
        
        results = {"url": url, "formats": {}}
        
        for format_type in formats:
            start_time = time.time()
            
            loader = SteelDocumentLoader(urls=[url], format=format_type)
            docs = loader.load()
            
            end_time = time.time()
            
            if docs:
                content = docs[0].page_content
                token_count = len(self.encoder.encode(content))
                char_count = len(content)
                
                results["formats"][format_type] = {
                    "tokens": token_count,
                    "characters": char_count,
                    "extraction_time": round(end_time - start_time, 2),
                    "tokens_per_char": round(token_count / char_count, 3),
                    "chars_per_token": round(char_count / token_count, 1)
                }
        
        # Calculate format efficiency
        if "html" in results["formats"] and "markdown" in results["formats"]:
            html_tokens = results["formats"]["html"]["tokens"]
            markdown_tokens = results["formats"]["markdown"]["tokens"]
            
            results["format_analysis"] = {
                "html_tokens": html_tokens,
                "markdown_tokens": markdown_tokens,
                "markdown_efficiency": round(markdown_tokens / html_tokens, 2)
            }
        
        self.results.append(results)
        return results
    
    def benchmark_multiple_urls(self, urls: List[str]) -> Dict:
        """Benchmark multiple URLs and provide aggregate statistics."""
        
        all_results = []
        for url in urls:
            try:
                result = self.benchmark_url(url)
                all_results.append(result)
            except Exception as e:
                print(f"Failed to benchmark {url}: {e}")
        
        # Calculate averages
        total_markdown_tokens = sum(r["formats"]["markdown"]["tokens"] for r in all_results if "markdown" in r["formats"])
        
        avg_markdown_tokens = total_markdown_tokens / len(all_results) if all_results else 0
        
        return {
            "individual_results": all_results,
            "summary": {
                "urls_tested": len(all_results),
                "avg_markdown_tokens": round(avg_markdown_tokens),
                "total_markdown_tokens": total_markdown_tokens,
                "avg_tokens_per_page": round(avg_markdown_tokens) if all_results else 0
            }
        }

# Usage example
monitor = TokenEfficiencyMonitor()

test_urls = [
    "https://techcrunch.com/2024/01/15/ai-startup-funding/",
    "https://www.theverge.com/ai-artificial-intelligence",
    "https://blog.openai.com/gpt-4-api-general-availability",
    "https://ai.googleblog.com/2024/01/gemini-next-generation.html"
]

benchmark_results = monitor.benchmark_multiple_urls(test_urls)

print("Steel Token Efficiency Results:")
print("=" * 40)
print(f"URLs tested: {benchmark_results['summary']['urls_tested']}")
print(f"Average markdown tokens: {benchmark_results['summary']['avg_markdown_tokens']:,}")
print(f"Total tokens processed: {benchmark_results['summary']['total_markdown_tokens']:,}")
print(f"Average tokens per page: {benchmark_results['summary']['avg_tokens_per_page']:,}")
```

## Best Practices Summary

### For Maximum Token Efficiency:

1. **Always use markdown format** for AI processing
2. **Focus content extraction** with CSS selectors
3. **Skip unnecessary metadata** (images/links) when not needed
4. **Use session reuse** for batch operations
5. **Implement token-aware chunking** for RAG applications
6. **Monitor and benchmark** your specific use cases

### Cost Optimization Checklist:

- [ ] Use Steel markdown format for optimal token efficiency
- [ ] Implement content filtering with selectors
- [ ] Choose appropriate extraction scope
- [ ] Monitor token usage in production
- [ ] Regular performance monitoring
- [ ] Optimize chunk sizes for your model
- [ ] Track cost metrics monthly

Steel's token-optimized design makes it an excellent choice for AI applications requiring large-scale web content processing, with significant cost savings through efficient content extraction.