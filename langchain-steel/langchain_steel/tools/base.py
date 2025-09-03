"""Base Steel tool for LangChain agents."""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, Union

from langchain_core.callbacks import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from langchain_steel.utils.client import SteelClient, AsyncSteelClient
from langchain_steel.utils.config import SteelConfig
from langchain_steel.utils.errors import SteelError

logger = logging.getLogger(__name__)


class BaseSteelTool(BaseTool, ABC):
    """Abstract base class for Steel tools.
    
    Provides common functionality for all Steel tools including:
    - Steel client initialization and management
    - Session handling
    - Error handling and logging
    - Configuration management
    """
    
    # Tool metadata (to be overridden by subclasses)
    name: str = "steel_tool"
    description: str = "A Steel.dev browser automation tool"
    
    # Configuration
    config: Optional[SteelConfig] = Field(default=None, exclude=True)
    session_reuse: bool = Field(default=True, description="Whether to reuse browser sessions")
    
    # Internal clients - using PrivateAttr since they start with underscore
    _client: Optional[SteelClient] = PrivateAttr(default=None)
    _async_client: Optional[AsyncSteelClient] = PrivateAttr(default=None)
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
    
    def __init__(self, **kwargs: Any) -> None:
        """Initialize Steel tool.
        
        Args:
            **kwargs: Tool configuration parameters
        """
        super().__init__(**kwargs)
        
        # Initialize configuration
        if self.config is None:
            self.config = SteelConfig.from_env()
        
        # Setup logging
        if self.config.enable_logging:
            logging.basicConfig(level=logging.INFO)
    
    @property
    def client(self) -> SteelClient:
        """Get or create synchronous Steel client."""
        if self._client is None:
            self._client = SteelClient(self.config)
        return self._client
    
    @property
    def async_client(self) -> AsyncSteelClient:
        """Get or create asynchronous Steel client."""
        if self._async_client is None:
            self._async_client = AsyncSteelClient(self.config)
        return self._async_client
    
    @abstractmethod
    def _run(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any,
    ) -> Any:
        """Run the tool synchronously.
        
        To be implemented by subclasses.
        
        Args:
            run_manager: Callback manager for tool execution
            **kwargs: Tool-specific parameters
            
        Returns:
            Tool execution result
        """
        pass
    
    @abstractmethod
    async def _arun(
        self,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
        **kwargs: Any,
    ) -> Any:
        """Run the tool asynchronously.
        
        To be implemented by subclasses.
        
        Args:
            run_manager: Async callback manager for tool execution
            **kwargs: Tool-specific parameters
            
        Returns:
            Tool execution result
        """
        pass
    
    def _prepare_steel_params(self, **kwargs: Any) -> Dict[str, Any]:
        """Prepare parameters for Steel API calls.
        
        Args:
            **kwargs: Raw parameters from tool input
            
        Returns:
            Cleaned parameters suitable for Steel API
        """
        # Remove None values and internal parameters
        cleaned_params = {}
        
        for key, value in kwargs.items():
            if value is not None and not key.startswith('_'):
                cleaned_params[key] = value
        
        return cleaned_params
    
    def _handle_steel_error(self, error: Exception, operation: str) -> str:
        """Handle and format Steel errors for user consumption.
        
        Args:
            error: Exception that occurred
            operation: Name of the operation that failed
            
        Returns:
            User-friendly error message
        """
        if isinstance(error, SteelError):
            error_msg = f"Steel {operation} failed: {error.message}"
            
            if hasattr(error, 'details') and error.details:
                # Add relevant error details
                relevant_details = {
                    k: v for k, v in error.details.items() 
                    if k in ['url', 'status_code', 'retry_after']
                }
                if relevant_details:
                    details_str = ", ".join(f"{k}={v}" for k, v in relevant_details.items())
                    error_msg += f" ({details_str})"
            
            logger.error(error_msg)
            return error_msg
        
        else:
            error_msg = f"Steel {operation} failed: {str(error)}"
            logger.error(error_msg)
            return error_msg
    
    def _log_tool_execution(self, operation: str, params: Dict[str, Any]) -> None:
        """Log tool execution details.
        
        Args:
            operation: Name of the operation
            params: Parameters used for the operation
        """
        if self.config and self.config.enable_logging:
            # Filter sensitive parameters for logging
            safe_params = {
                k: v for k, v in params.items() 
                if k not in ['api_key', 'session_id', 'headers']
            }
            logger.info(f"Executing Steel {operation} with params: {safe_params}")
    
    def cleanup(self) -> None:
        """Cleanup tool resources."""
        try:
            if self._client:
                self._client.cleanup_sessions()
            if self._async_client:
                # Note: This would need to be called from an async context
                # asyncio.create_task(self._async_client.cleanup_sessions())
                pass
        except Exception as e:
            logger.warning(f"Error during tool cleanup: {e}")
    
    def __del__(self) -> None:
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore errors during cleanup in destructor


