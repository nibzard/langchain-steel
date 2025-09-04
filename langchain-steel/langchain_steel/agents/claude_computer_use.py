"""ABOUTME: Claude Computer Use integration for Steel browser automation.
ABOUTME: Provides browser automation using Claude's computer use capabilities with Steel infrastructure."""

import os
import time
import base64
import json
import logging
import asyncio
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from PIL import Image
from io import BytesIO
from playwright.sync_api import sync_playwright, Error as PlaywrightError
from playwright.async_api import async_playwright, Error as AsyncPlaywrightError
from steel import Steel
from steel.types import Session

from anthropic import Anthropic, RateLimitError, APITimeoutError
from anthropic.types.beta import BetaMessageParam
import random

logger = logging.getLogger(__name__)

# Model configurations for Claude Computer Use
MODEL_CONFIGS = {
    "claude-3-5-sonnet-20241022": {
        "tool_type": "computer_20241022",
        "beta_flag": "computer-use-2024-10-22",
        "description": "Claude 3.5 Sonnet (stable)"
    }
}

# Key mapping for Claude Computer Use to Playwright
CUA_KEY_TO_PLAYWRIGHT_KEY = {
    "/": "Divide",
    "\\": "Backslash",
    "alt": "Alt",
    "arrowdown": "ArrowDown",
    "arrowleft": "ArrowLeft",
    "arrowright": "ArrowRight",
    "arrowup": "ArrowUp",
    "backspace": "Backspace",
    "capslock": "CapsLock",
    "cmd": "Meta",
    "ctrl": "Control",
    "delete": "Delete",
    "end": "End",
    "enter": "Enter",
    "esc": "Escape",
    "home": "Home",
    "insert": "Insert",
    "option": "Alt",
    "pagedown": "PageDown",
    "pageup": "PageUp",
    "shift": "Shift",
    "space": " ",
    "super": "Meta",
    "tab": "Tab",
    "win": "Meta",
    "Return": "Enter",
    "KP_Enter": "Enter", 
    "Escape": "Escape",
    "BackSpace": "Backspace",
    "Delete": "Delete",
    "Tab": "Tab",
    "ISO_Left_Tab": "Shift+Tab",
    "Up": "ArrowUp",
    "Down": "ArrowDown",
    "Left": "ArrowLeft", 
    "Right": "ArrowRight",
    "Page_Up": "PageUp",
    "Page_Down": "PageDown",
    "Home": "Home",
    "End": "End",
    "Insert": "Insert",
    "F1": "F1", "F2": "F2", "F3": "F3", "F4": "F4",
    "F5": "F5", "F6": "F6", "F7": "F7", "F8": "F8",
    "F9": "F9", "F10": "F10", "F11": "F11", "F12": "F12",
    "Shift_L": "Shift", "Shift_R": "Shift",
    "Control_L": "Control", "Control_R": "Control", 
    "Alt_L": "Alt", "Alt_R": "Alt",
    "Meta_L": "Meta", "Meta_R": "Meta",
    "Super_L": "Meta", "Super_R": "Meta",
    "minus": "-",
    "equal": "=",
    "bracketleft": "[",
    "bracketright": "]",
    "semicolon": ";",
    "apostrophe": "'",
    "grave": "`",
    "comma": ",",
    "period": ".",
    "slash": "/",
}

SYSTEM_PROMPT = """You are an expert browser automation assistant operating in an iterative execution loop. Your goal is to efficiently complete tasks using a Chrome browser with full internet access.

<CAPABILITIES>
* You control a Chrome browser tab and can navigate to any website
* You can click, type, scroll, take screenshots, and interact with web elements  
* You have full internet access and can visit any public website
* You can read content, fill forms, search for information, and perform complex multi-step tasks
* After each action, you receive a screenshot showing the current state

<COORDINATE_SYSTEM>
* The browser viewport has specific dimensions that you must respect
* All coordinates (x, y) must be within the viewport bounds
* X coordinates must be between 0 and the display width (inclusive)
* Y coordinates must be between 0 and the display height (inclusive)

<AUTONOMOUS_EXECUTION>
* Work completely independently - make decisions and act immediately without asking questions
* Never request clarification, present options, or ask for permission
* Make intelligent assumptions based on task context
* Take immediate action rather than explaining what you might do
* When the task objective is achieved, immediately declare "TASK_COMPLETED:" - do not provide commentary

<COMPLETION_CRITERIA>
* MANDATORY: When you complete the task, your final message MUST start with "TASK_COMPLETED: [brief summary]"
* MANDATORY: If technical issues prevent completion, your final message MUST start with "TASK_FAILED: [reason]"  
* Do not write anything after completing the task except the required completion message

<CRITICAL_REQUIREMENTS>
* This is fully automated execution - work completely independently
* Start by taking a screenshot to understand the current state
* Navigate to the most relevant website for the task without asking
* Always respect coordinate boundaries - invalid coordinates will fail
* Focus on the explicit task given, not implied or potential follow-up tasks

Remember: Be thorough but focused. Complete the specific task requested efficiently and provide clear results."""


def _is_running_in_event_loop() -> bool:
    """Check if we're running in an asyncio event loop."""
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


def _handle_rate_limit_error(attempt: int, max_retries: int = 10) -> Optional[float]:
    """Handle rate limit errors with improved exponential backoff.
    
    Args:
        attempt: Current attempt number (0-indexed)
        max_retries: Maximum number of retries
        
    Returns:
        Delay in seconds, or None if max retries exceeded
    """
    if attempt >= max_retries:
        return None
    
    # More conservative exponential backoff with longer initial delays
    # Progressive delays: 1s, 2s, 4s, 8s, 15s, 30s, 60s, 90s, 120s, 180s
    base_delays = [1, 2, 4, 8, 15, 30, 60, 90, 120, 180]
    base_delay = base_delays[min(attempt, len(base_delays) - 1)]
    
    # Add random jitter to prevent thundering herd
    jitter = random.uniform(0.2, 0.8)
    delay = base_delay + jitter
    
    logger.warning(f"Rate limit hit, retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retries})")
    return delay


