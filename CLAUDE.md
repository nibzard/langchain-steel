# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Structure

This repository contains a Steel.dev + LangChain integration implementation with the following structure:

```
steel-research-langchain/
├── langchain-steel/          # Main Python package
│   ├── langchain_steel/      # Core integration code
│   │   ├── tools/            # LangChain tools (scrape, crawl, extract, screenshot)
│   │   ├── agents/           # Browser agents and automation
│   │   ├── document_loaders/ # Document loading integration
│   │   └── utils/            # Configuration, client, error handling
│   ├── tests/                # Test suite
│   └── examples/             # Usage examples
├── docs/                     # Documentation files
├── test_*.py                 # Root-level test files for development
└── STRATEGY.md               # Strategic overview document
```

## Development Commands

### Package Development (from langchain-steel/ directory)
- **Install for development**: `make install-dev` or `pip install -e ".[dev]"`
- **Run tests**: `make test` (all tests) or `pytest`
- **Run unit tests only**: `make test-unit` or `pytest -m "not integration"`  
- **Run integration tests**: `make test-integration` or `pytest -m integration`
- **Test with coverage**: `make test-cov`
- **Quick development tests**: `make test-quick` (unit tests with early exit)

### Code Quality
- **Format code**: `make format` (black + isort)
- **Check formatting**: `make format-check`
- **Lint**: `make lint` (flake8)
- **Type check**: `make type-check` (mypy)
- **All quality checks**: `make quality`
- **CI simulation**: `make ci-test`

### Development Setup
- **Complete setup**: `make dev-setup`
- **Install pre-commit**: `make pre-commit-install`
- **Run pre-commit**: `make pre-commit-run`

### Build and Release
- **Build package**: `make build`
- **Clean artifacts**: `make clean`
- **Test publish**: `make publish-test`
- **Publish**: `make publish`

## Architecture

### Core Components

The integration follows LangChain patterns with Steel.dev as the backend:

- **SteelDocumentLoader**: Batch web content loading with AI optimization
- **SteelScrapeTool**: Single page content extraction 
- **SteelBrowserAgent**: Natural language browser automation using Claude Computer Use
- **SteelConfig**: Configuration management for API keys, proxy settings, output formats

### Key Features

- **AI-Optimized**: Built for 80% token usage reduction through smart content extraction
- **Multi-Format Support**: HTML, Markdown, Text, PDF outputs
- **Enterprise-Ready**: Anti-bot bypass, CAPTCHA solving, proxy support, session management
- **LangChain Integration**: Tools, document loaders, and agents following LangChain patterns

### Output Formats

The integration supports multiple output formats via `OutputFormat` enum:
- `OutputFormat.MARKDOWN`: AI-optimized structured text (default)
- `OutputFormat.HTML`: Full HTML content
- `OutputFormat.TEXT`: Plain text extraction  
- `OutputFormat.PDF`: PDF document generation

### Session Management

Steel supports persistent browser sessions with:
- Authentication state preservation
- Session reuse for efficiency
- Configurable timeouts (default: 300s)
- Proxy and stealth mode options

## Environment Variables

- **STEEL_API_KEY**: Required for Steel.dev API access
- **ANTHROPIC_API_KEY**: Required for Claude Computer Use features in browser agent

## Test Organization

Tests are organized by type using pytest markers:
- `@pytest.mark.unit`: Unit tests (fast, no external dependencies)
- `@pytest.mark.integration`: Integration tests (require API keys)
- `@pytest.mark.slow`: Long-running tests

## Common Development Tasks

### Running Specific Tests
```bash
# Unit tests only
pytest -m "not integration"

# Integration tests only  
pytest -m integration

# Specific test file
pytest tests/test_basic_functionality.py

# Single test
pytest tests/test_basic_functionality.py::test_steel_scrape_tool_basic
```

### Working with the Package
The package structure allows importing key components:
```python
from langchain_steel import SteelScrapeTool, SteelBrowserAgent, SteelConfig
```

### Configuration Examples
```python
# Basic configuration
config = SteelConfig(
    api_key="your-steel-api-key",
    default_format=OutputFormat.MARKDOWN
)

# Advanced configuration  
config = SteelConfig(
    api_key="your-key",
    use_proxy=True,
    solve_captcha=True,
    stealth_mode=True,
    session_timeout=300
)
```

## Documentation

Additional documentation is available in the `docs/` directory:
- Authentication guides
- Tool usage examples
- Token efficiency documentation
- LangGraph integration patterns

## Test Files at Root Level

Root-level test files (`test_*.py`) are development utilities for testing Steel integration functionality:
- `test_steel_connection.py`: Tests basic Steel API connectivity
- `test_browser_agent.py`: Tests browser agent functionality
- `test_action_parsing.py`: Tests action parsing capabilities

These are meant for development debugging and API verification.