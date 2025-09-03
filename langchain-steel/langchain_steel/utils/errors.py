"""Custom exceptions for Steel LangChain integration."""

from typing import Any, Dict, Optional


class SteelError(Exception):
    """Base exception for all Steel-related errors."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ) -> None:
        """Initialize Steel error.
        
        Args:
            message: Human-readable error message
            details: Additional error details and context
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.original_error = original_error
    
    def __str__(self) -> str:
        """Return string representation of error."""
        error_str = self.message
        
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            error_str += f" (Details: {details_str})"
        
        if self.original_error:
            error_str += f" (Caused by: {self.original_error})"
        
        return error_str


class SteelConfigError(SteelError):
    """Exception raised for configuration-related errors."""
    
    def __init__(self, message: str, config_field: Optional[str] = None) -> None:
        """Initialize configuration error.
        
        Args:
            message: Error message
            config_field: Name of the problematic configuration field
        """
        details = {"config_field": config_field} if config_field else None
        super().__init__(message, details)
        self.config_field = config_field


class SteelAPIError(SteelError):
    """Exception raised for Steel API-related errors."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        api_error_code: Optional[str] = None,
        request_id: Optional[str] = None,
        original_error: Optional[Exception] = None
    ) -> None:
        """Initialize API error.
        
        Args:
            message: Error message
            status_code: HTTP status code from API response
            api_error_code: Steel-specific error code
            request_id: Request ID for tracking
            original_error: Original HTTP exception
        """
        details = {
            "status_code": status_code,
            "api_error_code": api_error_code,
            "request_id": request_id,
        }
        # Remove None values
        details = {k: v for k, v in details.items() if v is not None}
        
        super().__init__(message, details, original_error)
        self.status_code = status_code
        self.api_error_code = api_error_code
        self.request_id = request_id


class SteelTimeoutError(SteelError):
    """Exception raised when Steel operations timeout."""
    
    def __init__(
        self,
        message: str = "Operation timed out",
        timeout_duration: Optional[float] = None,
        operation: Optional[str] = None,
        original_error: Optional[Exception] = None
    ) -> None:
        """Initialize timeout error.
        
        Args:
            message: Error message
            timeout_duration: Timeout duration in seconds
            operation: Name of the operation that timed out
            original_error: Original timeout exception
        """
        details = {
            "timeout_duration": timeout_duration,
            "operation": operation,
        }
        # Remove None values
        details = {k: v for k, v in details.items() if v is not None}
        
        super().__init__(message, details, original_error)
        self.timeout_duration = timeout_duration
        self.operation = operation


class SteelRateLimitError(SteelAPIError):
    """Exception raised when Steel API rate limits are exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        rate_limit_type: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """Initialize rate limit error.
        
        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
            rate_limit_type: Type of rate limit (requests, sessions, etc.)
            **kwargs: Additional arguments for SteelAPIError
        """
        super().__init__(message, **kwargs)
        self.retry_after = retry_after
        self.rate_limit_type = rate_limit_type
        
        # Add rate limit details
        if retry_after is not None:
            self.details["retry_after"] = retry_after
        if rate_limit_type is not None:
            self.details["rate_limit_type"] = rate_limit_type


class SteelSessionError(SteelError):
    """Exception raised for Steel session-related errors."""
    
    def __init__(
        self,
        message: str,
        session_id: Optional[str] = None,
        session_state: Optional[str] = None,
        original_error: Optional[Exception] = None
    ) -> None:
        """Initialize session error.
        
        Args:
            message: Error message
            session_id: ID of the problematic session
            session_state: Current session state
            original_error: Original exception
        """
        details = {
            "session_id": session_id,
            "session_state": session_state,
        }
        # Remove None values
        details = {k: v for k, v in details.items() if v is not None}
        
        super().__init__(message, details, original_error)
        self.session_id = session_id
        self.session_state = session_state


class SteelContentError(SteelError):
    """Exception raised for content extraction and processing errors."""
    
    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        content_type: Optional[str] = None,
        format_requested: Optional[str] = None,
        original_error: Optional[Exception] = None
    ) -> None:
        """Initialize content error.
        
        Args:
            message: Error message
            url: URL being processed when error occurred
            content_type: MIME type of content
            format_requested: Output format that was requested
            original_error: Original exception
        """
        details = {
            "url": url,
            "content_type": content_type,
            "format_requested": format_requested,
        }
        # Remove None values  
        details = {k: v for k, v in details.items() if v is not None}
        
        super().__init__(message, details, original_error)
        self.url = url
        self.content_type = content_type
        self.format_requested = format_requested


class SteelAuthenticationError(SteelAPIError):
    """Exception raised for authentication-related errors."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        api_key_valid: Optional[bool] = None,
        **kwargs: Any
    ) -> None:
        """Initialize authentication error.
        
        Args:
            message: Error message
            api_key_valid: Whether the API key format is valid
            **kwargs: Additional arguments for SteelAPIError
        """
        super().__init__(message, **kwargs)
        self.api_key_valid = api_key_valid
        
        if api_key_valid is not None:
            self.details["api_key_valid"] = api_key_valid


def handle_steel_api_error(response: Any, request_id: Optional[str] = None) -> SteelAPIError:
    """Convert Steel API response to appropriate exception.
    
    Args:
        response: HTTP response object
        request_id: Request ID for tracking
        
    Returns:
        Appropriate SteelAPIError subclass
    """
    status_code = getattr(response, "status_code", None)
    
    try:
        error_data = response.json() if hasattr(response, "json") else {}
    except Exception:
        error_data = {}
    
    message = error_data.get("message", f"API error {status_code}")
    api_error_code = error_data.get("error_code")
    
    # Determine specific error type based on status code
    if status_code == 401:
        return SteelAuthenticationError(
            message=message,
            status_code=status_code,
            api_error_code=api_error_code,
            request_id=request_id,
        )
    elif status_code == 429:
        retry_after = None
        if hasattr(response, "headers"):
            retry_after_header = response.headers.get("Retry-After")
            if retry_after_header:
                try:
                    retry_after = int(retry_after_header)
                except ValueError:
                    pass
        
        return SteelRateLimitError(
            message=message,
            status_code=status_code,
            api_error_code=api_error_code,
            request_id=request_id,
            retry_after=retry_after,
        )
    elif status_code and 500 <= status_code < 600:
        return SteelAPIError(
            message=f"Server error: {message}",
            status_code=status_code,
            api_error_code=api_error_code,
            request_id=request_id,
        )
    else:
        return SteelAPIError(
            message=message,
            status_code=status_code,
            api_error_code=api_error_code,
            request_id=request_id,
        )