class SteelBrowserSession:
    """Manages Steel browser session with Playwright integration."""

    def __init__(
        self,
        steel_client: Steel,
        width: int = 1024,
        height: int = 768,
        use_proxy: bool = False,
        solve_captcha: bool = False,
        session_timeout: int = 900000,
        start_url: str = "https://www.google.com",
    ):
        self.steel_client = steel_client
        self.dimensions = (width, height)
        self.use_proxy = use_proxy
        self.solve_captcha = solve_captcha
        self.session_timeout = session_timeout
        self.start_url = start_url
        self.session: Optional[Session] = None
        self._playwright = None
        self._browser = None
        self._page = None
        self._last_mouse_position = None
        self._last_keepalive = 0
        self._keepalive_interval = 30  # seconds

    def get_dimensions(self) -> Tuple[int, int]:
        return self.dimensions

    def get_current_url(self) -> str:
        try:
            return self._page.url if self._page and not self._page.is_closed() else ""
        except Exception:
            return ""
    
    def _ensure_page_ready(self) -> bool:
        """Ensure the page is ready for operations."""
        try:
            if not self._page or self._page.is_closed():
                logger.warning("Page is closed, attempting to get a new page")
                if self._browser and len(self._browser.contexts) > 0:
                    context = self._browser.contexts[0]
                    if len(context.pages) > 0:
                        self._page = context.pages[0]
                    else:
                        self._page = context.new_page()
                        width, height = self.dimensions
                        self._page.set_viewport_size({"width": width, "height": height})
                    logger.info("Successfully obtained new page")
                    return True
                else:
                    logger.error("No browser context available")
                    return False
            
            # Test basic page functionality
            url = self._page.url
            logger.debug(f"Page ready check passed, URL: {url}")
            return True
            
        except Exception as e:
            logger.error(f"Page readiness check failed: {e}")
            return False

    def _validate_connection(self) -> bool:
        """Validate that the browser connection is stable and ready."""
        try:
            if not self._browser or not self._page or self._page.is_closed():
                return False
            
            # Test basic page operations
            url = self._page.url
            logger.debug(f"Page URL: {url}")
            return True
        except Exception as e:
            logger.warning(f"Connection validation failed: {e}")
            return False
    
    def _connect_to_browser_with_retry(self, steel_api_key: str, max_retries: int = 3) -> bool:
        """Connect to Steel browser with retry logic."""
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to Steel browser via CDP (attempt {attempt + 1}/{max_retries}): {self.session.websocket_url}")
                browser = self._playwright.chromium.connect_over_cdp(
                    f"{self.session.websocket_url}&apiKey={steel_api_key}",
                    timeout=60000
                )
                self._browser = browser
                
                # Wait a moment for the connection to stabilize
                time.sleep(1.0)
                
                context = browser.contexts[0]
                logger.info(f"Connected to browser context with {len(context.pages)} pages")

                if len(context.pages) == 0:
                    logger.warning("No pages available in browser context, creating new page")
                    self._page = context.new_page()
                else:
                    self._page = context.pages[0]
                
                # Validate the connection
                if self._validate_connection():
                    logger.info("Browser connection validated successfully")
                    return True
                else:
                    logger.warning(f"Connection validation failed on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        time.sleep(2.0)  # Wait before retry
                        continue
                    
            except Exception as e:
                logger.warning(f"Browser connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2.0)  # Wait before retry
                    continue
                else:
                    raise e
        
        return False
    
    def _safe_navigate_to_start_url(self) -> None:
        """Safely navigate to start URL with comprehensive error recovery."""
        logger.info(f"Navigating to start URL: {self.start_url}")
        
        # First, ensure we have a valid page
        if not self._ensure_page_ready():
            logger.error("Cannot navigate - page is not ready")
            return
        
        # Try primary navigation
        try:
            self._page.goto(self.start_url, wait_until="domcontentloaded", timeout=30000)
            logger.info(f"Successfully navigated to: {self._page.url}")
            return
        except Exception as nav_error:
            logger.warning(f"Primary navigation to {self.start_url} failed: {nav_error}")
            
            # Check if page is still valid after navigation failure
            if not self._ensure_page_ready():
                logger.warning("Page became invalid after navigation failure")
                return
        
        # Try fallback navigation strategies
        fallback_urls = [
            "https://www.google.com/?hl=en-GB",  # Simplified Google
            "https://example.com",  # Minimal test site
            "data:text/html,<html><body><h1>Ready for automation</h1></body></html>"  # Data URI
        ]
        
        for fallback_url in fallback_urls:
            try:
                logger.info(f"Trying fallback navigation to: {fallback_url}")
                self._page.goto(fallback_url, wait_until="domcontentloaded", timeout=15000)
                logger.info(f"Successfully navigated to fallback: {self._page.url}")
                return
            except Exception as fallback_error:
                logger.warning(f"Fallback navigation to {fallback_url} failed: {fallback_error}")
                # Ensure page is still ready for next attempt
                if not self._ensure_page_ready():
                    logger.error("Page became invalid, cannot continue navigation attempts")
                    return
                continue
        
        # If all navigation attempts failed, log and continue
        logger.info("All navigation attempts failed - continuing with current page")
        logger.info("Claude will be able to navigate manually during task execution")

    def __enter__(self):
        width, height = self.dimensions
        session_params = {
            "use_proxy": self.use_proxy,
            "solve_captcha": self.solve_captcha,
            "api_timeout": self.session_timeout,
            "block_ads": True,
            "dimensions": {"width": width, "height": height}
        }
        
        try:
            self.session = self.steel_client.sessions.create(**session_params)
            logger.info(f"Steel Session created: {self.session.session_viewer_url}")

            self._playwright = sync_playwright().start()
            
            # Get Steel API key from environment or Steel client
            steel_api_key = os.getenv("STEEL_API_KEY")
            if not steel_api_key:
                steel_api_key = getattr(self.steel_client, '_api_key', None)
            
            if not steel_api_key:
                raise ValueError("STEEL_API_KEY not found in environment or client")
            
            # Use retry logic for browser connection
            if not self._connect_to_browser_with_retry(steel_api_key):
                raise RuntimeError("Failed to establish stable browser connection after retries")
            
            # Add page error handler to suppress non-critical errors
            def handle_page_error(error):
                try:
                    error_message = str(error)
                    if "Cannot redefine property" in error_message:
                        logger.debug(f"Suppressing non-critical page error: {error}")
                    else:
                        logger.warning(f"Page error: {error}")
                except Exception as handler_error:
                    logger.warning(f"Error in page error handler: {handler_error}")
            
            self._page.on("pageerror", handle_page_error)
            
            # Set viewport size with error handling
            try:
                self._page.set_viewport_size({"width": width, "height": height})
                logger.info(f"Viewport set to {width}x{height}")
            except Exception as viewport_error:
                logger.warning(f"Failed to set viewport size: {viewport_error}")
                # Continue anyway - this isn't critical
            
            # Navigate to start URL with enhanced error recovery
            self._safe_navigate_to_start_url()
            
            return self
        except Exception as e:
            logger.error(f"Failed to create Steel browser session: {e}")
            # Clean up partially created resources
            if hasattr(self, '_browser') and self._browser:
                try:
                    self._browser.close()
                except:
                    pass
            if hasattr(self, '_playwright') and self._playwright:
                try:
                    self._playwright.stop()
                except:
                    pass
            if hasattr(self, 'session') and self.session:
                try:
                    self.steel_client.sessions.release(self.session.id)
                except:
                    pass
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.info("Cleaning up Steel browser session...")
        
        # Close page first
        if hasattr(self, '_page') and self._page:
            try:
                self._page.close()
                logger.info("Page closed")
            except Exception as e:
                logger.warning(f"Error closing page: {e}")
        
        # Close browser 
        if hasattr(self, '_browser') and self._browser:
            try:
                self._browser.close()
                logger.info("Browser closed")
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
        
        # Stop playwright
        if hasattr(self, '_playwright') and self._playwright:
            try:
                self._playwright.stop()
                logger.info("Playwright stopped")
            except Exception as e:
                logger.warning(f"Error stopping playwright: {e}")

        # Release Steel session last
        if hasattr(self, 'session') and self.session:
            try:
                logger.info("Releasing Steel session...")
                self.steel_client.sessions.release(self.session.id)
                logger.info(f"Session completed. View replay at {self.session.session_viewer_url}")
            except Exception as e:
                logger.warning(f"Error releasing Steel session: {e}")
    
    def _perform_keepalive_if_needed(self) -> None:
        """Perform keepalive check if enough time has passed."""
        current_time = time.time()
        if current_time - self._last_keepalive > self._keepalive_interval:
            try:
                # Simple keepalive - check if page is still responsive
                if self._page and not self._page.is_closed():
                    url = self._page.url
                    logger.debug(f"Keepalive check passed - URL: {url}")
                    self._last_keepalive = current_time
                else:
                    logger.warning("Keepalive check failed - page is closed")
                    self._last_keepalive = current_time
            except Exception as e:
                logger.warning(f"Keepalive check failed: {e}")
                self._last_keepalive = current_time

    def screenshot(self) -> str:
        """Take a screenshot and return base64 encoded image."""
        # Perform keepalive check if needed
        self._perform_keepalive_if_needed()
        
        # Ensure page is ready for screenshot
        if not self._ensure_page_ready():
            raise RuntimeError("Browser session is not ready for screenshot")
        
        try:
            width, height = self.dimensions
            png_bytes = self._page.screenshot(
                full_page=False,
                clip={"x": 0, "y": 0, "width": width, "height": height}
            )
            return base64.b64encode(png_bytes).decode("utf-8")
        except PlaywrightError as error:
            logger.error(f"Screenshot failed, trying CDP fallback: {error}")
            try:
                cdp_session = self._page.context.new_cdp_session(self._page)
                result = cdp_session.send(
                    "Page.captureScreenshot", {"format": "png", "fromSurface": False}
                )
                return result["data"]
            except PlaywrightError as cdp_error:
                logger.error(f"CDP screenshot also failed: {cdp_error}")
                raise error

    def validate_and_get_coordinates(self, coordinate):
        """Validate and get coordinates like the canonical example."""
        if not isinstance(coordinate, (list, tuple)) or len(coordinate) != 2:
            raise ValueError(f"{coordinate} must be a tuple or list of length 2")
        if not all(isinstance(i, int) and i >= 0 for i in coordinate):
            raise ValueError(f"{coordinate} must be a tuple/list of non-negative ints")
        
        x, y = self.clamp_coordinates(coordinate[0], coordinate[1])
        return x, y

    def clamp_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """Clamp coordinates to viewport bounds."""
        width, height = self.dimensions
        clamped_x = max(0, min(x, width - 1))
        clamped_y = max(0, min(y, height - 1))
        
        if x != clamped_x or y != clamped_y:
            logger.warning(f"Coordinate clamped: ({x}, {y}) → ({clamped_x}, {clamped_y})")
        
        return clamped_x, clamped_y

    def execute_computer_action(
        self, 
        action: str, 
        text: str = None,
        coordinate = None,
        scroll_direction: str = None,
        scroll_amount: int = None,
        duration = None,
        key: str = None,
        **kwargs
    ) -> str:
        """Execute a computer action and return screenshot."""
        
        # Check if browser session is still active before action
        if not self._page or self._page.is_closed():
            raise RuntimeError("Browser session has been closed")
        
        try:
            if action in ("left_mouse_down", "left_mouse_up"):
                if coordinate is not None:
                    raise ValueError(f"coordinate is not accepted for {action}")
                
                if action == "left_mouse_down":
                    self._page.mouse.down()
                elif action == "left_mouse_up":
                    self._page.mouse.up()
                
                return self.screenshot()
        
        except PlaywrightError as e:
            if "Target page, context or browser has been closed" in str(e):
                raise RuntimeError(f"Browser session closed during action '{action}': {e}")
            else:
                raise e
        
        if action == "scroll":
            if scroll_direction is None or scroll_direction not in ("up", "down", "left", "right"):
                raise ValueError("scroll_direction must be 'up', 'down', 'left', or 'right'")
            if scroll_amount is None or not isinstance(scroll_amount, int) or scroll_amount < 0:
                raise ValueError("scroll_amount must be a non-negative int")
            
            try:
                if coordinate is not None:
                    x, y = self.validate_and_get_coordinates(coordinate)
                    self._page.mouse.move(x, y)
                    self._last_mouse_position = (x, y)
                
                if text:
                    modifier_key = text
                    if modifier_key in CUA_KEY_TO_PLAYWRIGHT_KEY:
                        modifier_key = CUA_KEY_TO_PLAYWRIGHT_KEY[modifier_key]
                    self._page.keyboard.down(modifier_key)
                
                scroll_mapping = {
                    "down": (0, 100 * scroll_amount),
                    "up": (0, -100 * scroll_amount),
                    "right": (100 * scroll_amount, 0),
                    "left": (-100 * scroll_amount, 0)
                }
                delta_x, delta_y = scroll_mapping[scroll_direction]
                self._page.mouse.wheel(delta_x, delta_y)
                
                if text:
                    self._page.keyboard.up(modifier_key)
                
                return self.screenshot()
                
            except PlaywrightError as e:
                if "Target page, context or browser has been closed" in str(e):
                    raise RuntimeError(f"Browser session closed during scroll action: {e}")
                else:
                    raise e
        
        if action in ("hold_key", "wait"):
            if duration is None or not isinstance(duration, (int, float)):
                raise ValueError("duration must be a number")
            if duration < 0:
                raise ValueError("duration must be non-negative")
            if duration > 100:
                raise ValueError("duration is too long")
            
            if action == "hold_key":
                if text is None:
                    raise ValueError("text is required for hold_key")
                
                hold_key = text
                if hold_key in CUA_KEY_TO_PLAYWRIGHT_KEY:
                    hold_key = CUA_KEY_TO_PLAYWRIGHT_KEY[hold_key]
                
                self._page.keyboard.down(hold_key)
                time.sleep(duration)
                self._page.keyboard.up(hold_key)
                
            elif action == "wait":
                time.sleep(duration)
            
            return self.screenshot()
        
        if action in ("left_click", "right_click", "double_click", "triple_click", "middle_click"):
            if text is not None:
                raise ValueError(f"text is not accepted for {action}")
            
            if coordinate is not None:
                x, y = self.validate_and_get_coordinates(coordinate)
                self._page.mouse.move(x, y)
                self._last_mouse_position = (x, y)
                click_x, click_y = x, y
            elif self._last_mouse_position:
                click_x, click_y = self._last_mouse_position
            else:
                width, height = self.dimensions
                click_x, click_y = width // 2, height // 2
            
            if key:
                modifier_key = key
                if modifier_key in CUA_KEY_TO_PLAYWRIGHT_KEY:
                    modifier_key = CUA_KEY_TO_PLAYWRIGHT_KEY[modifier_key]
                self._page.keyboard.down(modifier_key)
            
            if action == "left_click":
                self._page.mouse.click(click_x, click_y)
            elif action == "right_click":
                self._page.mouse.click(click_x, click_y, button="right")
            elif action == "double_click":
                self._page.mouse.dblclick(click_x, click_y)
            elif action == "triple_click":
                for _ in range(3):
                    self._page.mouse.click(click_x, click_y)
            elif action == "middle_click":
                self._page.mouse.click(click_x, click_y, button="middle")
            
            if key:
                self._page.keyboard.up(modifier_key)
            
            return self.screenshot()
        
        if action in ("mouse_move", "left_click_drag"):
            if coordinate is None:
                raise ValueError(f"coordinate is required for {action}")
            if text is not None:
                raise ValueError(f"text is not accepted for {action}")
            
            x, y = self.validate_and_get_coordinates(coordinate)
            
            if action == "mouse_move":
                self._page.mouse.move(x, y)
                self._last_mouse_position = (x, y)
            elif action == "left_click_drag":
                self._page.mouse.down()
                self._page.mouse.move(x, y)
                self._page.mouse.up()
                self._last_mouse_position = (x, y)
            
            return self.screenshot()
        
        if action in ("key", "type"):
            if text is None:
                raise ValueError(f"text is required for {action}")
            if coordinate is not None:
                raise ValueError(f"coordinate is not accepted for {action}")
            
            if action == "key":
                press_key = text
                
                if "+" in press_key:
                    key_parts = press_key.split("+")
                    modifier_keys = key_parts[:-1]
                    main_key = key_parts[-1]
                    
                    playwright_modifiers = []
                    for mod in modifier_keys:
                        if mod.lower() in ("ctrl", "control"):
                            playwright_modifiers.append("Control")
                        elif mod.lower() in ("shift",):
                            playwright_modifiers.append("Shift")
                        elif mod.lower() in ("alt", "option"):
                            playwright_modifiers.append("Alt")
                        elif mod.lower() in ("cmd", "meta", "super"):
                            playwright_modifiers.append("Meta")
                        else:
                            playwright_modifiers.append(mod)
                    
                    if main_key in CUA_KEY_TO_PLAYWRIGHT_KEY:
                        main_key = CUA_KEY_TO_PLAYWRIGHT_KEY[main_key]
                    
                    press_key = "+".join(playwright_modifiers + [main_key])
                else:
                    if press_key in CUA_KEY_TO_PLAYWRIGHT_KEY:
                        press_key = CUA_KEY_TO_PLAYWRIGHT_KEY[press_key]
                
                self._page.keyboard.press(press_key)
            elif action == "type":
                # Type with chunking for better reliability
                TYPING_DELAY_MS = 12
                TYPING_GROUP_SIZE = 50
                for chunk in [text[i:i + TYPING_GROUP_SIZE] for i in range(0, len(text), TYPING_GROUP_SIZE)]:
                    self._page.keyboard.type(chunk, delay=TYPING_DELAY_MS)
                    time.sleep(0.01)
            
            return self.screenshot()
        
        if action in ("screenshot", "cursor_position"):
            if text is not None:
                raise ValueError(f"text is not accepted for {action}")
            if coordinate is not None:
                raise ValueError(f"coordinate is not accepted for {action}")
            
            return self.screenshot()
        
        raise ValueError(f"Invalid action: {action}")


class AsyncSteelBrowserSession:
    """Async version of Steel browser session with Playwright integration."""

    def __init__(
        self,
        steel_client: Steel,
        width: int = 1024,
        height: int = 768,
        use_proxy: bool = False,
        solve_captcha: bool = False,
        session_timeout: int = 900000,
        start_url: str = "https://www.google.com",
    ):
        self.steel_client = steel_client
        self.dimensions = (width, height)
        self.use_proxy = use_proxy
        self.solve_captcha = solve_captcha
        self.session_timeout = session_timeout
        self.start_url = start_url
        self.session: Optional[Session] = None
        self._playwright = None
        self._browser = None
        self._page = None
        self._last_mouse_position = None
        self._last_keepalive = 0
        self._keepalive_interval = 30  # seconds

    def get_dimensions(self) -> Tuple[int, int]:
        return self.dimensions

    def get_current_url(self) -> str:
        return self._page.url if self._page else ""

    async def __aenter__(self):
        width, height = self.dimensions
        session_params = {
            "use_proxy": self.use_proxy,
            "solve_captcha": self.solve_captcha,
            "api_timeout": self.session_timeout,
            "block_ads": True,
            "dimensions": {"width": width, "height": height}
        }
        
        try:
            self.session = self.steel_client.sessions.create(**session_params)
            logger.info(f"Steel Session created: {self.session.session_viewer_url}")

            self._playwright = await async_playwright().start()
            
            # Get Steel API key from environment or Steel client
            steel_api_key = os.getenv("STEEL_API_KEY")
            if not steel_api_key:
                steel_api_key = getattr(self.steel_client, '_api_key', None)
            
            if not steel_api_key:
                raise ValueError("STEEL_API_KEY not found in environment or client")
            
            logger.info(f"Connecting to Steel browser via CDP: {self.session.websocket_url}")
            browser = await self._playwright.chromium.connect_over_cdp(
                f"{self.session.websocket_url}&apiKey={steel_api_key}",
                timeout=60000
            )
            self._browser = browser
            context = browser.contexts[0]
            logger.info(f"Connected to browser context with {len(context.pages)} pages")

            self._page = context.pages[0]
            await self._page.set_viewport_size({"width": width, "height": height})
            
            # Add page error handler to suppress non-critical errors
            def handle_page_error(error):
                try:
                    error_message = str(error)
                    if "Cannot redefine property" in error_message:
                        logger.debug(f"Suppressing non-critical page error: {error}")
                    else:
                        logger.warning(f"Page error: {error}")
                except Exception as handler_error:
                    logger.warning(f"Error in page error handler: {handler_error}")
            
            self._page.on("pageerror", handle_page_error)
            
            # Navigate to start URL with better error handling
            logger.info(f"Navigating to start URL: {self.start_url}")
            try:
                await self._page.goto(self.start_url, wait_until="domcontentloaded", timeout=30000)
                logger.info(f"Successfully navigated to: {self._page.url}")
            except Exception as nav_error:
                logger.warning(f"Navigation to {self.start_url} failed: {nav_error}")
                # Try a simple fallback URL
                try:
                    await self._page.goto("data:text/html,<html><body><h1>Ready for automation</h1></body></html>", wait_until="domcontentloaded")
                    logger.info("Using fallback HTML page")
                except Exception:
                    logger.info("Continuing with current page - Claude can navigate manually")
            
            return self
        except Exception as e:
            logger.error(f"Failed to create Steel browser session: {e}")
            # Clean up partially created resources
            if hasattr(self, '_browser') and self._browser:
                try:
                    await self._browser.close()
                except:
                    pass
            if hasattr(self, '_playwright') and self._playwright:
                try:
                    await self._playwright.stop()
                except:
                    pass
            if hasattr(self, 'session') and self.session:
                try:
                    self.steel_client.sessions.release(self.session.id)
                except:
                    pass
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        logger.info("Cleaning up Steel browser session...")
        
        # Close page first
        if hasattr(self, '_page') and self._page:
            try:
                await self._page.close()
                logger.info("Page closed")
            except Exception as e:
                logger.warning(f"Error closing page: {e}")
        
        # Close browser 
        if hasattr(self, '_browser') and self._browser:
            try:
                await self._browser.close()
                logger.info("Browser closed")
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
        
        # Stop playwright
        if hasattr(self, '_playwright') and self._playwright:
            try:
                await self._playwright.stop()
                logger.info("Playwright stopped")
            except Exception as e:
                logger.warning(f"Error stopping playwright: {e}")

        # Release Steel session last
        if hasattr(self, 'session') and self.session:
            try:
                logger.info("Releasing Steel session...")
                self.steel_client.sessions.release(self.session.id)
                logger.info(f"Session completed. View replay at {self.session.session_viewer_url}")
            except Exception as e:
                logger.warning(f"Error releasing Steel session: {e}")

    async def screenshot(self) -> str:
        """Take a screenshot and return base64 encoded image."""
        try:
            width, height = self.dimensions
            png_bytes = await self._page.screenshot(
                full_page=False,
                clip={"x": 0, "y": 0, "width": width, "height": height}
            )
            return base64.b64encode(png_bytes).decode("utf-8")
        except AsyncPlaywrightError as error:
            logger.error(f"Screenshot failed, trying CDP fallback: {error}")
            try:
                cdp_session = await self._page.context.new_cdp_session(self._page)
                result = await cdp_session.send(
                    "Page.captureScreenshot", {"format": "png", "fromSurface": False}
                )
                return result["data"]
            except AsyncPlaywrightError as cdp_error:
                logger.error(f"CDP screenshot also failed: {cdp_error}")
                raise error

    def validate_and_get_coordinates(self, coordinate):
        """Validate and get coordinates like the canonical example."""
        if not isinstance(coordinate, (list, tuple)) or len(coordinate) != 2:
            raise ValueError(f"{coordinate} must be a tuple or list of length 2")
        if not all(isinstance(i, int) and i >= 0 for i in coordinate):
            raise ValueError(f"{coordinate} must be a tuple/list of non-negative ints")
        
        x, y = self.clamp_coordinates(coordinate[0], coordinate[1])
        return x, y

    def clamp_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """Clamp coordinates to viewport bounds."""
        width, height = self.dimensions
        clamped_x = max(0, min(x, width - 1))
        clamped_y = max(0, min(y, height - 1))
        
        if x != clamped_x or y != clamped_y:
            logger.warning(f"Coordinate clamped: ({x}, {y}) → ({clamped_x}, {clamped_y})")
        
        return clamped_x, clamped_y

    async def execute_computer_action(
        self, 
        action: str, 
        text: str = None,
        coordinate = None,
        scroll_direction: str = None,
        scroll_amount: int = None,
        duration = None,
        key: str = None,
        **kwargs
    ) -> str:
        """Execute a computer action and return screenshot."""
        
        # Check if browser session is still active before action
        if not self._page or self._page.is_closed():
            raise RuntimeError("Browser session has been closed")
        
        try:
            if action in ("left_mouse_down", "left_mouse_up"):
                if coordinate is not None:
                    raise ValueError(f"coordinate is not accepted for {action}")
                
                if action == "left_mouse_down":
                    await self._page.mouse.down()
                elif action == "left_mouse_up":
                    await self._page.mouse.up()
        
        except AsyncPlaywrightError as e:
            if "Target page, context or browser has been closed" in str(e):
                raise RuntimeError(f"Browser session closed during action '{action}': {e}")
            else:
                raise e
            
            return await self.screenshot()
        
        if action == "scroll":
            if scroll_direction is None or scroll_direction not in ("up", "down", "left", "right"):
                raise ValueError("scroll_direction must be 'up', 'down', 'left', or 'right'")
            if scroll_amount is None or not isinstance(scroll_amount, int) or scroll_amount < 0:
                raise ValueError("scroll_amount must be a non-negative int")
            
            if coordinate is not None:
                x, y = self.validate_and_get_coordinates(coordinate)
                await self._page.mouse.move(x, y)
                self._last_mouse_position = (x, y)
            
            if text:
                modifier_key = text
                if modifier_key in CUA_KEY_TO_PLAYWRIGHT_KEY:
                    modifier_key = CUA_KEY_TO_PLAYWRIGHT_KEY[modifier_key]
                await self._page.keyboard.down(modifier_key)
            
            scroll_mapping = {
                "down": (0, 100 * scroll_amount),
                "up": (0, -100 * scroll_amount),
                "right": (100 * scroll_amount, 0),
                "left": (-100 * scroll_amount, 0)
            }
            delta_x, delta_y = scroll_mapping[scroll_direction]
            await self._page.mouse.wheel(delta_x, delta_y)
            
            if text:
                await self._page.keyboard.up(modifier_key)
            
            return await self.screenshot()
        
        if action in ("hold_key", "wait"):
            if duration is None or not isinstance(duration, (int, float)):
                raise ValueError("duration must be a number")
            if duration < 0:
                raise ValueError("duration must be non-negative")
            if duration > 100:
                raise ValueError("duration is too long")
            
            if action == "hold_key":
                if text is None:
                    raise ValueError("text is required for hold_key")
                
                hold_key = text
                if hold_key in CUA_KEY_TO_PLAYWRIGHT_KEY:
                    hold_key = CUA_KEY_TO_PLAYWRIGHT_KEY[hold_key]
                
                await self._page.keyboard.down(hold_key)
                await asyncio.sleep(duration)
                await self._page.keyboard.up(hold_key)
                
            elif action == "wait":
                await asyncio.sleep(duration)
            
            return await self.screenshot()
        
        if action in ("left_click", "right_click", "double_click", "triple_click", "middle_click"):
            if text is not None:
                raise ValueError(f"text is not accepted for {action}")
            
            if coordinate is not None:
                x, y = self.validate_and_get_coordinates(coordinate)
                await self._page.mouse.move(x, y)
                self._last_mouse_position = (x, y)
                click_x, click_y = x, y
            elif self._last_mouse_position:
                click_x, click_y = self._last_mouse_position
            else:
                width, height = self.dimensions
                click_x, click_y = width // 2, height // 2
            
            if key:
                modifier_key = key
                if modifier_key in CUA_KEY_TO_PLAYWRIGHT_KEY:
                    modifier_key = CUA_KEY_TO_PLAYWRIGHT_KEY[modifier_key]
                await self._page.keyboard.down(modifier_key)
            
            if action == "left_click":
                await self._page.mouse.click(click_x, click_y)
            elif action == "right_click":
                await self._page.mouse.click(click_x, click_y, button="right")
            elif action == "double_click":
                await self._page.mouse.dblclick(click_x, click_y)
            elif action == "triple_click":
                for _ in range(3):
                    await self._page.mouse.click(click_x, click_y)
            elif action == "middle_click":
                await self._page.mouse.click(click_x, click_y, button="middle")
            
            if key:
                await self._page.keyboard.up(modifier_key)
            
            return await self.screenshot()
        
        if action in ("mouse_move", "left_click_drag"):
            if coordinate is None:
                raise ValueError(f"coordinate is required for {action}")
            if text is not None:
                raise ValueError(f"text is not accepted for {action}")
            
            x, y = self.validate_and_get_coordinates(coordinate)
            
            if action == "mouse_move":
                await self._page.mouse.move(x, y)
                self._last_mouse_position = (x, y)
            elif action == "left_click_drag":
                await self._page.mouse.down()
                await self._page.mouse.move(x, y)
                await self._page.mouse.up()
                self._last_mouse_position = (x, y)
            
            return await self.screenshot()
        
        if action in ("key", "type"):
            if text is None:
                raise ValueError(f"text is required for {action}")
            if coordinate is not None:
                raise ValueError(f"coordinate is not accepted for {action}")
            
            if action == "key":
                press_key = text
                
                if "+" in press_key:
                    key_parts = press_key.split("+")
                    modifier_keys = key_parts[:-1]
                    main_key = key_parts[-1]
                    
                    playwright_modifiers = []
                    for mod in modifier_keys:
                        if mod.lower() in ("ctrl", "control"):
                            playwright_modifiers.append("Control")
                        elif mod.lower() in ("shift",):
                            playwright_modifiers.append("Shift")
                        elif mod.lower() in ("alt", "option"):
                            playwright_modifiers.append("Alt")
                        elif mod.lower() in ("cmd", "meta", "super"):
                            playwright_modifiers.append("Meta")
                        else:
                            playwright_modifiers.append(mod)
                    
                    if main_key in CUA_KEY_TO_PLAYWRIGHT_KEY:
                        main_key = CUA_KEY_TO_PLAYWRIGHT_KEY[main_key]
                    
                    press_key = "+".join(playwright_modifiers + [main_key])
                else:
                    if press_key in CUA_KEY_TO_PLAYWRIGHT_KEY:
                        press_key = CUA_KEY_TO_PLAYWRIGHT_KEY[press_key]
                
                await self._page.keyboard.press(press_key)
            elif action == "type":
                # Type with chunking for better reliability
                TYPING_DELAY_MS = 12
                TYPING_GROUP_SIZE = 50
                for chunk in [text[i:i + TYPING_GROUP_SIZE] for i in range(0, len(text), TYPING_GROUP_SIZE)]:
                    await self._page.keyboard.type(chunk, delay=TYPING_DELAY_MS)
                    await asyncio.sleep(0.01)
            
            return await self.screenshot()
        
        if action in ("screenshot", "cursor_position"):
            if text is not None:
                raise ValueError(f"text is not accepted for {action}")
            if coordinate is not None:
                raise ValueError(f"coordinate is not accepted for {action}")
            
            return await self.screenshot()
        
        raise ValueError(f"Invalid action: {action}")


class ClaudeComputerUseAgent:
    """Claude Computer Use agent for browser automation."""

    def __init__(
        self, 
        anthropic_api_key: str,
        browser_session: SteelBrowserSession,
        model: str = "claude-3-5-sonnet-20241022"
    ):
        self.client = Anthropic(api_key=anthropic_api_key)
        self.browser_session = browser_session
        self.model = model
        self.messages: List[BetaMessageParam] = []
        self._last_screenshot_cache = None
        self._screenshot_cache_timestamp = 0
        self._cache_duration = 1.0  # Cache screenshots for 1 second
        
        if model not in MODEL_CONFIGS:
            raise ValueError(f"Unsupported model: {model}. Available: {list(MODEL_CONFIGS.keys())}")
        
        self.model_config = MODEL_CONFIGS[model]
        
        width, height = browser_session.get_dimensions()
        self.viewport_width = width
        self.viewport_height = height
        
        self.system_prompt = SYSTEM_PROMPT.replace(
            '<COORDINATE_SYSTEM>',
            f'<COORDINATE_SYSTEM>\n* The browser viewport dimensions are {width}x{height} pixels\n* The browser viewport has specific dimensions that you must respect'
        )
        
        self.tools = [{
            "type": self.model_config["tool_type"],
            "name": "computer",
            "display_width_px": width,
            "display_height_px": height,
            "display_number": 1,
        }]

    def _get_cached_screenshot(self) -> Optional[str]:
        """Get cached screenshot if still valid."""
        current_time = time.time()
        if (self._last_screenshot_cache and 
            current_time - self._screenshot_cache_timestamp < self._cache_duration):
            return self._last_screenshot_cache
        return None
    
    def _cache_screenshot(self, screenshot: str) -> None:
        """Cache a screenshot with timestamp."""
        self._last_screenshot_cache = screenshot
        self._screenshot_cache_timestamp = time.time()
        
    def _get_screenshot_with_cache(self, force_new: bool = False) -> str:
        """Get screenshot with caching to reduce redundant captures."""
        if not force_new:
            cached = self._get_cached_screenshot()
            if cached:
                logger.debug("Using cached screenshot")
                return cached
                
        screenshot = self.browser_session.screenshot()
        self._cache_screenshot(screenshot)
        return screenshot

    def execute_task(self, task: str, max_iterations: int = 30) -> Dict[str, Any]:
        """Execute a browser automation task using Claude Computer Use."""
        
        logger.info(f"Executing task: {task}")
        
        input_items = [{"role": "user", "content": task}]
        new_items = []
        iterations = 0
        
        while iterations < max_iterations:
            iterations += 1
            
            # Handle rate limiting with retry logic
            retry_attempt = 0
            response = None
            
            while retry_attempt < 10:  # Max 10 retry attempts per iteration
                try:
                    response = self.client.beta.messages.create(
                        model=self.model,
                        max_tokens=4096,
                        system=self.system_prompt,
                        messages=input_items + new_items,
                        tools=self.tools,
                        betas=[self.model_config["beta_flag"]]
                    )
                    break  # Success, exit retry loop
                    
                except (RateLimitError, APITimeoutError) as rate_error:
                    delay = _handle_rate_limit_error(retry_attempt)
                    if delay is None:
                        logger.error(f"Max retries exceeded for rate limiting: {rate_error}")
                        return {
                            "success": False,
                            "result": f"Rate limit exceeded after retries: {str(rate_error)}",
                            "iterations": iterations,
                            "final_url": self.browser_session.get_current_url()
                        }
                    
                    time.sleep(delay)
                    retry_attempt += 1
                    continue
                    
                except Exception as other_error:
                    # Handle other errors immediately (don't retry)
                    logger.error(f"Error during task execution: {other_error}")
                    return {
                        "success": False,
                        "result": f"Error: {str(other_error)}",
                        "iterations": iterations,
                        "final_url": self.browser_session.get_current_url()
                    }
            
            # Check if we got a response after retries
            if response is None:
                return {
                    "success": False,
                    "result": "Failed to get response after retries",
                    "iterations": iterations,
                    "final_url": self.browser_session.get_current_url()
                }
            
            try:
                
                # Process response content blocks
                for block in response.content:
                    if block.type == "text":
                        logger.info(f"Claude: {block.text}")
                        
                        # Check for completion
                        if "TASK_COMPLETED:" in block.text:
                            return {
                                "success": True,
                                "result": block.text,
                                "iterations": iterations,
                                "final_url": self.browser_session.get_current_url()
                            }
                        elif "TASK_FAILED:" in block.text:
                            return {
                                "success": False,
                                "result": block.text,
                                "iterations": iterations,
                                "final_url": self.browser_session.get_current_url()
                            }
                        
                        # Add text message to conversation
                        new_items.append({
                            "role": "assistant",
                            "content": [{"type": "text", "text": block.text}]
                        })
                    
                    elif block.type == "tool_use":
                        if block.name == "computer":
                            tool_input = block.input
                            action = tool_input.get("action")
                            
                            logger.info(f"Action: {action}({tool_input})")
                            
                            # Execute the computer action
                            # Force new screenshot for actions that change the page state
                            force_screenshot = action not in ("screenshot", "cursor_position")
                            
                            if action == "screenshot":
                                # Use cached screenshot if available for pure screenshot requests
                                screenshot_base64 = self._get_screenshot_with_cache(force_new=False)
                            else:
                                # Execute action and get fresh screenshot
                                screenshot_base64 = self.browser_session.execute_computer_action(
                                    action=action,
                                    text=tool_input.get("text"),
                                    coordinate=tool_input.get("coordinate"),
                                    scroll_direction=tool_input.get("scroll_direction"),
                                    scroll_amount=tool_input.get("scroll_amount"),
                                    key=tool_input.get("key")
                                )
                                # Cache the new screenshot
                                self._cache_screenshot(screenshot_base64)
                            
                            # Add tool use message
                            new_items.append({
                                "role": "assistant", 
                                "content": [{
                                    "type": "tool_use",
                                    "id": block.id,
                                    "name": block.name,
                                    "input": tool_input
                                }]
                            })
                            
                            # Add tool result with screenshot
                            new_items.append({
                                "role": "user",
                                "content": [{
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": [{
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": "image/png",
                                            "data": screenshot_base64
                                        }
                                    }]
                                }]
                            })
                            
            except Exception as processing_error:
                logger.error(f"Error processing response: {processing_error}")
                return {
                    "success": False,
                    "result": f"Error processing response: {str(processing_error)}",
                    "iterations": iterations,
                    "final_url": self.browser_session.get_current_url()
                }
            
            # Add longer delay between iterations to prevent rate limiting (sync version)
            if iterations < max_iterations:
                time.sleep(2.0)  # 2 second delay between iterations
        
        return {
            "success": False,
            "result": f"Task execution stopped after {max_iterations} iterations",
            "iterations": iterations,
            "final_url": self.browser_session.get_current_url()
        }


