"""Steel client wrapper for LangChain integration."""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Union
from contextlib import asynccontextmanager, contextmanager

try:
    from steel import Steel, AsyncSteel
    from steel.types import Session
except ImportError as e:
    raise ImportError(
        "Steel SDK is required. Install with: pip install steel-sdk>=0.1.0b9"
    ) from e

from langchain_steel.utils.config import SteelConfig
from langchain_steel.utils.errors import (
    SteelAPIError,
    SteelAuthenticationError,
    SteelError,
    SteelSessionError,
    SteelTimeoutError,
    handle_steel_api_error,
)
from langchain_steel.utils.retry import retry_on_steel_error, async_retry_on_steel_error

logger = logging.getLogger(__name__)


class SteelSessionManager:
    """Manages Steel browser sessions with pooling and reuse capabilities."""
    
    def __init__(self, max_sessions: int = 10, session_ttl: int = 300) -> None:
        """Initialize session manager.
        
        Args:
            max_sessions: Maximum number of concurrent sessions
            session_ttl: Session time-to-live in seconds
        """
        self.max_sessions = max_sessions
        self.session_ttl = session_ttl
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._session_lock = asyncio.Lock()
    
    def add_session(self, session: Session, reusable: bool = True) -> None:
        """Add session to pool.
        
        Args:
            session: Steel session object
            reusable: Whether session can be reused
        """
        self._sessions[session.id] = {
            "session": session,
            "created_at": time.time(),
            "last_used": time.time(),
            "reusable": reusable,
            "in_use": False,
        }
    
    def get_available_session(self) -> Optional[Session]:
        """Get an available session from the pool.
        
        Returns:
            Available session or None if no sessions available
        """
        current_time = time.time()
        
        for session_id, session_data in self._sessions.items():
            # Check if session is expired
            if current_time - session_data["created_at"] > self.session_ttl:
                continue
            
            # Check if session is available and reusable
            if (
                not session_data["in_use"] 
                and session_data["reusable"]
            ):
                session_data["in_use"] = True
                session_data["last_used"] = current_time
                return session_data["session"]
        
        return None
    
    def release_session(self, session_id: str) -> None:
        """Release session back to pool.
        
        Args:
            session_id: ID of session to release
        """
        if session_id in self._sessions:
            self._sessions[session_id]["in_use"] = False
            self._sessions[session_id]["last_used"] = time.time()
    
    def remove_session(self, session_id: str) -> None:
        """Remove session from pool.
        
        Args:
            session_id: ID of session to remove
        """
        self._sessions.pop(session_id, None)
    
    def cleanup_expired_sessions(self) -> List[str]:
        """Remove expired sessions from pool.
        
        Returns:
            List of removed session IDs
        """
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session_data in list(self._sessions.items()):
            if current_time - session_data["created_at"] > self.session_ttl:
                expired_sessions.append(session_id)
                self.remove_session(session_id)
        
        return expired_sessions
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session pool statistics.
        
        Returns:
            Dictionary with session statistics
        """
        total_sessions = len(self._sessions)
        in_use_sessions = sum(1 for s in self._sessions.values() if s["in_use"])
        available_sessions = total_sessions - in_use_sessions
        
        return {
            "total_sessions": total_sessions,
            "in_use_sessions": in_use_sessions,
            "available_sessions": available_sessions,
            "max_sessions": self.max_sessions,
        }


class SteelClient:
    """Enhanced Steel client with session management and retry logic."""
    
    def __init__(self, config: Optional[SteelConfig] = None) -> None:
        """Initialize Steel client.
        
        Args:
            config: Steel configuration (uses environment defaults if None)
        """
        self.config = config or SteelConfig.from_env()
        
        # Initialize Steel SDK clients
        try:
            self._client = Steel(steel_api_key=self.config.api_key)
            self._async_client = AsyncSteel(steel_api_key=self.config.api_key)
        except Exception as e:
            raise SteelAuthenticationError(
                "Failed to initialize Steel client. Check API key.",
                original_error=e,
            )
        
        # Session management
        self.session_manager = SteelSessionManager()
        
        # Setup logging
        if self.config.enable_logging:
            logging.basicConfig(level=logging.INFO)
    
    def create_session(
        self, 
        reuse_existing: bool = True,
        **session_options: Any
    ) -> Session:
        """Create or reuse a Steel browser session.
        
        Args:
            reuse_existing: Whether to try reusing an existing session
            **session_options: Additional session options
            
        Returns:
            Steel session object
            
        Raises:
            SteelSessionError: If session creation fails
        """
        # Try to reuse existing session if requested
        if reuse_existing:
            existing_session = self.session_manager.get_available_session()
            if existing_session:
                logger.info(f"Reusing existing session: {existing_session.id}")
                return existing_session
        
        # Create new session
        try:
            # Merge config options with provided options
            options = self.config.to_session_options()
            options.update(session_options)
            
            logger.info("Creating new Steel session...")
            session = self._client.sessions.create(**options)
            
            # Add to session pool if reusable
            self.session_manager.add_session(session, reusable=reuse_existing)
            
            logger.info(f"Created Steel session: {session.id}")
            return session
            
        except Exception as e:
            # Clean up any failed session attempts
            self.session_manager.cleanup_expired_sessions()
            
            if hasattr(e, "response"):
                raise handle_steel_api_error(e.response)
            else:
                raise SteelSessionError(
                    f"Failed to create Steel session: {str(e)}",
                    original_error=e,
                )
    
    def release_session(self, session_id: str) -> None:
        """Release and cleanup Steel session.
        
        Args:
            session_id: ID of session to release
        """
        try:
            self._client.sessions.release(session_id)
            self.session_manager.remove_session(session_id)
            logger.info(f"Released Steel session: {session_id}")
            
        except Exception as e:
            logger.warning(f"Failed to release session {session_id}: {str(e)}")
            # Remove from local pool even if API call fails
            self.session_manager.remove_session(session_id)
    
    def scrape(
        self,
        url: str,
        session: Optional[Session] = None,
        format: Optional[str] = None,
        **scrape_options: Any
    ) -> Dict[str, Any]:
        """Scrape content from URL using Steel.
        
        Args:
            url: URL to scrape
            session: Optional existing session to use
            format: Output format (html, markdown, text, pdf)
            **scrape_options: Additional scraping options
            
        Returns:
            Scraped content data
            
        Raises:
            SteelAPIError: If scraping fails
        """
        # Use provided session or create a new one
        if session is None:
            session = self.create_session()
            session_created = True
        else:
            session_created = False
        
        try:
            # Set default format from config
            if format is None:
                format = self.config.default_format.value
            
            # Prepare scrape parameters
            # Note: Steel SDK scrape() method doesn't use session_id - it's a direct API call
            scrape_params = {
                "url": url,
                "format": [format] if isinstance(format, str) else format,  # Steel expects array
                **scrape_options
            }
            
            logger.info(f"Scraping URL: {url} (format: {format}) with session: {session.id}")
            
            # Perform scraping through Steel SDK
            # The session is managed separately from the scrape parameters
            result = self._client.scrape(**scrape_params)
            
            logger.info(f"Successfully scraped {url}")
            return result
            
        except Exception as e:
            if hasattr(e, "response"):
                raise handle_steel_api_error(e.response)
            else:
                raise SteelError(f"Failed to scrape {url}: {str(e)}", original_error=e)
        
        finally:
            # Release session if we created it
            if session_created:
                self.session_manager.release_session(session.id)
    
    @contextmanager
    def session_context(self, **session_options: Any):
        """Context manager for session lifecycle.
        
        Args:
            **session_options: Session creation options
            
        Yields:
            Steel session object
        """
        session = self.create_session(**session_options)
        try:
            yield session
        finally:
            self.session_manager.release_session(session.id)
    
    def cleanup_sessions(self) -> None:
        """Cleanup expired sessions."""
        expired = self.session_manager.cleanup_expired_sessions()
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
        
        # Release expired sessions from Steel API
        for session_id in expired:
            try:
                self._client.sessions.release(session_id)
            except Exception as e:
                logger.warning(f"Failed to release expired session {session_id}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics.
        
        Returns:
            Dictionary with client and session statistics
        """
        stats = {
            "config": {
                "api_timeout": self.config.api_timeout,
                "session_timeout": self.config.session_timeout,
                "use_proxy": self.config.use_proxy,
                "solve_captcha": self.config.solve_captcha,
                "stealth_mode": self.config.stealth_mode,
            },
            "sessions": self.session_manager.get_stats(),
        }
        
        return stats


