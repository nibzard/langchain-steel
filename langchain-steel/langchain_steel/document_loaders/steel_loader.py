"""Steel document loader for LangChain."""

import asyncio
import logging
from typing import Any, Dict, Iterator, List, Optional, Union
from urllib.parse import urlparse

from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document

from langchain_steel.utils.client import SteelClient, AsyncSteelClient
from langchain_steel.utils.config import SteelConfig, OutputFormat
from langchain_steel.utils.errors import SteelContentError, SteelError

logger = logging.getLogger(__name__)


class SteelDocumentLoader(BaseLoader):
    """Steel document loader for LangChain.
    
    Loads web content using Steel.dev's AI-optimized browser automation platform,
    providing token-efficient content extraction and enterprise-grade infrastructure.
    
    This loader supports:
    - Batch URL processing with session reuse
    - Multiple output formats (Markdown, HTML, Text, PDF)
    - Advanced browser features (proxy, CAPTCHA solving, stealth mode)
    - Metadata extraction and content optimization
    - Error handling and retry logic
    
    Examples:
        Basic usage:
            >>> loader = SteelDocumentLoader(
            ...     urls=["https://example.com"],
            ...     format=OutputFormat.MARKDOWN
            ... )
            >>> documents = loader.load()
        
        Advanced configuration:
            >>> config = SteelConfig(
            ...     api_key="your-key",
            ...     use_proxy=True,
            ...     solve_captcha=True
            ... )
            >>> loader = SteelDocumentLoader(
            ...     urls=["https://example.com"],
            ...     config=config,
            ...     extract_images=True,
            ...     session_reuse=True
            ... )
            >>> documents = loader.load()
        
        Async loading:
            >>> async def load_docs():
            ...     documents = await loader.aload()
            ...     return documents
    """
    
    def __init__(
        self,
        urls: Union[str, List[str]],
        config: Optional[SteelConfig] = None,
        format: Optional[OutputFormat] = None,
        session_reuse: bool = True,
        extract_images: bool = False,
        extract_links: bool = False,
        custom_headers: Optional[Dict[str, str]] = None,
        delay_ms: Optional[int] = None,
        wait_for_selector: Optional[str] = None,
        screenshot: bool = False,
        **kwargs: Any
    ) -> None:
        """Initialize Steel document loader.
        
        Args:
            urls: URL or list of URLs to load
            config: Steel configuration (uses environment defaults if None)
            format: Output format for content extraction
            session_reuse: Whether to reuse browser sessions for efficiency
            extract_images: Whether to extract image information
            extract_links: Whether to extract link information
            custom_headers: Custom HTTP headers to send
            delay_ms: Delay in milliseconds before content extraction
            wait_for_selector: CSS selector to wait for before extraction
            screenshot: Whether to capture screenshots
            **kwargs: Additional Steel API parameters
        """
        # Normalize URLs to list
        if isinstance(urls, str):
            self.urls = [urls]
        else:
            self.urls = list(urls)
        
        # Validate URLs
        self._validate_urls()
        
        # Configuration
        self.config = config or SteelConfig.from_env()
        self.format = format or self.config.default_format
        self.session_reuse = session_reuse
        
        # Content extraction options
        self.extract_images = extract_images
        self.extract_links = extract_links
        self.custom_headers = custom_headers or {}
        self.delay_ms = delay_ms
        self.wait_for_selector = wait_for_selector
        self.screenshot = screenshot
        
        # Additional Steel parameters
        self.steel_params = kwargs
        
        # Initialize clients
        self._client: Optional[SteelClient] = None
        self._async_client: Optional[AsyncSteelClient] = None
    
    def _validate_urls(self) -> None:
        """Validate that all URLs are properly formatted."""
        for url in self.urls:
            if not isinstance(url, str):
                raise SteelContentError(f"URL must be string, got {type(url)}")
            
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise SteelContentError(f"Invalid URL format: {url}")
            
            if parsed.scheme not in ("http", "https"):
                raise SteelContentError(f"Unsupported URL scheme: {parsed.scheme}")
    
    @property
    def client(self) -> SteelClient:
        """Get or create sync Steel client."""
        if self._client is None:
            self._client = SteelClient(self.config)
        return self._client
    
    @property
    def async_client(self) -> AsyncSteelClient:
        """Get or create async Steel client."""
        if self._async_client is None:
            self._async_client = AsyncSteelClient(self.config)
        return self._async_client
    
    def _extract_content_from_response(self, response: Dict[str, Any], url: str) -> str:
        """Extract content from Steel API response.
        
        Args:
            response: Steel API response
            url: Original URL (for error context)
            
        Returns:
            Extracted content string
            
        Raises:
            SteelContentError: If content extraction fails
        """
        try:
            # Handle different response formats from Steel API
            if isinstance(response, dict):
                # Try different content keys
                for content_key in ["content", "data", "body", "text", "html"]:
                    if content_key in response:
                        content = response[content_key]
                        if content and isinstance(content, str):
                            return content
                
                # If no content found, try to serialize the response
                if response:
                    return str(response)
            
            elif isinstance(response, str):
                return response
            
            else:
                return str(response)
        
        except Exception as e:
            raise SteelContentError(
                f"Failed to extract content from response for URL: {url}",
                url=url,
                format_requested=self.format.value,
                original_error=e
            )
        
        raise SteelContentError(
            f"No content found in Steel response for URL: {url}",
            url=url,
            format_requested=self.format.value
        )
    
    def _extract_metadata(self, response: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Extract metadata from Steel API response.
        
        Args:
            response: Steel API response
            url: Original URL
            
        Returns:
            Dictionary of metadata
        """
        metadata = {
            "source": url,
            "format": self.format.value,
            "loader": "SteelDocumentLoader"
        }
        
        if isinstance(response, dict):
            # Extract common metadata fields
            metadata_fields = {
                "title": ["title", "page_title"],
                "description": ["description", "meta_description"],
                "content_type": ["content_type", "mime_type"],
                "status_code": ["status_code", "http_status"],
                "final_url": ["final_url", "resolved_url", "url"],
                "load_time": ["load_time", "duration"],
                "page_size": ["page_size", "content_length"]
            }
            
            for meta_key, possible_keys in metadata_fields.items():
                for key in possible_keys:
                    if key in response:
                        metadata[meta_key] = response[key]
                        break
            
            # Extract image information if requested
            if self.extract_images and "images" in response:
                metadata["images"] = response["images"]
            
            # Extract link information if requested
            if self.extract_links and "links" in response:
                metadata["links"] = response["links"]
            
            # Add screenshot information if captured
            if self.screenshot and "screenshot" in response:
                metadata["screenshot"] = response["screenshot"]
        
        return metadata
    
    def _load_single_url(self, url: str) -> Document:
        """Load content from a single URL.
        
        Args:
            url: URL to load
            
        Returns:
            LangChain Document object
            
        Raises:
            SteelError: If loading fails
        """
        try:
            logger.info(f"Loading content from URL: {url}")
            
            # Prepare scraping parameters
            scrape_params = {
                "format": self.format.value,
                **self.steel_params
            }
            
            # Add optional parameters
            if self.custom_headers:
                scrape_params["headers"] = self.custom_headers
            
            if self.delay_ms is not None:
                scrape_params["delay"] = self.delay_ms
            
            if self.wait_for_selector:
                scrape_params["wait_for_selector"] = self.wait_for_selector
            
            if self.screenshot:
                scrape_params["screenshot"] = True
            
            if self.extract_images:
                scrape_params["extract_images"] = True
            
            if self.extract_links:
                scrape_params["extract_links"] = True
            
            # Scrape content using Steel client
            response = self.client.scrape(
                url=url,
                **scrape_params
            )
            
            # Extract content and metadata
            content = self._extract_content_from_response(response, url)
            metadata = self._extract_metadata(response, url)
            
            # Create and return Document
            document = Document(
                page_content=content,
                metadata=metadata
            )
            
            logger.info(f"Successfully loaded content from {url} (length: {len(content)})")
            return document
        
        except SteelError:
            # Re-raise Steel errors
            raise
        
        except Exception as e:
            raise SteelContentError(
                f"Failed to load content from URL: {url}",
                url=url,
                format_requested=self.format.value,
                original_error=e
            )
    
    async def _aload_single_url(self, url: str) -> Document:
        """Async load content from a single URL.
        
        Args:
            url: URL to load
            
        Returns:
            LangChain Document object
        """
        try:
            logger.info(f"Loading content from URL (async): {url}")
            
            # Prepare scraping parameters
            scrape_params = {
                "format": self.format.value,
                **self.steel_params
            }
            
            # Add optional parameters
            if self.custom_headers:
                scrape_params["headers"] = self.custom_headers
            
            if self.delay_ms is not None:
                scrape_params["delay"] = self.delay_ms
            
            if self.wait_for_selector:
                scrape_params["wait_for_selector"] = self.wait_for_selector
            
            if self.screenshot:
                scrape_params["screenshot"] = True
            
            if self.extract_images:
                scrape_params["extract_images"] = True
            
            if self.extract_links:
                scrape_params["extract_links"] = True
            
            # Note: This assumes Steel SDK has async scrape method
            # Adjust based on actual Steel SDK async API
            async with self.async_client.session_context() as session:
                response = await self.async_client.scrape(
                    url=url,
                    session=session,
                    **scrape_params
                )
            
            # Extract content and metadata
            content = self._extract_content_from_response(response, url)
            metadata = self._extract_metadata(response, url)
            
            # Create and return Document
            document = Document(
                page_content=content,
                metadata=metadata
            )
            
            logger.info(f"Successfully loaded content from {url} (async, length: {len(content)})")
            return document
        
        except SteelError:
            raise
        
        except Exception as e:
            raise SteelContentError(
                f"Failed to load content from URL: {url}",
                url=url,
                format_requested=self.format.value,
                original_error=e
            )
    
    def load(self) -> List[Document]:
        """Load documents from all URLs.
        
        Returns:
            List of LangChain Document objects
            
        Raises:
            SteelError: If loading fails
        """
        logger.info(f"Loading {len(self.urls)} URLs with Steel document loader")
        
        documents = []
        errors = []
        
        try:
            # Load documents with session reuse if enabled
            if self.session_reuse and len(self.urls) > 1:
                with self.client.session_context() as session:
                    for url in self.urls:
                        try:
                            # Use session for efficient loading
                            response = self.client.scrape(
                                url=url,
                                session=session,
                                format=self.format.value,
                                **self._get_scrape_params()
                            )
                            
                            content = self._extract_content_from_response(response, url)
                            metadata = self._extract_metadata(response, url)
                            
                            document = Document(
                                page_content=content,
                                metadata=metadata
                            )
                            documents.append(document)
                            
                        except Exception as e:
                            error_msg = f"Failed to load {url}: {str(e)}"
                            logger.warning(error_msg)
                            errors.append(error_msg)
            
            else:
                # Load documents individually
                for url in self.urls:
                    try:
                        document = self._load_single_url(url)
                        documents.append(document)
                    except Exception as e:
                        error_msg = f"Failed to load {url}: {str(e)}"
                        logger.warning(error_msg)
                        errors.append(error_msg)
            
            # Cleanup sessions
            self.client.cleanup_sessions()
            
            logger.info(f"Successfully loaded {len(documents)} out of {len(self.urls)} URLs")
            
            # If no documents loaded and we have errors, raise the first error
            if not documents and errors:
                raise SteelContentError(f"Failed to load any documents. First error: {errors[0]}")
            
            return documents
        
        except SteelError:
            raise
        
        except Exception as e:
            raise SteelError(f"Document loading failed: {str(e)}", original_error=e)
    
    async def aload(self) -> List[Document]:
        """Async load documents from all URLs.
        
        Returns:
            List of LangChain Document objects
        """
        logger.info(f"Loading {len(self.urls)} URLs with Steel document loader (async)")
        
        # Load documents concurrently
        try:
            tasks = [self._aload_single_url(url) for url in self.urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            documents = []
            errors = []
            
            for i, result in enumerate(results):
                if isinstance(result, Document):
                    documents.append(result)
                elif isinstance(result, Exception):
                    error_msg = f"Failed to load {self.urls[i]}: {str(result)}"
                    logger.warning(error_msg)
                    errors.append(error_msg)
            
            # Cleanup sessions
            await self.async_client.cleanup_sessions()
            
            logger.info(f"Successfully loaded {len(documents)} out of {len(self.urls)} URLs (async)")
            
            if not documents and errors:
                raise SteelContentError(f"Failed to load any documents. First error: {errors[0]}")
            
            return documents
        
        except SteelError:
            raise
        
        except Exception as e:
            raise SteelError(f"Async document loading failed: {str(e)}", original_error=e)
    
    def lazy_load(self) -> Iterator[Document]:
        """Lazy load documents one at a time.
        
        Yields:
            LangChain Document objects
        """
        logger.info(f"Lazy loading {len(self.urls)} URLs with Steel document loader")
        
        try:
            if self.session_reuse:
                with self.client.session_context() as session:
                    for url in self.urls:
                        try:
                            response = self.client.scrape(
                                url=url,
                                session=session,
                                format=self.format.value,
                                **self._get_scrape_params()
                            )
                            
                            content = self._extract_content_from_response(response, url)
                            metadata = self._extract_metadata(response, url)
                            
                            yield Document(
                                page_content=content,
                                metadata=metadata
                            )
                            
                        except Exception as e:
                            logger.warning(f"Failed to load {url}: {str(e)}")
                            continue
            else:
                for url in self.urls:
                    try:
                        document = self._load_single_url(url)
                        yield document
                    except Exception as e:
                        logger.warning(f"Failed to load {url}: {str(e)}")
                        continue
            
            # Cleanup after lazy loading
            self.client.cleanup_sessions()
        
        except Exception as e:
            raise SteelError(f"Lazy document loading failed: {str(e)}", original_error=e)
    
    def _get_scrape_params(self) -> Dict[str, Any]:
        """Get scraping parameters for Steel API calls.
        
        Returns:
            Dictionary of scraping parameters
        """
        params = self.steel_params.copy()
        
        if self.custom_headers:
            params["headers"] = self.custom_headers
        
        if self.delay_ms is not None:
            params["delay"] = self.delay_ms
        
        if self.wait_for_selector:
            params["wait_for_selector"] = self.wait_for_selector
        
        if self.screenshot:
            params["screenshot"] = True
        
        if self.extract_images:
            params["extract_images"] = True
        
        if self.extract_links:
            params["extract_links"] = True
        
        return params