async def create_browser_automation_agent(
    steel_client: Steel,
    anthropic_api_key: str,
    task: str,
    max_iterations: int = 30,
    width: int = 1024,
    height: int = 768,
    use_proxy: bool = False,
    solve_captcha: bool = False,
    session_timeout: int = 900000,
    model: str = "claude-3-5-sonnet-20241022"
) -> Dict[str, Any]:
    """Factory function to create and run browser automation with proper async handling.
    
    This function automatically detects if we're in an async context and uses the 
    appropriate browser session type.
    """
    # Use async browser session since we're in an async function
    async with AsyncSteelBrowserSession(
        steel_client=steel_client,
        width=width,
        height=height,
        use_proxy=use_proxy,
        solve_captcha=solve_captcha,
        session_timeout=session_timeout
    ) as browser_session:
        
        # Create Claude agent with async browser session
        claude_agent = AsyncClaudeComputerUseAgent(
            anthropic_api_key=anthropic_api_key,
            browser_session=browser_session,
            model=model
        )
        
        # Execute the task
        result = await claude_agent.execute_task(task, max_iterations=max_iterations)
        
        # Add session information
        if browser_session.session:
            result["session_url"] = browser_session.session.session_viewer_url
        
        return result


class AsyncClaudeComputerUseAgent:
    """Async version of Claude Computer Use agent for browser automation."""

    def __init__(
        self, 
        anthropic_api_key: str,
        browser_session: AsyncSteelBrowserSession,
        model: str = "claude-3-5-sonnet-20241022"
    ):
        self.client = Anthropic(api_key=anthropic_api_key)
        self.browser_session = browser_session
        self.model = model
        self.messages: List[BetaMessageParam] = []
        self._last_screenshot_cache = None
        self._screenshot_cache_timestamp = 0
        self._cache_duration = 1.0  # Cache screenshots for 1 second
        
        if model not in MODEL_CONFIGS:
            raise ValueError(f"Unsupported model: {model}. Available: {list(MODEL_CONFIGS.keys())}")
        
        self.model_config = MODEL_CONFIGS[model]
        
        width, height = browser_session.get_dimensions()
        self.viewport_width = width
        self.viewport_height = height
        
        self.system_prompt = SYSTEM_PROMPT.replace(
            '<COORDINATE_SYSTEM>',
            f'<COORDINATE_SYSTEM>\n* The browser viewport dimensions are {width}x{height} pixels\n* The browser viewport has specific dimensions that you must respect'
        )
        
        self.tools = [{
            "type": self.model_config["tool_type"],
            "name": "computer",
            "display_width_px": width,
            "display_height_px": height,
            "display_number": 1,
        }]

    def _get_cached_screenshot(self) -> Optional[str]:
        """Get cached screenshot if still valid."""
        current_time = time.time()
        if (self._last_screenshot_cache and 
            current_time - self._screenshot_cache_timestamp < self._cache_duration):
            return self._last_screenshot_cache
        return None
    
    def _cache_screenshot(self, screenshot: str) -> None:
        """Cache a screenshot with timestamp."""
        self._last_screenshot_cache = screenshot
        self._screenshot_cache_timestamp = time.time()
        
    async def _get_screenshot_with_cache(self, force_new: bool = False) -> str:
        """Get screenshot with caching to reduce redundant captures."""
        if not force_new:
            cached = self._get_cached_screenshot()
            if cached:
                logger.debug("Using cached screenshot")
                return cached
                
        screenshot = await self.browser_session.screenshot()
        self._cache_screenshot(screenshot)
        return screenshot

    async def execute_task(self, task: str, max_iterations: int = 30) -> Dict[str, Any]:
        """Execute a browser automation task using Claude Computer Use."""
        
        logger.info(f"Executing task: {task}")
        
        input_items = [{"role": "user", "content": task}]
        new_items = []
        iterations = 0
        
        while iterations < max_iterations:
            iterations += 1
            
            # Handle rate limiting with retry logic
            retry_attempt = 0
            response = None
            
            while retry_attempt < 10:  # Max 10 retry attempts per iteration
                try:
                    response = self.client.beta.messages.create(
                        model=self.model,
                        max_tokens=4096,
                        system=self.system_prompt,
                        messages=input_items + new_items,
                        tools=self.tools,
                        betas=[self.model_config["beta_flag"]]
                    )
                    break  # Success, exit retry loop
                    
                except (RateLimitError, APITimeoutError) as rate_error:
                    delay = _handle_rate_limit_error(retry_attempt)
                    if delay is None:
                        logger.error(f"Max retries exceeded for rate limiting: {rate_error}")
                        return {
                            "success": False,
                            "result": f"Rate limit exceeded after retries: {str(rate_error)}",
                            "iterations": iterations,
                            "final_url": self.browser_session.get_current_url()
                        }
                    
                    await asyncio.sleep(delay)  # Use async sleep
                    retry_attempt += 1
                    continue
                    
                except Exception as other_error:
                    # Handle other errors immediately (don't retry)
                    logger.error(f"Error during task execution: {other_error}")
                    return {
                        "success": False,
                        "result": f"Error: {str(other_error)}",
                        "iterations": iterations,
                        "final_url": self.browser_session.get_current_url()
                    }
            
            # Check if we got a response after retries
            if response is None:
                return {
                    "success": False,
                    "result": "Failed to get response after retries",
                    "iterations": iterations,
                    "final_url": self.browser_session.get_current_url()
                }
            
            try:
                
                # Process response content blocks
                for block in response.content:
                    if block.type == "text":
                        logger.info(f"Claude: {block.text}")
                        
                        # Check for completion
                        if "TASK_COMPLETED:" in block.text:
                            return {
                                "success": True,
                                "result": block.text,
                                "iterations": iterations,
                                "final_url": self.browser_session.get_current_url()
                            }
                        elif "TASK_FAILED:" in block.text:
                            return {
                                "success": False,
                                "result": block.text,
                                "iterations": iterations,
                                "final_url": self.browser_session.get_current_url()
                            }
                        
                        # Add text message to conversation
                        new_items.append({
                            "role": "assistant",
                            "content": [{"type": "text", "text": block.text}]
                        })
                    
                    elif block.type == "tool_use":
                        if block.name == "computer":
                            tool_input = block.input
                            action = tool_input.get("action")
                            
                            logger.info(f"Action: {action}({tool_input})")
                            
                            # Execute the computer action (async)
                            # Force new screenshot for actions that change the page state
                            force_screenshot = action not in ("screenshot", "cursor_position")
                            
                            if action == "screenshot":
                                # Use cached screenshot if available for pure screenshot requests
                                screenshot_base64 = await self._get_screenshot_with_cache(force_new=False)
                            else:
                                # Execute action and get fresh screenshot
                                screenshot_base64 = await self.browser_session.execute_computer_action(
                                    action=action,
                                    text=tool_input.get("text"),
                                    coordinate=tool_input.get("coordinate"),
                                    scroll_direction=tool_input.get("scroll_direction"),
                                    scroll_amount=tool_input.get("scroll_amount"),
                                    key=tool_input.get("key")
                                )
                                # Cache the new screenshot
                                self._cache_screenshot(screenshot_base64)
                            
                            # Add tool use message
                            new_items.append({
                                "role": "assistant", 
                                "content": [{
                                    "type": "tool_use",
                                    "id": block.id,
                                    "name": block.name,
                                    "input": tool_input
                                }]
                            })
                            
                            # Add tool result with screenshot
                            new_items.append({
                                "role": "user",
                                "content": [{
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": [{
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": "image/png",
                                            "data": screenshot_base64
                                        }
                                    }]
                                }]
                            })
                            
            except Exception as processing_error:
                logger.error(f"Error processing response: {processing_error}")
                return {
                    "success": False,
                    "result": f"Error processing response: {str(processing_error)}",
                    "iterations": iterations,
                    "final_url": self.browser_session.get_current_url()
                }
            
            # Add longer delay between iterations to prevent rate limiting (async version)
            if iterations < max_iterations:
                await asyncio.sleep(2.0)  # 2 second delay between iterations
        
        return {
            "success": False,
            "result": f"Task execution stopped after {max_iterations} iterations",
            "iterations": iterations,
            "final_url": self.browser_session.get_current_url()
        }