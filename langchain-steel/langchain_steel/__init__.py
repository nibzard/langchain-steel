"""LangChain Steel Integration.

This package provides Steel.dev browser automation and web scraping capabilities
for LangChain applications, featuring AI-optimized content extraction and 
enterprise-grade browser infrastructure.
"""

# Only import working modules to avoid import errors
from langchain_steel.tools import SteelScrapeTool
from langchain_steel.agents import SteelBrowserAgent
from langchain_steel.utils import SteelConfig

# TODO: Enable these imports once implemented
# from langchain_steel.document_loaders import SteelDocumentLoader
# from langchain_steel.tools import (
#     SteelCrawlTool, 
#     SteelExtractTool,
#     SteelScreenshotTool,
# )

__version__ = "0.1.0"
__author__ = "Steel Integration Team"
__email__ = "integrations@steel.dev"

__all__ = [
    # Tools
    "SteelScrapeTool",
    # Agents
    "SteelBrowserAgent",
    # Configuration
    "SteelConfig",
    # Metadata
    "__version__",
    
    # TODO: Enable these once implemented
    # "SteelDocumentLoader",
    # "SteelCrawlTool",
    # "SteelExtractTool", 
    # "SteelScreenshotTool",
]