"""Steel scrape tool for single-page content extraction."""

import logging
from typing import Any, Dict, Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
from pydantic import BaseModel, Field

from langchain_steel.tools.base import BaseSteelTool
from langchain_steel.utils.config import OutputFormat
from langchain_steel.utils.errors import SteelContentError

logger = logging.getLogger(__name__)


class SteelScrapeInput(BaseModel):
    """Input schema for Steel scrape tool."""
    
    url: str = Field(description="URL to scrape content from")
    format: Optional[str] = Field(
        default="markdown",
        description="Output format: html, markdown, text, or pdf"
    )
    wait_for_selector: Optional[str] = Field(
        default=None,
        description="CSS selector to wait for before scraping"
    )
    delay_ms: Optional[int] = Field(
        default=None,
        description="Delay in milliseconds before scraping content"
    )
    screenshot: bool = Field(
        default=False,
        description="Whether to capture a screenshot"
    )
    extract_images: bool = Field(
        default=False,
        description="Whether to extract image information"
    )
    extract_links: bool = Field(
        default=False,
        description="Whether to extract link information"
    )
    custom_headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="Custom HTTP headers to send with the request"
    )


class SteelScrapeTool(BaseSteelTool):
    """Steel tool for scraping content from a single web page.
    
    This tool uses Steel.dev's AI-optimized browser automation to extract
    content from web pages with advanced features like:
    - Multiple output formats (HTML, Markdown, Text, PDF)
    - JavaScript rendering and dynamic content support
    - CAPTCHA solving and anti-bot bypass
    - Proxy support for geographic targeting
    - Screenshot capture
    - Metadata and link extraction
    
    Examples:
        Basic scraping:
            >>> scraper = SteelScrapeTool()
            >>> result = scraper.run("https://example.com")
        
        With specific format:
            >>> result = scraper.run({
            ...     "url": "https://example.com",
            ...     "format": "markdown",
            ...     "screenshot": True
            ... })
        
        Advanced usage with selectors:
            >>> result = scraper.run({
            ...     "url": "https://example.com",
            ...     "wait_for_selector": ".main-content",
            ...     "delay_ms": 2000,
            ...     "extract_links": True
            ... })
    """
    
    name: str = "steel_scrape"
    description: str = (
        "Scrape content from a single web page using Steel.dev's AI-optimized browser automation. "
        "Supports JavaScript rendering, CAPTCHA solving, and multiple output formats. "
        "Input should be a URL string or dict with url and optional parameters like format, "
        "wait_for_selector, delay_ms, screenshot, extract_images, extract_links, and custom_headers."
    )
    args_schema: Type[BaseModel] = SteelScrapeInput
    
    def _run(
        self,
        url: str,
        format: Optional[str] = "markdown",
        wait_for_selector: Optional[str] = None,
        delay_ms: Optional[int] = None,
        screenshot: bool = False,
        extract_images: bool = False,
        extract_links: bool = False,
        custom_headers: Optional[Dict[str, str]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Scrape content from a web page.
        
        Args:
            url: URL to scrape
            format: Output format (html, markdown, text, pdf)
            wait_for_selector: CSS selector to wait for
            delay_ms: Delay before scraping in milliseconds
            screenshot: Whether to capture screenshot
            extract_images: Whether to extract image information
            extract_links: Whether to extract link information
            custom_headers: Custom HTTP headers
            run_manager: Callback manager for tool execution
            
        Returns:
            Scraped content as string, or error message if scraping fails
        """
        try:
            self._log_tool_execution("scrape", {
                "url": url,
                "format": format,
                "wait_for_selector": wait_for_selector,
                "delay_ms": delay_ms,
                "screenshot": screenshot,
                "extract_images": extract_images,
                "extract_links": extract_links,
            })
            
            # Validate format
            if format and format.lower() not in [f.value for f in OutputFormat]:
                return f"Invalid format '{format}'. Supported formats: html, markdown, text, pdf"
            
            # Prepare scraping parameters
            scrape_params = {
                "format": format or "markdown",
            }
            
            if wait_for_selector:
                scrape_params["wait_for_selector"] = wait_for_selector
            
            if delay_ms is not None:
                scrape_params["delay"] = delay_ms
            
            if screenshot:
                scrape_params["screenshot"] = True
            
            if extract_images:
                scrape_params["extract_images"] = True
            
            if extract_links:
                scrape_params["extract_links"] = True
            
            if custom_headers:
                scrape_params["headers"] = custom_headers
            
            # Execute scraping
            if run_manager:
                run_manager.on_text(f"Scraping content from: {url}\n")
            
            response = self.client.scrape(url=url, **scrape_params)
            
            # Extract content from response
            content = self._extract_content_from_response(response, url, format)
            
            if run_manager:
                run_manager.on_text(f"Successfully scraped {len(content)} characters\n")
            
            # Add metadata if additional extraction was requested
            if screenshot or extract_images or extract_links:
                metadata = self._extract_metadata_summary(response)
                if metadata:
                    content += f"\n\n--- Metadata ---\n{metadata}"
            
            return content
        
        except Exception as e:
            error_msg = self._handle_steel_error(e, "scrape")
            if run_manager:
                run_manager.on_text(f"Error: {error_msg}\n")
            return f"Error scraping {url}: {error_msg}"
    
    async def _arun(
        self,
        url: str,
        format: Optional[str] = "markdown",
        wait_for_selector: Optional[str] = None,
        delay_ms: Optional[int] = None,
        screenshot: bool = False,
        extract_images: bool = False,
        extract_links: bool = False,
        custom_headers: Optional[Dict[str, str]] = None,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Async scrape content from a web page.
        
        Args:
            url: URL to scrape
            format: Output format (html, markdown, text, pdf)
            wait_for_selector: CSS selector to wait for
            delay_ms: Delay before scraping in milliseconds
            screenshot: Whether to capture screenshot
            extract_images: Whether to extract image information
            extract_links: Whether to extract link information
            custom_headers: Custom HTTP headers
            run_manager: Async callback manager for tool execution
            
        Returns:
            Scraped content as string, or error message if scraping fails
        """
        try:
            self._log_tool_execution("scrape", {
                "url": url,
                "format": format,
                "async": True,
            })
            
            # Validate format
            if format and format.lower() not in [f.value for f in OutputFormat]:
                return f"Invalid format '{format}'. Supported formats: html, markdown, text, pdf"
            
            # Prepare scraping parameters
            scrape_params = {
                "format": format or "markdown",
            }
            
            if wait_for_selector:
                scrape_params["wait_for_selector"] = wait_for_selector
            
            if delay_ms is not None:
                scrape_params["delay"] = delay_ms
            
            if screenshot:
                scrape_params["screenshot"] = True
            
            if extract_images:
                scrape_params["extract_images"] = True
            
            if extract_links:
                scrape_params["extract_links"] = True
            
            if custom_headers:
                scrape_params["headers"] = custom_headers
            
            # Execute async scraping
            if run_manager:
                await run_manager.on_text(f"Scraping content from: {url}\n")
            
            # Use session context for efficient async scraping
            async with self.async_client.session_context() as session:
                # Note: Adjust based on actual Steel SDK async API
                response = await self.async_client.scrape(
                    url=url, 
                    session=session,
                    **scrape_params
                )
            
            # Extract content from response
            content = self._extract_content_from_response(response, url, format)
            
            if run_manager:
                await run_manager.on_text(f"Successfully scraped {len(content)} characters\n")
            
            # Add metadata if additional extraction was requested
            if screenshot or extract_images or extract_links:
                metadata = self._extract_metadata_summary(response)
                if metadata:
                    content += f"\n\n--- Metadata ---\n{metadata}"
            
            return content
        
        except Exception as e:
            error_msg = self._handle_steel_error(e, "scrape")
            if run_manager:
                await run_manager.on_text(f"Error: {error_msg}\n")
            return f"Error scraping {url}: {error_msg}"
    
    def _extract_content_from_response(self, response: Any, url: str, format: str) -> str:
        """Extract content from Steel API response.
        
        Args:
            response: Steel API response
            url: Original URL
            format: Requested format
            
        Returns:
            Extracted content string
            
        Raises:
            SteelContentError: If content extraction fails
        """
        try:
            if isinstance(response, dict):
                # Try different content keys based on format
                content_keys = ["content", "data", "body", "text", "html", "markdown"]
                
                for key in content_keys:
                    if key in response and response[key]:
                        content = response[key]
                        if isinstance(content, str):
                            return content.strip()
                
                # If no standard content key found, try to serialize
                if response:
                    return str(response)
            
            elif isinstance(response, str):
                return response.strip()
            
            else:
                return str(response)
        
        except Exception as e:
            raise SteelContentError(
                f"Failed to extract content from Steel response for URL: {url}",
                url=url,
                format_requested=format,
                original_error=e
            )
        
        raise SteelContentError(
            f"No content found in Steel response for URL: {url}",
            url=url,
            format_requested=format
        )
    
    def _extract_metadata_summary(self, response: Any) -> str:
        """Extract and format metadata summary from response.
        
        Args:
            response: Steel API response
            
        Returns:
            Formatted metadata summary
        """
        if not isinstance(response, dict):
            return ""
        
        metadata_parts = []
        
        # Title and basic info
        if "title" in response:
            metadata_parts.append(f"Title: {response['title']}")
        
        if "final_url" in response and response["final_url"]:
            metadata_parts.append(f"Final URL: {response['final_url']}")
        
        if "status_code" in response:
            metadata_parts.append(f"Status Code: {response['status_code']}")
        
        # Performance info
        if "load_time" in response:
            metadata_parts.append(f"Load Time: {response['load_time']}ms")
        
        # Images
        if "images" in response and response["images"]:
            images = response["images"]
            if isinstance(images, list):
                metadata_parts.append(f"Images Found: {len(images)}")
                # Show first few image URLs
                for i, img in enumerate(images[:3]):
                    if isinstance(img, dict) and "src" in img:
                        metadata_parts.append(f"  Image {i+1}: {img['src']}")
                    elif isinstance(img, str):
                        metadata_parts.append(f"  Image {i+1}: {img}")
                
                if len(images) > 3:
                    metadata_parts.append(f"  ... and {len(images) - 3} more images")
        
        # Links
        if "links" in response and response["links"]:
            links = response["links"]
            if isinstance(links, list):
                metadata_parts.append(f"Links Found: {len(links)}")
                # Show first few links
                for i, link in enumerate(links[:3]):
                    if isinstance(link, dict):
                        href = link.get("href", "")
                        text = link.get("text", "")
                        metadata_parts.append(f"  Link {i+1}: {text} -> {href}")
                    elif isinstance(link, str):
                        metadata_parts.append(f"  Link {i+1}: {link}")
                
                if len(links) > 3:
                    metadata_parts.append(f"  ... and {len(links) - 3} more links")
        
        # Screenshot
        if "screenshot" in response and response["screenshot"]:
            metadata_parts.append(f"Screenshot: {response['screenshot']}")
        
        return "\n".join(metadata_parts) if metadata_parts else ""