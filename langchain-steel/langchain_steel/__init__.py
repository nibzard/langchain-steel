"""LangChain Steel Integration.

This package provides Steel.dev browser automation and web scraping capabilities
for LangChain applications, featuring AI-optimized content extraction and 
enterprise-grade browser infrastructure.
"""

from langchain_steel.document_loaders import SteelDocumentLoader
from langchain_steel.tools import (
    SteelScrapeTool,
    SteelCrawlTool, 
    SteelExtractTool,
    SteelScreenshotTool,
)
from langchain_steel.agents import SteelBrowserAgent
from langchain_steel.utils import SteelConfig

__version__ = "0.1.0"
__author__ = "Steel Integration Team"
__email__ = "integrations@steel.dev"

__all__ = [
    # Document Loaders
    "SteelDocumentLoader",
    # Tools
    "SteelScrapeTool",
    "SteelCrawlTool",
    "SteelExtractTool", 
    "SteelScreenshotTool",
    # Agents
    "SteelBrowserAgent",
    # Configuration
    "SteelConfig",
    # Metadata
    "__version__",
]