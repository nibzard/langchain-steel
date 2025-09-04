"""Steel browser agent for LangChain - natural language browser automation.
ABOUTME: Clean, simplified browser agent using Steel infrastructure and Claude Computer Use.
"""

import logging
import asyncio
from typing import Any, Dict, Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
from pydantic import BaseModel, Field

from langchain_steel.tools.base import BaseSteelTool
from langchain_steel.agents.computer_use import run_browser_task

logger = logging.getLogger(__name__)


class SteelBrowserAgentInput(BaseModel):
    """Input schema for Steel browser agent."""
    
    task: str = Field(
        description="Natural language description of the browser task to perform"
    )
    max_steps: Optional[int] = Field(
        default=30,
        description="Maximum number of interaction steps"
    )
    use_proxy: Optional[bool] = Field(
        default=False,
        description="Enable proxy for the browser session"
    )
    solve_captcha: Optional[bool] = Field(
        default=False,
        description="Enable automatic CAPTCHA solving"
    )


class SteelBrowserAgent(BaseSteelTool):
    """Steel browser agent for natural language browser automation.
    
    This tool enables browser automation through natural language instructions.
    It uses Steel's cloud infrastructure with Claude Computer Use for intelligent,
    autonomous web interaction.
    
    Features:
    - Natural language task execution
    - Cloud-based browser sessions
    - CAPTCHA solving capability
    - Proxy support
    - Session replay URLs for debugging
    
    Example:
        >>> agent = SteelBrowserAgent()
        >>> result = agent.run("Go to Hacker News and get the top 5 posts")
        >>> print(result)
    """
    
    name: str = "steel_browser_agent"
    description: str = (
        "Perform browser automation tasks using natural language. "
        "Can navigate websites, extract data, fill forms, and interact with web pages. "
        "Input should be a clear description of what you want to accomplish."
    )
    args_schema: Type[BaseModel] = SteelBrowserAgentInput
    
    def _run(
        self,
        task: str,
        max_steps: Optional[int] = 30,
        use_proxy: Optional[bool] = False,
        solve_captcha: Optional[bool] = False,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute browser automation task synchronously."""
        
        # Run async function in sync context
        result = asyncio.run(self._arun(
            task=task,
            max_steps=max_steps,
            use_proxy=use_proxy,
            solve_captcha=solve_captcha,
            run_manager=run_manager
        ))
        return result
    
    async def _arun(
        self,
        task: str,
        max_steps: Optional[int] = 30,
        use_proxy: Optional[bool] = False,
        solve_captcha: Optional[bool] = False,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Execute browser automation task asynchronously."""
        
        try:
            # Log execution
            self._log_tool_execution("browser_agent", {
                "task": task[:100] + "..." if len(task) > 100 else task,
                "max_steps": max_steps
            })
            
            # Validate configuration
            self.config.validate_browser_agent_config()
            
            # Notify via callback manager if available
            if run_manager:
                await run_manager.on_text(f"🤖 Starting browser task: {task}\n")
                await run_manager.on_text(f"⚙️  Max steps: {max_steps}\n")
                if use_proxy:
                    await run_manager.on_text("🛡️  Proxy enabled\n")
                if solve_captcha:
                    await run_manager.on_text("🧩 CAPTCHA solving enabled\n")
            
            # Execute browser task
            result = await run_browser_task(
                steel_api_key=self.config.api_key,
                anthropic_api_key=self.config.anthropic_api_key,
                task=task,
                max_steps=max_steps,
                use_proxy=use_proxy,
                solve_captcha=solve_captcha
            )
            
            # Process result
            success_icon = "✅" if result.get("success") else "❌"
            
            if run_manager:
                await run_manager.on_text(
                    f"{success_icon} Task {'completed' if result.get('success') else 'failed'} "
                    f"after {result.get('steps', 0)} steps\n"
                )
                if result.get("session_url"):
                    await run_manager.on_text(f"🔗 Session replay: {result['session_url']}\n")
            
            # Format output
            output_lines = []
            
            if result.get("success"):
                output_lines.append(f"✅ Task completed successfully")
            else:
                output_lines.append(f"❌ Task failed")
            
            if result.get("result"):
                # Extract the actual result text after the status prefix
                result_text = result["result"]
                if "TASK_COMPLETED:" in result_text:
                    result_text = result_text.split("TASK_COMPLETED:", 1)[1].strip()
                elif "TASK_FAILED:" in result_text:
                    result_text = result_text.split("TASK_FAILED:", 1)[1].strip()
                
                output_lines.append(f"\n📄 Result:\n{result_text}")
            
            output_lines.append(f"\n🔢 Steps executed: {result.get('steps', 0)}")
            
            if result.get("session_url"):
                output_lines.append(f"🔗 Session replay: {result['session_url']}")
            
            return "\n".join(output_lines)
            
        except Exception as e:
            error_msg = self._handle_steel_error(e, "browser_agent")
            if run_manager:
                await run_manager.on_text(f"💥 Error: {error_msg}\n")
            logger.error(f"Browser automation failed: {error_msg}")
            return f"Browser automation failed: {error_msg}"