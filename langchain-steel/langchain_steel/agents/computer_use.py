"""Simplified Steel + Claude Computer Use integration for browser automation.
ABOUTME: Clean implementation of browser automation using Steel infrastructure and Claude's computer use capabilities.
"""

import os
import time
import base64
import logging
import asyncio
from typing import Any, Dict, List, Optional, Tuple
from contextlib import asynccontextmanager

from steel import Steel
from playwright.async_api import async_playwright, Page
from anthropic import Anthropic, RateLimitError

logger = logging.getLogger(__name__)

# Computer Use tool configuration for different Claude models
TOOL_CONFIG = {
    "type": "computer_20241022",
    "name": "computer"
}

# Key mappings for Claude Computer Use to Playwright
KEY_MAPPINGS = {
    "Return": "Enter",
    "return": "Enter",
    "Enter": "Enter",
    "enter": "Enter",
    "space": " ",
    "Space": " ",
    "cmd": "Meta",
    "Cmd": "Meta",
    "ctrl": "Control",
    "Ctrl": "Control",
    "Control": "Control",
    "alt": "Alt",
    "Alt": "Alt",
    "shift": "Shift",
    "Shift": "Shift",
    "tab": "Tab",
    "Tab": "Tab",
    "escape": "Escape",
    "Escape": "Escape",
    "esc": "Escape",
    "backspace": "Backspace",
    "Backspace": "Backspace",
    "delete": "Delete",
    "Delete": "Delete",
    "arrowup": "ArrowUp",
    "ArrowUp": "ArrowUp",
    "arrowdown": "ArrowDown",
    "ArrowDown": "ArrowDown",
    "arrowleft": "ArrowLeft",
    "ArrowLeft": "ArrowLeft",
    "arrowright": "ArrowRight",
    "ArrowRight": "ArrowRight",
    "pageup": "PageUp",
    "PageUp": "PageUp",
    "pagedown": "PageDown",
    "PageDown": "PageDown",
    "home": "Home",
    "Home": "Home",
    "end": "End",
    "End": "End",
    "up": "ArrowUp",
    "down": "ArrowDown",
    "left": "ArrowLeft",
    "right": "ArrowRight",
}

# System prompt for Claude Computer Use
SYSTEM_PROMPT = """You are an AI assistant operating a web browser to complete tasks. You have access to a browser that you control through computer actions.

IMPORTANT INSTRUCTIONS:
- Take a screenshot first to see the current state
- Navigate directly to the relevant websites for your task
- Complete the specific task requested efficiently
- When done, respond with "TASK_COMPLETED: " followed by your results
- If you cannot complete the task, respond with "TASK_FAILED: " followed by the reason

Be direct and action-oriented. Focus on completing the task."""


