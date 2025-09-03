"""Configuration management for Steel LangChain integration."""

import os
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum

from langchain_steel.utils.errors import SteelConfigError


class OutputFormat(str, Enum):
    """Supported output formats for Steel content extraction."""
    
    HTML = "html"
    MARKDOWN = "markdown"
    TEXT = "text"
    PDF = "pdf"


@dataclass
class ProxyConfig:
    """Proxy configuration for Steel requests."""
    
    enabled: bool = False
    rotate: bool = True
    country: Optional[str] = None
    sticky_session: bool = False


@dataclass
class SteelConfig:
    """Configuration class for Steel LangChain integration.
    
    This class manages all configuration options for Steel browser automation
    and web scraping operations, providing sensible defaults and validation.
    
    Attributes:
        api_key: Steel API key for authentication
        base_url: Steel API base URL (default: Steel Cloud)
        default_format: Default output format for content extraction
        session_timeout: Default session timeout in seconds
        api_timeout: API request timeout in milliseconds
        use_proxy: Whether to use Steel's proxy network
        solve_captcha: Whether to enable automatic CAPTCHA solving
        stealth_mode: Whether to enable stealth browsing features
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries in seconds
        session_options: Additional session configuration options
        proxy_config: Proxy-specific configuration
        user_agent: Custom user agent string
        enable_logging: Whether to enable detailed logging
    """
    
    # Authentication
    api_key: str = field(default_factory=lambda: os.getenv("STEEL_API_KEY", ""))
    base_url: str = "https://api.steel.dev"
    
    # Default behavior
    default_format: OutputFormat = OutputFormat.MARKDOWN
    session_timeout: int = 300  # 5 minutes
    api_timeout: int = 60000    # 60 seconds in milliseconds
    
    # Browser features - Default to False for hobby plan compatibility
    use_proxy: bool = False
    solve_captcha: bool = False
    stealth_mode: bool = False
    
    # Retry configuration
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Advanced options
    session_options: Dict[str, Any] = field(default_factory=dict)
    proxy_config: Optional[ProxyConfig] = field(default_factory=lambda: ProxyConfig())
    user_agent: Optional[str] = None
    enable_logging: bool = False
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate_config()
        
        # Set default proxy config if None
        if self.proxy_config is None:
            self.proxy_config = ProxyConfig()
    
    def _validate_config(self) -> None:
        """Validate configuration values."""
        if not self.api_key:
            raise SteelConfigError(
                "Steel API key is required. Set STEEL_API_KEY environment variable "
                "or provide api_key parameter."
            )
        
        if not self.base_url:
            raise SteelConfigError("Steel API base URL cannot be empty.")
        
        if self.session_timeout <= 0:
            raise SteelConfigError("Session timeout must be positive.")
        
        if self.api_timeout <= 0:
            raise SteelConfigError("API timeout must be positive.")
        
        if self.max_retries < 0:
            raise SteelConfigError("Max retries cannot be negative.")
        
        if self.retry_delay < 0:
            raise SteelConfigError("Retry delay cannot be negative.")
    
    @classmethod
    def from_env(cls, **kwargs: Any) -> "SteelConfig":
        """Create configuration from environment variables.
        
        Environment variables:
        - STEEL_API_KEY: Steel API key
        - STEEL_BASE_URL: Steel API base URL
        - STEEL_USE_PROXY: Whether to use proxy (true/false)
        - STEEL_SOLVE_CAPTCHA: Whether to solve CAPTCHAs (true/false)
        - STEEL_STEALTH_MODE: Whether to use stealth mode (true/false)
        - STEEL_SESSION_TIMEOUT: Session timeout in seconds
        - STEEL_API_TIMEOUT: API timeout in milliseconds
        - STEEL_MAX_RETRIES: Maximum retry attempts
        - STEEL_RETRY_DELAY: Retry delay in seconds
        
        Args:
            **kwargs: Additional configuration overrides
            
        Returns:
            SteelConfig instance with environment-based configuration
        """
        env_config = {
            "api_key": os.getenv("STEEL_API_KEY", ""),
            "base_url": os.getenv("STEEL_BASE_URL", "https://api.steel.dev"),
            "use_proxy": os.getenv("STEEL_USE_PROXY", "false").lower() == "true",
            "solve_captcha": os.getenv("STEEL_SOLVE_CAPTCHA", "false").lower() == "true",
            "stealth_mode": os.getenv("STEEL_STEALTH_MODE", "false").lower() == "true",
        }
        
        # Parse numeric environment variables
        if timeout := os.getenv("STEEL_SESSION_TIMEOUT"):
            try:
                env_config["session_timeout"] = int(timeout)
            except ValueError:
                raise SteelConfigError(f"Invalid STEEL_SESSION_TIMEOUT: {timeout}")
        
        if api_timeout := os.getenv("STEEL_API_TIMEOUT"):
            try:
                env_config["api_timeout"] = int(api_timeout)
            except ValueError:
                raise SteelConfigError(f"Invalid STEEL_API_TIMEOUT: {api_timeout}")
        
        if max_retries := os.getenv("STEEL_MAX_RETRIES"):
            try:
                env_config["max_retries"] = int(max_retries)
            except ValueError:
                raise SteelConfigError(f"Invalid STEEL_MAX_RETRIES: {max_retries}")
        
        if retry_delay := os.getenv("STEEL_RETRY_DELAY"):
            try:
                env_config["retry_delay"] = float(retry_delay)
            except ValueError:
                raise SteelConfigError(f"Invalid STEEL_RETRY_DELAY: {retry_delay}")
        
        # Merge with provided kwargs, with kwargs taking precedence
        env_config.update(kwargs)
        
        return cls(**env_config)
    
    def to_session_options(self) -> Dict[str, Any]:
        """Convert configuration to Steel SDK session options.
        
        Returns:
            Dictionary suitable for Steel.sessions.create() call
        """
        options = {
            # Valid Steel SDK parameters
            "api_timeout": self.api_timeout,
            "solve_captcha": self.solve_captcha,
        }
        
        # Handle proxy configuration - explicitly set to avoid Steel SDK defaults
        options["use_proxy"] = self.use_proxy
        
        if self.use_proxy:
            # Add proxy-specific options if configured
            if self.proxy_config:
                if self.proxy_config.country:
                    options["region"] = self.proxy_config.country.lower()
        
        # Add user agent if specified
        if self.user_agent:
            options["user_agent"] = self.user_agent
        
        # Add stealth configuration if enabled
        if self.stealth_mode:
            options["block_ads"] = True
            # Note: stealth_config structure needs to be determined from Steel SDK docs
        
        # Merge with custom session options (these override defaults)
        options.update(self.session_options)
        
        return options
    
    def copy(self, **changes: Any) -> "SteelConfig":
        """Create a copy of the configuration with optional changes.
        
        Args:
            **changes: Configuration fields to update
            
        Returns:
            New SteelConfig instance with applied changes
        """
        # Create dict of current values
        current_values = {
            field.name: getattr(self, field.name) 
            for field in self.__dataclass_fields__.values()
        }
        
        # Apply changes
        current_values.update(changes)
        
        return SteelConfig(**current_values)