class SteelToolInput(BaseModel):
    """Base input schema for Steel tools."""
    
    class Config:
        """Pydantic configuration."""
        extra = "allow"  # Allow additional fields for tool-specific parameters


class SteelToolMixin:
    """Mixin class providing common Steel tool functionality.
    
    Can be used to add Steel capabilities to existing tools.
    """
    
    def __init__(self, config: Optional[SteelConfig] = None, **kwargs: Any) -> None:
        """Initialize Steel tool mixin.
        
        Args:
            config: Steel configuration
            **kwargs: Additional parameters
        """
        super().__init__(**kwargs)
        self.steel_config = config or SteelConfig.from_env()
        self._steel_client: Optional[SteelClient] = None
        self._steel_async_client: Optional[AsyncSteelClient] = None
    
    @property
    def steel_client(self) -> SteelClient:
        """Get or create Steel client."""
        if self._steel_client is None:
            self._steel_client = SteelClient(self.steel_config)
        return self._steel_client
    
    @property
    def steel_async_client(self) -> AsyncSteelClient:
        """Get or create async Steel client."""
        if self._steel_async_client is None:
            self._steel_async_client = AsyncSteelClient(self.steel_config)
        return self._steel_async_client


def create_steel_tool(
    name: str,
    description: str,
    input_schema: Type[BaseModel],
    sync_func: callable,
    async_func: callable = None,
    config: Optional[SteelConfig] = None,
) -> Type[BaseSteelTool]:
    """Factory function to create Steel tools.
    
    Args:
        name: Tool name
        description: Tool description
        input_schema: Pydantic schema for tool inputs
        sync_func: Synchronous implementation function
        async_func: Asynchronous implementation function (optional)
        config: Steel configuration (optional)
        
    Returns:
        Steel tool class
    """
    
    class DynamicSteelTool(BaseSteelTool):
        name = name
        description = description
        args_schema = input_schema
        
        def _run(
            self,
            run_manager: Optional[CallbackManagerForToolRun] = None,
            **kwargs: Any,
        ) -> Any:
            """Run the tool synchronously."""
            try:
                self._log_tool_execution(name, kwargs)
                steel_params = self._prepare_steel_params(**kwargs)
                return sync_func(self.client, steel_params, run_manager)
            
            except Exception as e:
                return self._handle_steel_error(e, name)
        
        async def _arun(
            self,
            run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
            **kwargs: Any,
        ) -> Any:
            """Run the tool asynchronously."""
            try:
                self._log_tool_execution(name, kwargs)
                steel_params = self._prepare_steel_params(**kwargs)
                
                if async_func:
                    return await async_func(self.async_client, steel_params, run_manager)
                else:
                    # Fallback to sync function in thread pool
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(
                        None, lambda: sync_func(self.client, steel_params, run_manager)
                    )
            
            except Exception as e:
                return self._handle_steel_error(e, name)
    
    if config:
        DynamicSteelTool.config = config
    
    return DynamicSteelTool