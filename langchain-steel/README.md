# LangChain Steel Integration

[![PyPI version](https://badge.fury.io/py/langchain-steel.svg)](https://badge.fury.io/py/langchain-steel)
[![Python versions](https://img.shields.io/pypi/pyversions/langchain-steel.svg)](https://pypi.org/project/langchain-steel/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/steel-dev/langchain-steel/workflows/Tests/badge.svg)](https://github.com/steel-dev/langchain-steel/actions)
[![Coverage](https://codecov.io/gh/steel-dev/langchain-steel/branch/main/graph/badge.svg)](https://codecov.io/gh/steel-dev/langchain-steel)

**AI-first browser automation and web scraping for LangChain**

Steel.dev integration for LangChain provides powerful browser automation and web scraping capabilities specifically designed for AI agents. Built on top of [Steel.dev's](https://steel.dev) AI-optimized browser infrastructure, this integration delivers up to 80% token usage reduction compared to traditional web scraping solutions.

## 🚀 Key Features

- **🤖 AI-Optimized**: Built specifically for AI agents with token-efficient content extraction
- **🔧 Multiple Integration Patterns**: Document loaders, tools, and browser agents
- **⚡ High Performance**: Advanced caching, session reuse, and parallel processing
- **🛡️ Enterprise-Ready**: Anti-bot bypass, CAPTCHA solving, and proxy support
- **🌐 Comprehensive**: Support for HTML, Markdown, PDF extraction and screenshots
- **🔄 Session Management**: Persistent sessions with authentication and state management

## 📦 Installation

```bash
pip install langchain-steel
```

### Development Installation

```bash
git clone https://github.com/steel-dev/langchain-steel.git
cd langchain-steel
pip install -e ".[dev]"
```

## 🔑 Quick Start

### 1. Get Your Steel API Key

Sign up at [steel.dev](https://steel.dev) and get your API key.

```bash
export STEEL_API_KEY="your-steel-api-key"
```

### 2. Basic Document Loading

```python
from langchain_steel import SteelDocumentLoader

# Load web content for RAG applications
loader = SteelDocumentLoader(
    urls=["https://example.com", "https://another-site.com"],
    format="markdown"  # AI-optimized format
)

documents = loader.load()
print(f"Loaded {len(documents)} documents")
```

### 3. Web Scraping with Tools

```python
from langchain_steel import SteelScrapeTool
from langchain.agents import initialize_agent, AgentType
from langchain_openai import OpenAI

# Initialize tool
scrape_tool = SteelScrapeTool()

# Create agent with Steel scraping capabilities  
agent = initialize_agent(
    tools=[scrape_tool],
    llm=OpenAI(temperature=0),
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION
)

# Use in conversation
result = agent.run("Scrape the homepage of https://news.ycombinator.com and summarize the top stories")
```

### 4. Complex Browser Automation

```python
from langchain_steel import SteelBrowserAgent

# High-level browser automation
browser_agent = SteelBrowserAgent()

result = browser_agent.run(
    task="Go to GitHub, search for 'langchain', and get details of the top 3 repositories"
)
print(result)
```

## 🔧 Available Components

### Document Loaders

- **`SteelDocumentLoader`**: Batch web content loading with AI optimization

### Tools

- **`SteelScrapeTool`**: Single page content extraction
- **`SteelCrawlTool`**: Multi-page crawling with depth control
- **`SteelExtractTool`**: AI-powered structured data extraction
- **`SteelScreenshotTool`**: Visual content capture

### Agents

- **`SteelBrowserAgent`**: Natural language browser automation

## 📊 Performance Comparison

| Solution | Token Efficiency | Setup Complexity | AI Optimization | Enterprise Features |
|----------|------------------|-------------------|----------------|-------------------|
| **Steel.dev** | ⭐⭐⭐⭐⭐ (80% reduction) | ⭐⭐⭐⭐⭐ Simple | ⭐⭐⭐⭐⭐ Native | ⭐⭐⭐⭐⭐ Full |
| Browserbase | ⭐⭐⭐ Good | ⭐⭐⭐⭐ Easy | ⭐⭐ Limited | ⭐⭐⭐⭐ Good |
| Browserless | ⭐⭐ Basic | ⭐⭐⭐ Moderate | ⭐ None | ⭐⭐ Basic |
| Selenium | ⭐ Poor | ⭐ Complex | ⭐ None | ⭐⭐ Limited |

## 🛠️ Advanced Configuration

```python
from langchain_steel import SteelConfig, SteelDocumentLoader

# Advanced configuration
config = SteelConfig(
    api_key="your-api-key",
    use_proxy=True,
    solve_captcha=True,
    stealth_mode=True,
    session_timeout=300,
    default_format="markdown"
)

loader = SteelDocumentLoader(
    urls=["https://example.com"],
    config=config,
    # Session reuse for efficiency
    reuse_session=True,
    # Custom extraction options
    extract_images=True,
    extract_links=True
)
```

## 📚 Examples

Check out the [examples directory](examples/) for more comprehensive use cases:

- [`basic_scraping.py`](examples/basic_scraping.py) - Simple web scraping
- [`document_loading.py`](examples/document_loading.py) - RAG pipeline integration  
- [`browser_automation.py`](examples/browser_automation.py) - Complex automation
- [`agent_integration.py`](examples/agent_integration.py) - LangChain agent usage

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/steel-dev/langchain-steel.git
cd langchain-steel

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run type checking
mypy langchain_steel

# Format code
black langchain_steel tests examples
isort langchain_steel tests examples
```

## 📖 Documentation

- [API Reference](https://langchain-steel.readthedocs.io)
- [User Guide](docs/user-guide.md)
- [Migration Guide](docs/migration-guide.md) - From other browser automation tools
- [Best Practices](docs/best-practices.md)

## 🆘 Support

- [GitHub Issues](https://github.com/steel-dev/langchain-steel/issues) - Bug reports and feature requests
- [GitHub Discussions](https://github.com/steel-dev/langchain-steel/discussions) - Community support
- [Steel.dev Documentation](https://docs.steel.dev) - Steel platform documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on [Steel.dev](https://steel.dev) - AI-first browser automation platform
- Integrated with [LangChain](https://langchain.com) - Framework for developing with LLMs
- Inspired by the need for token-efficient web automation in AI applications

---

**Made with ❤️ by the Steel.dev team**