class AsyncSteelClient:
    """Async version of Steel client with session management."""
    
    def __init__(self, config: Optional[SteelConfig] = None) -> None:
        """Initialize async Steel client.
        
        Args:
            config: Steel configuration (uses environment defaults if None)
        """
        self.config = config or SteelConfig.from_env()
        
        # Initialize Steel SDK async client
        try:
            self._client = AsyncSteel(steel_api_key=self.config.api_key)
        except Exception as e:
            raise SteelAuthenticationError(
                "Failed to initialize async Steel client. Check API key.",
                original_error=e,
            )
        
        # Session management
        self.session_manager = SteelSessionManager()
    
    async def create_session(
        self, 
        reuse_existing: bool = True,
        **session_options: Any
    ) -> Session:
        """Create or reuse a Steel browser session asynchronously.
        
        Args:
            reuse_existing: Whether to try reusing an existing session
            **session_options: Additional session options
            
        Returns:
            Steel session object
        """
        # Try to reuse existing session if requested
        if reuse_existing:
            async with self.session_manager._session_lock:
                existing_session = self.session_manager.get_available_session()
                if existing_session:
                    logger.info(f"Reusing existing session: {existing_session.id}")
                    return existing_session
        
        # Create new session
        try:
            options = self.config.to_session_options()
            options.update(session_options)
            
            logger.info("Creating new Steel session (async)...")
            session = await self._client.sessions.create(**options)
            
            # Add to session pool
            async with self.session_manager._session_lock:
                self.session_manager.add_session(session, reusable=reuse_existing)
            
            logger.info(f"Created Steel session (async): {session.id}")
            return session
            
        except Exception as e:
            await self.cleanup_sessions()
            
            if hasattr(e, "response"):
                raise handle_steel_api_error(e.response)
            else:
                raise SteelSessionError(
                    f"Failed to create Steel session: {str(e)}",
                    original_error=e,
                )
    
    async def release_session(self, session_id: str) -> None:
        """Release and cleanup Steel session asynchronously.
        
        Args:
            session_id: ID of session to release
        """
        try:
            await self._client.sessions.release(session_id)
            async with self.session_manager._session_lock:
                self.session_manager.remove_session(session_id)
            logger.info(f"Released Steel session (async): {session_id}")
            
        except Exception as e:
            logger.warning(f"Failed to release session {session_id}: {str(e)}")
            async with self.session_manager._session_lock:
                self.session_manager.remove_session(session_id)
    
    @asynccontextmanager
    async def session_context(self, **session_options: Any):
        """Async context manager for session lifecycle.
        
        Args:
            **session_options: Session creation options
            
        Yields:
            Steel session object
        """
        session = await self.create_session(**session_options)
        try:
            yield session
        finally:
            await self.release_session(session.id)
    
    async def cleanup_sessions(self) -> None:
        """Cleanup expired sessions asynchronously."""
        async with self.session_manager._session_lock:
            expired = self.session_manager.cleanup_expired_sessions()
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions (async)")
        
        # Release expired sessions from Steel API
        for session_id in expired:
            try:
                await self._client.sessions.release(session_id)
            except Exception as e:
                logger.warning(f"Failed to release expired session {session_id}: {e}")