"""ABOUTME: Steel browser agent for natural language browser automation tasks.
ABOUTME: Provides high-level browser automation using Steel's cloud infrastructure."""

import logging
import os
import asyncio
from typing import Any, Dict, Optional, Union, Type
import json

from langchain_core.callbacks import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
from pydantic import BaseModel, Field

from langchain_steel.tools.base import BaseSteelTool
from langchain_steel.utils.errors import SteelError
from langchain_steel.agents.claude_computer_use import (
    create_browser_automation_agent
)

logger = logging.getLogger(__name__)


class SteelBrowserAgentInput(BaseModel):
    """Input schema for Steel browser agent."""
    
    task: str = Field(description="Natural language description of the browser task to perform")
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session ID to reuse an existing browser session"
    )
    max_steps: Optional[int] = Field(
        default=50,
        description="Maximum number of interaction steps to perform"
    )
    session_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional session configuration (proxy, stealth_mode, solve_captcha, etc.)"
    )
    return_format: Optional[str] = Field(
        default="text",
        description="Format for returned data: 'text', 'json', or 'structured'"
    )


class SteelBrowserAgent(BaseSteelTool):
    """Steel browser agent for natural language browser automation.
    
    This tool enables complex browser automation through natural language task descriptions.
    It leverages Steel's cloud-based browser infrastructure to perform multi-step web interactions,
    handle dynamic content, solve CAPTCHAs, and extract structured data.
    
    Key Features:
    - Natural language task execution
    - Cloud-based browser sessions with advanced anti-detection
    - Automatic CAPTCHA solving and proxy rotation
    - Session persistence for multi-step workflows
    - Support for JavaScript-heavy applications and SPAs
    - Structured data extraction and formatting
    
    Examples:
        Basic task execution:
            >>> agent = SteelBrowserAgent()
            >>> result = agent.run("Go to Hacker News and get the top 5 posts")
        
        With session options:
            >>> result = agent.run({
            ...     "task": "Search GitHub for Python ML libraries and get the top 10",
            ...     "session_options": {
            ...         "use_proxy": True,
            ...         "stealth_mode": True
            ...     }
            ... })
        
        Multi-step workflow with session persistence:
            >>> result1 = agent.run("Login to example.com and navigate to dashboard")
            >>> session_id = result1.get("session_id")
            >>> result2 = agent.run({
            ...     "task": "Download the monthly report from the dashboard",
            ...     "session_id": session_id
            ... })
    """
    
    name: str = "steel_browser_agent"
    description: str = (
        "Perform complex browser automation tasks using natural language descriptions. "
        "This tool can navigate websites, interact with elements, fill forms, extract data, "
        "and handle dynamic content. It supports multi-step workflows, session persistence, "
        "and advanced anti-detection features. Input should be a natural language task "
        "description or a dict with 'task' and optional parameters like session_id, "
        "max_steps, session_options, and return_format."
    )
    args_schema: Type[BaseModel] = SteelBrowserAgentInput
    
    def _run(
        self,
        task: str,
        session_id: Optional[str] = None,
        max_steps: Optional[int] = 50,
        session_options: Optional[Dict[str, Any]] = None,
        return_format: Optional[str] = "text",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute a browser automation task.
        
        Args:
            task: Natural language description of the task
            session_id: Optional existing session ID to reuse
            max_steps: Maximum number of interaction steps
            session_options: Session configuration options
            return_format: Format for returned data
            run_manager: Callback manager for tool execution
            
        Returns:
            Task results as formatted string
        """
        try:
            self._log_tool_execution("browser_agent", {
                "task": task[:100] + "..." if len(task) > 100 else task,
                "session_id": session_id,
                "max_steps": max_steps,
                "return_format": return_format,
            })
            
            if run_manager:
                run_manager.on_text(f"Executing browser task: {task}\n")
            
            # Execute the browser automation task
            result = self._execute_browser_task(
                task=task,
                session_id=session_id,
                max_steps=max_steps,
                session_options=session_options or {},
                return_format=return_format,
                run_manager=run_manager
            )
            
            if run_manager:
                run_manager.on_text(f"Task completed successfully\n")
            
            return result
        
        except Exception as e:
            error_msg = self._handle_steel_error(e, "browser_agent")
            if run_manager:
                run_manager.on_text(f"Error: {error_msg}\n")
            return f"Browser automation failed: {error_msg}"
    
    async def _arun(
        self,
        task: str,
        session_id: Optional[str] = None,
        max_steps: Optional[int] = 50,
        session_options: Optional[Dict[str, Any]] = None,
        return_format: Optional[str] = "text",
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Execute a browser automation task asynchronously.
        
        Args:
            task: Natural language description of the task
            session_id: Optional existing session ID to reuse
            max_steps: Maximum number of interaction steps
            session_options: Session configuration options
            return_format: Format for returned data
            run_manager: Async callback manager for tool execution
            
        Returns:
            Task results as formatted string
        """
        try:
            self._log_tool_execution("browser_agent", {
                "task": task[:100] + "..." if len(task) > 100 else task,
                "session_id": session_id,
                "async": True,
            })
            
            if run_manager:
                await run_manager.on_text(f"Executing browser task (async): {task}\n")
            
            # Execute async browser automation task
            result = await self._execute_browser_task_async(
                task=task,
                session_id=session_id,
                max_steps=max_steps,
                session_options=session_options or {},
                return_format=return_format,
                run_manager=run_manager
            )
            
            if run_manager:
                await run_manager.on_text(f"Task completed successfully (async)\n")
            
            return result
        
        except Exception as e:
            error_msg = self._handle_steel_error(e, "browser_agent")
            if run_manager:
                await run_manager.on_text(f"Error: {error_msg}\n")
            return f"Browser automation failed: {error_msg}"
    
    def _execute_browser_task(
        self,
        task: str,
        session_id: Optional[str],
        max_steps: int,
        session_options: Dict[str, Any],
        return_format: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute browser automation task using Claude Computer Use.
        
        This method uses Claude's computer use capabilities with Steel's browser
        infrastructure to perform complex browser automation tasks.
        
        Args:
            task: Natural language task description
            session_id: Optional existing session ID (ignored for now)
            max_steps: Maximum interaction steps
            session_options: Session configuration
            return_format: Output format
            run_manager: Optional callback manager
            
        Returns:
            Formatted task results
        """
        # Validate browser agent configuration
        self.config.validate_browser_agent_config()
        anthropic_api_key = self.config.anthropic_api_key
        
        # Prepare session options with defaults
        session_config = {
            "use_proxy": session_options.get("use_proxy", False),
            "solve_captcha": session_options.get("solve_captcha", False),
            "session_timeout": session_options.get("session_timeout", 900000),
            "width": session_options.get("width", 1024),
            "height": session_options.get("height", 768),
        }
        
        if run_manager:
            run_manager.on_text(f"Starting Claude Computer Use browser automation\n")
            run_manager.on_text(f"Task: {task}\n")
            run_manager.on_text(f"Max steps: {max_steps}\n")
        
        try:
            # Check if we're in an async context and handle appropriately
            try:
                # Try to get the running event loop
                loop = asyncio.get_running_loop()
                # We're in an event loop, run synchronously but await the async task
                import concurrent.futures
                import threading
                
                # Create a new thread with its own event loop for the async task
                def run_in_thread():
                    return asyncio.run(self._execute_async_browser_task(
                        task, anthropic_api_key, session_config, max_steps, run_manager
                    ))
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    result = future.result()
                    
            except RuntimeError:
                # No event loop running, we can use asyncio.run() directly
                result = asyncio.run(self._execute_async_browser_task(
                    task, anthropic_api_key, session_config, max_steps, run_manager
                ))
            
            if run_manager:
                run_manager.on_text(f"Task completed after {result['iterations']} iterations\n")
            
            # Format the result
            formatted_result = self._format_claude_result(result, return_format)
            
            # Add session information
            if "session_url" in result:
                session_info = f"\n\nSession URL: {result['session_url']}"
                formatted_result += session_info
            
            return formatted_result
                
        except Exception as e:
            error_msg = f"Browser automation failed: {str(e)}"
            logger.error(error_msg)
            if run_manager:
                run_manager.on_text(f"Error: {error_msg}\n")
            raise SteelError(error_msg, original_error=e)
    
    async def _execute_async_browser_task(
        self,
        task: str,
        anthropic_api_key: str,
        session_config: Dict[str, Any],
        max_steps: int,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        """Execute browser automation task using async factory function."""
        
        if run_manager:
            run_manager.on_text(f"Creating async browser automation session\n")
        
        # Use the async factory function
        result = await create_browser_automation_agent(
            steel_client=self.client._client,  # Get the Steel SDK client
            anthropic_api_key=anthropic_api_key,
            task=task,
            max_iterations=max_steps,
            width=session_config["width"],
            height=session_config["height"],
            use_proxy=session_config["use_proxy"],
            solve_captcha=session_config["solve_captcha"],
            session_timeout=session_config["session_timeout"],
            model="claude-3-5-sonnet-20241022"
        )
        
        return result
    
    async def _execute_browser_task_async(
        self,
        task: str,
        session_id: Optional[str],
        max_steps: int,
        session_options: Dict[str, Any],
        return_format: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Execute browser automation task asynchronously using Claude Computer Use."""
        
        # Validate browser agent configuration
        self.config.validate_browser_agent_config()
        anthropic_api_key = self.config.anthropic_api_key
        
        # Prepare session options with defaults
        session_config = {
            "use_proxy": session_options.get("use_proxy", False),
            "solve_captcha": session_options.get("solve_captcha", False),
            "session_timeout": session_options.get("session_timeout", 900000),
            "width": session_options.get("width", 1024),
            "height": session_options.get("height", 768),
        }
        
        if run_manager:
            await run_manager.on_text(f"Starting Claude Computer Use browser automation (async)\n")
            await run_manager.on_text(f"Task: {task}\n")
            await run_manager.on_text(f"Max steps: {max_steps}\n")
        
        try:
            # Use the async factory function directly
            result = await create_browser_automation_agent(
                steel_client=self.client._client,  # Get the Steel SDK client
                anthropic_api_key=anthropic_api_key,
                task=task,
                max_iterations=max_steps,
                width=session_config["width"],
                height=session_config["height"],
                use_proxy=session_config["use_proxy"],
                solve_captcha=session_config["solve_captcha"],
                session_timeout=session_config["session_timeout"],
                model="claude-3-5-sonnet-20241022"
            )
            
            if run_manager:
                await run_manager.on_text(f"Task completed after {result['iterations']} iterations\n")
            
            # Format the result
            formatted_result = self._format_claude_result(result, return_format)
            
            # Add session information
            if "session_url" in result:
                session_info = f"\n\nSession URL: {result['session_url']}"
                formatted_result += session_info
            
            return formatted_result
                
        except Exception as e:
            error_msg = f"Browser automation failed: {str(e)}"
            logger.error(error_msg)
            if run_manager:
                await run_manager.on_text(f"Error: {error_msg}\n")
            raise SteelError(error_msg, original_error=e)
    
    def _format_claude_result(self, result: Dict[str, Any], format_type: str) -> str:
        """Format Claude Computer Use result based on requested format.
        
        Args:
            result: Result from Claude Computer Use execution
            format_type: Desired output format
            
        Returns:
            Formatted result string
        """
        if format_type == "json":
            return json.dumps(result, indent=2)
        
        elif format_type == "structured":
            structured = {
                "task_completed": result.get("success", False),
                "iterations_executed": result.get("iterations", 0),
                "result_summary": result.get("result", ""),
                "final_url": result.get("final_url", ""),
                "method": "claude_computer_use",
            }
            return json.dumps(structured, indent=2)
        
        else:  # text format (default)
            result_parts = []
            
            if result.get("success"):
                result_parts.append("✅ Task completed successfully")
            else:
                result_parts.append("❌ Task failed")
            
            if "result" in result:
                result_parts.append(f"\nResult: {result['result']}")
            
            if "iterations" in result:
                result_parts.append(f"Iterations: {result['iterations']}")
            
            if "final_url" in result:
                result_parts.append(f"Final URL: {result['final_url']}")
            
            result_parts.append(f"Method: Claude Computer Use")
            
            return "\n".join(result_parts)
    
    
    
    
    
    def _format_browser_result(self, raw_result: Dict[str, Any], format_type: str) -> str:
        """Format browser automation results.
        
        Args:
            raw_result: Raw result from Steel API
            format_type: Desired output format
            
        Returns:
            Formatted result string
        """
        if not raw_result.get("success"):
            return f"Task failed: {raw_result.get('error', 'Unknown error')}"
        
        if format_type == "json":
            return json.dumps(raw_result, indent=2)
        
        elif format_type == "structured":
            # Create structured summary
            structured = {
                "task_completed": raw_result.get("task", ""),
                "steps_executed": raw_result.get("steps_executed", 0),
                "result_summary": raw_result.get("result", ""),
                "final_url": raw_result.get("final_url", ""),
                "execution_time_seconds": raw_result.get("execution_time", 0),
                "extracted_data": raw_result.get("extracted_data", {}),
                "metadata": raw_result.get("metadata", {})
            }
            return json.dumps(structured, indent=2)
        
        else:  # text format (default)
            result_parts = []
            
            if "result" in raw_result:
                result_parts.append(f"Task Result: {raw_result['result']}")
            
            if "steps_executed" in raw_result:
                result_parts.append(f"Steps Executed: {raw_result['steps_executed']}")
            
            if "final_url" in raw_result:
                result_parts.append(f"Final URL: {raw_result['final_url']}")
            
            if "execution_time" in raw_result:
                result_parts.append(f"Execution Time: {raw_result['execution_time']}s")
            
            if "extracted_data" in raw_result and raw_result["extracted_data"]:
                result_parts.append(f"Extracted Data: {json.dumps(raw_result['extracted_data'], indent=2)}")
            
            return "\n".join(result_parts)
    