class SteelBrowser:
    """Manages Steel browser session with Playwright integration."""
    
    def __init__(
        self,
        steel_client: Steel,
        width: int = 1280,
        height: int = 800,
        use_proxy: bool = False,
        solve_captcha: bool = False
    ):
        self.steel_client = steel_client
        self.width = width
        self.height = height
        self.use_proxy = use_proxy
        self.solve_captcha = solve_captcha
        self.session = None
        self.playwright = None
        self.browser = None
        self.page = None
    
    async def __aenter__(self):
        """Create Steel session and connect Playwright."""
        try:
            # Create Steel session
            self.session = self.steel_client.sessions.create(
                use_proxy=self.use_proxy,
                solve_captcha=self.solve_captcha,
                dimensions={"width": self.width, "height": self.height}
            )
            logger.info(f"Steel session created: {self.session.session_viewer_url}")
            
            # Connect Playwright
            self.playwright = await async_playwright().start()
            
            # Get API key
            api_key = os.getenv("STEEL_API_KEY") or getattr(self.steel_client, '_api_key', None)
            if not api_key:
                raise ValueError("STEEL_API_KEY not found")
            
            # Connect to browser
            ws_url = f"{self.session.websocket_url}&apiKey={api_key}"
            self.browser = await self.playwright.chromium.connect_over_cdp(ws_url)
            
            # Get page
            context = self.browser.contexts[0]
            self.page = context.pages[0] if context.pages else await context.new_page()
            await self.page.set_viewport_size({"width": self.width, "height": self.height})
            
            return self
            
        except Exception as e:
            await self._cleanup()
            raise e
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources."""
        await self._cleanup()
    
    async def _cleanup(self):
        """Clean up browser resources."""
        if self.page:
            try:
                await self.page.close()
            except:
                pass
        
        if self.browser:
            try:
                await self.browser.close()
            except:
                pass
        
        if self.playwright:
            try:
                await self.playwright.stop()
            except:
                pass
        
        if self.session:
            try:
                self.steel_client.sessions.release(self.session.id)
                logger.info(f"Session released: {self.session.session_viewer_url}")
            except:
                pass
    
    async def screenshot(self) -> str:
        """Take a screenshot and return base64 encoded image."""
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        png_bytes = await self.page.screenshot(
            full_page=False,
            clip={"x": 0, "y": 0, "width": self.width, "height": self.height}
        )
        return base64.b64encode(png_bytes).decode("utf-8")
    
    async def execute_action(
        self,
        action: str,
        coordinate: Optional[Tuple[int, int]] = None,
        text: Optional[str] = None,
        key: Optional[str] = None,
        **kwargs
    ) -> str:
        """Execute a browser action and return screenshot."""
        
        # Handle mouse actions
        if action in ("left_click", "right_click", "double_click", "middle_click"):
            if coordinate:
                x, y = self._clamp_coords(coordinate)
                await self.page.mouse.move(x, y)
                
                if action == "left_click":
                    await self.page.mouse.click(x, y)
                elif action == "right_click":
                    await self.page.mouse.click(x, y, button="right")
                elif action == "double_click":
                    await self.page.mouse.dblclick(x, y)
                elif action == "middle_click":
                    await self.page.mouse.click(x, y, button="middle")
        
        # Handle keyboard actions
        elif action == "type" and text:
            await self.page.keyboard.type(text, delay=12)
        
        elif action == "key" and text:
            # Handle key combinations like "ctrl+l" or "cmd+t"
            if "+" in text:
                key_parts = text.split("+")
                modifier_keys = [KEY_MAPPINGS.get(k.strip(), k.strip()) for k in key_parts[:-1]]
                main_key = KEY_MAPPINGS.get(key_parts[-1].strip(), key_parts[-1].strip())
                
                # Press modifiers
                for mod in modifier_keys:
                    await self.page.keyboard.down(mod)
                
                # Press main key
                await self.page.keyboard.press(main_key)
                
                # Release modifiers
                for mod in reversed(modifier_keys):
                    await self.page.keyboard.up(mod)
            else:
                # Single key press
                key_to_press = KEY_MAPPINGS.get(text.strip(), text.strip())
                await self.page.keyboard.press(key_to_press)
        
        # Handle scroll
        elif action == "scroll":
            direction = kwargs.get("scroll_direction", "down")
            amount = kwargs.get("scroll_amount", 3)
            
            if coordinate:
                x, y = self._clamp_coords(coordinate)
                await self.page.mouse.move(x, y)
            
            delta_map = {
                "up": (0, -100 * amount),
                "down": (0, 100 * amount),
                "left": (-100 * amount, 0),
                "right": (100 * amount, 0)
            }
            dx, dy = delta_map.get(direction, (0, 100))
            await self.page.mouse.wheel(dx, dy)
        
        # Handle mouse move
        elif action == "mouse_move" and coordinate:
            x, y = self._clamp_coords(coordinate)
            await self.page.mouse.move(x, y)
        
        # Handle wait
        elif action == "wait":
            duration = kwargs.get("duration", 1)
            await asyncio.sleep(duration)
        
        # Return screenshot after action
        return await self.screenshot()
    
    def _clamp_coords(self, coordinate: Tuple[int, int]) -> Tuple[int, int]:
        """Clamp coordinates to viewport bounds."""
        x, y = coordinate
        x = max(0, min(x, self.width - 1))
        y = max(0, min(y, self.height - 1))
        return x, y


class ClaudeAgent:
    """Claude Computer Use agent for browser automation."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022"
    ):
        self.client = Anthropic(api_key=api_key)
        self.model = model
        
    async def execute_task(
        self,
        browser: SteelBrowser,
        task: str,
        max_steps: int = 30
    ) -> Dict[str, Any]:
        """Execute a browser automation task."""
        
        logger.info(f"Starting task: {task}")
        
        # Build tool definition
        tools = [{
            **TOOL_CONFIG,
            "display_width_px": browser.width,
            "display_height_px": browser.height,
            "display_number": 1
        }]
        
        # Initialize conversation
        messages = [{"role": "user", "content": task}]
        
        for step in range(max_steps):
            try:
                # Call Claude with rate limit handling
                response = await self._call_claude_with_retry(
                    messages=messages,
                    tools=tools,
                    system=SYSTEM_PROMPT
                )
                
                # Process response
                for block in response.content:
                    if block.type == "text":
                        logger.info(f"Claude: {block.text}")
                        
                        # Check for completion
                        if "TASK_COMPLETED:" in block.text:
                            return {
                                "success": True,
                                "result": block.text,
                                "steps": step + 1,
                                "session_url": browser.session.session_viewer_url
                            }
                        elif "TASK_FAILED:" in block.text:
                            return {
                                "success": False,
                                "result": block.text,
                                "steps": step + 1,
                                "session_url": browser.session.session_viewer_url
                            }
                        
                        # Add to conversation
                        messages.append({
                            "role": "assistant",
                            "content": block.text
                        })
                    
                    elif block.type == "tool_use" and block.name == "computer":
                        # Execute browser action
                        tool_input = block.input
                        action = tool_input.get("action", "screenshot")
                        
                        logger.info(f"Action: {action}")
                        
                        # Execute action and get screenshot
                        screenshot = await browser.execute_action(
                            action=action,
                            coordinate=tool_input.get("coordinate"),
                            text=tool_input.get("text"),
                            key=tool_input.get("key"),
                            scroll_direction=tool_input.get("scroll_direction"),
                            scroll_amount=tool_input.get("scroll_amount"),
                            duration=tool_input.get("duration")
                        )
                        
                        # Add tool use and result to conversation
                        messages.append({
                            "role": "assistant",
                            "content": [{
                                "type": "tool_use",
                                "id": block.id,
                                "name": "computer",
                                "input": tool_input
                            }]
                        })
                        
                        messages.append({
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": [{
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/png",
                                        "data": screenshot
                                    }
                                }]
                            }]
                        })
                
            except Exception as e:
                logger.error(f"Error at step {step}: {e}")
                return {
                    "success": False,
                    "result": f"Error: {str(e)}",
                    "steps": step + 1,
                    "session_url": browser.session.session_viewer_url if browser.session else None
                }
        
        return {
            "success": False,
            "result": f"Max steps ({max_steps}) reached without completion",
            "steps": max_steps,
            "session_url": browser.session.session_viewer_url if browser.session else None
        }
    
    async def _call_claude_with_retry(
        self,
        messages: List[Dict],
        tools: List[Dict],
        system: str,
        max_retries: int = 3
    ):
        """Call Claude API with retry logic for rate limits."""
        
        for attempt in range(max_retries):
            try:
                return self.client.beta.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=system,
                    messages=messages,
                    tools=tools,
                    betas=["computer-use-2024-10-22"]
                )
            except RateLimitError as e:
                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt, 10)
                    logger.warning(f"Rate limit hit, waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise e


async def run_browser_task(
    steel_api_key: str,
    anthropic_api_key: str,
    task: str,
    max_steps: int = 30,
    use_proxy: bool = False,
    solve_captcha: bool = False
) -> Dict[str, Any]:
    """Run a browser automation task with Steel and Claude.
    
    Args:
        steel_api_key: Steel API key
        anthropic_api_key: Anthropic API key
        task: Natural language task description
        max_steps: Maximum number of steps to execute
        use_proxy: Enable proxy for the browser session
        solve_captcha: Enable CAPTCHA solving
    
    Returns:
        Dictionary with task results
    
    Example:
        >>> result = await run_browser_task(
        ...     steel_api_key="your_steel_key",
        ...     anthropic_api_key="your_anthropic_key",
        ...     task="Go to Hacker News and get the top 5 posts"
        ... )
    """
    
    # Initialize Steel client
    steel_client = Steel(steel_api_key=steel_api_key)
    
    # Create browser session
    async with SteelBrowser(
        steel_client=steel_client,
        use_proxy=use_proxy,
        solve_captcha=solve_captcha
    ) as browser:
        
        # Create Claude agent
        agent = ClaudeAgent(api_key=anthropic_api_key)
        
        # Execute task
        result = await agent.execute_task(
            browser=browser,
            task=task,
            max_steps=max_steps
        )
        
        return result