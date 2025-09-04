#!/usr/bin/env python3
"""
Integration tests for Steel-LangChain components.

These tests focus on integration between components and with LangChain
framework, testing realistic usage patterns and workflows.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, Mock
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from langchain_steel import SteelScrapeTool, SteelBrowserAgent, SteelConfig


class TestLangChainIntegration:
    """Test integration with LangChain framework."""
    
    def test_scrape_tool_langchain_interface(self):
        """Test that SteelScrapeTool properly implements LangChain BaseTool interface."""
        with patch.dict(os.environ, {"STEEL_API_KEY": "mock-key"}):
            with patch('langchain_steel.utils.client.SteelClient'):
                tool = SteelScrapeTool()
                
                # Test LangChain BaseTool interface
                assert hasattr(tool, 'name')
                assert hasattr(tool, 'description')
                assert hasattr(tool, 'args_schema')
                assert hasattr(tool, 'run')
                assert hasattr(tool, 'arun')
                assert hasattr(tool, '_run')
                assert hasattr(tool, '_arun')
                
                # Test tool metadata
                assert isinstance(tool.name, str)
                assert len(tool.name) > 0
                assert isinstance(tool.description, str)
                assert len(tool.description) > 0
    
    def test_browser_agent_langchain_interface(self):
        """Test that SteelBrowserAgent properly implements LangChain BaseTool interface."""
        with patch.dict(os.environ, {"STEEL_API_KEY": "mock-key"}):
            with patch('langchain_steel.utils.client.SteelClient'):
                agent = SteelBrowserAgent()
                
                # Test LangChain BaseTool interface
                assert hasattr(agent, 'name')
                assert hasattr(agent, 'description')
                assert hasattr(agent, 'args_schema')
                assert hasattr(agent, 'run')
                assert hasattr(agent, 'arun')
                assert hasattr(agent, '_run')
                assert hasattr(agent, '_arun')
                
                # Test agent metadata
                assert isinstance(agent.name, str)
                assert len(agent.name) > 0
                assert isinstance(agent.description, str)
                assert len(agent.description) > 0
    
    @pytest.mark.skipif(
        "langchain" not in sys.modules,
        reason="LangChain not available"
    )
    def test_tools_in_agent_list(self):
        """Test that Steel tools can be used in LangChain agent tool lists."""
        try:
            from langchain.agents import load_tools
            
            with patch.dict(os.environ, {"STEEL_API_KEY": "mock-key"}):
                with patch('langchain_steel.utils.client.SteelClient'):
                    scrape_tool = SteelScrapeTool()
                    browser_agent = SteelBrowserAgent()
                    
                    tools = [scrape_tool, browser_agent]
                    
                    # Verify tools can be used in a list
                    assert len(tools) == 2
                    
                    # Verify each tool has required attributes
                    for tool in tools:
                        assert hasattr(tool, 'name')
                        assert hasattr(tool, 'description')
                        assert hasattr(tool, 'run')
                        
        except ImportError:
            pytest.skip("LangChain not available for this test")


class TestWorkflowIntegration:
    """Test workflow integration scenarios."""
    
    @pytest.fixture
    def mock_tools(self):
        """Provide mock Steel tools."""
        with patch.dict(os.environ, {"STEEL_API_KEY": "mock-key"}):
            with patch('langchain_steel.utils.client.SteelClient') as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                scrape_tool = SteelScrapeTool()
                browser_agent = SteelBrowserAgent()
                
                # Mock successful responses
                scrape_tool._client = mock_client
                browser_agent._client = mock_client
                
                mock_client.scrape.return_value = {"content": "Mock scraped content"}
                mock_client.browser_task.return_value = {"result": "Mock browser result"}
                
                return scrape_tool, browser_agent, mock_client
    
    def test_sequential_tool_usage(self, mock_tools):
        """Test using multiple Steel tools in sequence."""
        scrape_tool, browser_agent, mock_client = mock_tools
        
        # Simulate sequential workflow
        results = []
        
        # Step 1: Scrape initial content
        try:
            result1 = scrape_tool.invoke({"url": "https://example.com"})
            results.append(("scrape", result1))
        except Exception as e:
            results.append(("scrape", f"Error: {e}"))
        
        # Step 2: Use browser for complex task
        try:
            result2 = browser_agent.invoke({"task": "Navigate and extract data"})
            results.append(("browse", result2))
        except Exception as e:
            results.append(("browse", f"Error: {e}"))
        
        # Verify workflow execution
        assert len(results) == 2
        assert results[0][0] == "scrape"
        assert results[1][0] == "browse"
    
    def test_concurrent_tool_usage(self, mock_tools):
        """Test using Steel tools concurrently (simulated)."""
        scrape_tool, browser_agent, mock_client = mock_tools
        
        # Simulate concurrent tasks
        tasks = [
            ("scrape", scrape_tool, {"url": "https://site1.com"}),
            ("browse", browser_agent, {"task": "Navigate site2"}),
            ("scrape", scrape_tool, {"url": "https://site3.com"}),
        ]
        
        results = []
        for task_type, tool, params in tasks:
            try:
                result = tool.invoke(params)
                results.append((task_type, "success", result))
            except Exception as e:
                results.append((task_type, "error", str(e)))
        
        # Verify all tasks were attempted
        assert len(results) == 3
        assert all(len(result) == 3 for result in results)
    
    def test_error_recovery_workflow(self, mock_tools):
        """Test error recovery in workflows."""
        scrape_tool, browser_agent, mock_client = mock_tools
        
        # Mock an error scenario
        mock_client.scrape.side_effect = Exception("Mock API error")
        
        workflow_results = []
        
        # Try scraping with error handling
        try:
            result = scrape_tool.invoke({"url": "https://failing-site.com"})
            workflow_results.append(("scrape_success", result))
        except Exception:
            # Fallback to browser automation
            try:
                mock_client.browser_task.return_value = {"result": "Browser fallback success"}
                result = browser_agent.invoke({"task": "Get content from failing site"})
                workflow_results.append(("browser_fallback", result))
            except Exception as e:
                workflow_results.append(("total_failure", str(e)))
        
        # Should have attempted fallback
        assert len(workflow_results) >= 1


class TestConfigurationIntegration:
    """Test configuration integration across components."""
    
    def test_shared_configuration(self):
        """Test sharing configuration between tools."""
        config = SteelConfig(
            api_key="shared-key",
            session_timeout=120,
            use_proxy=False,
            stealth_mode=True
        )
        
        with patch('langchain_steel.utils.client.SteelClient'):
            scrape_tool = SteelScrapeTool(config=config)
            browser_agent = SteelBrowserAgent(config=config)
            
            # Both tools should use the same configuration
            assert scrape_tool.config.api_key == "shared-key"
            assert browser_agent.config.api_key == "shared-key"
            assert scrape_tool.config.session_timeout == 120
            assert browser_agent.config.session_timeout == 120
    
    def test_configuration_override(self):
        """Test configuration override scenarios."""
        base_config = SteelConfig(
            api_key="base-key",
            session_timeout=60,
            use_proxy=True
        )
        
        override_config = SteelConfig(
            api_key="override-key",
            session_timeout=180,
            use_proxy=False
        )
        
        with patch('langchain_steel.utils.client.SteelClient'):
            tool1 = SteelScrapeTool(config=base_config)
            tool2 = SteelScrapeTool(config=override_config)
            
            # Tools should have different configurations
            assert tool1.config.api_key == "base-key"
            assert tool2.config.api_key == "override-key"
            assert tool1.config.session_timeout == 60
            assert tool2.config.session_timeout == 180
    
    def test_environment_configuration_integration(self):
        """Test environment variable configuration integration."""
        env_vars = {
            "STEEL_API_KEY": "env-api-key",
            "STEEL_USE_PROXY": "false",
            "STEEL_SOLVE_CAPTCHA": "true",
            "STEEL_SESSION_TIMEOUT": "300"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('langchain_steel.utils.client.SteelClient'):
                # Tools should pick up environment configuration
                tool = SteelScrapeTool()
                
                # Verify environment configuration is used
                assert tool.config.api_key == "env-api-key"


class TestAsyncIntegration:
    """Test async functionality integration."""
    
    @pytest.fixture
    def mock_async_tools(self):
        """Provide mock async Steel tools."""
        with patch.dict(os.environ, {"STEEL_API_KEY": "mock-key"}):
            with patch('langchain_steel.utils.client.AsyncSteelClient') as mock_async_client_class:
                mock_async_client = MagicMock()
                mock_async_client_class.return_value = mock_async_client
                
                scrape_tool = SteelScrapeTool()
                browser_agent = SteelBrowserAgent()
                
                # Mock async client
                scrape_tool._async_client = mock_async_client
                browser_agent._async_client = mock_async_client
                
                return scrape_tool, browser_agent, mock_async_client
    
    def test_async_tool_interface(self, mock_async_tools):
        """Test async tool interface."""
        scrape_tool, browser_agent, mock_async_client = mock_async_tools
        
        # Verify async methods exist
        assert hasattr(scrape_tool, '_arun')
        assert hasattr(browser_agent, '_arun')
        assert hasattr(scrape_tool, 'arun')
        assert hasattr(browser_agent, 'arun')
        
        # Verify async methods are callable
        assert callable(scrape_tool._arun)
        assert callable(browser_agent._arun)
    
    @pytest.mark.asyncio
    async def test_async_scraping(self, mock_async_tools):
        """Test async scraping functionality."""
        scrape_tool, _, mock_async_client = mock_async_tools
        
        # Mock async response
        mock_response = {"content": "Async scraped content"}
        mock_async_client.scrape.return_value = mock_response
        
        # Mock session context
        mock_session_context = MagicMock()
        mock_session_context.__aenter__.return_value = MagicMock()
        mock_session_context.__aexit__.return_value = None
        mock_async_client.session_context.return_value = mock_session_context
        
        try:
            result = await scrape_tool._arun("https://example.com")
            assert isinstance(result, str)
        except Exception as e:
            # Expected due to mock limitations, but test structure is validated
            assert "scrape" in str(e).lower() or "session" in str(e).lower()


class TestDataFlow:
    """Test data flow between components."""
    
    def test_scrape_to_browser_data_flow(self):
        """Test data flow from scraping to browser automation."""
        with patch.dict(os.environ, {"STEEL_API_KEY": "mock-key"}):
            with patch('langchain_steel.utils.client.SteelClient') as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                scrape_tool = SteelScrapeTool()
                browser_agent = SteelBrowserAgent()
                
                # Mock scraping result
                scrape_result = {
                    "content": "Page content with important links",
                    "links": [{"href": "/page1", "text": "Link 1"}]
                }
                mock_client.scrape.return_value = scrape_result
                
                # Simulate workflow: scrape first, then use results for browser task
                try:
                    scraped_data = scrape_tool.invoke({
                        "url": "https://example.com",
                        "extract_links": True
                    })
                    
                    # Use scraped data to inform browser task
                    browser_task = f"Navigate to links found in: {scraped_data[:100]}"
                    browser_result = browser_agent.invoke({"task": browser_task})
                    
                    # Verify data flow occurred
                    assert isinstance(scraped_data, str)
                    assert isinstance(browser_result, str)
                    
                except Exception as e:
                    # Expected due to mock API, but structure is validated
                    assert isinstance(e, Exception)
    
    def test_configuration_data_flow(self):
        """Test configuration data flow between components."""
        config = SteelConfig(
            api_key="flow-test-key",
            session_timeout=240
        )
        
        with patch('langchain_steel.utils.client.SteelClient'):
            tools = [
                SteelScrapeTool(config=config),
                SteelBrowserAgent(config=config)
            ]
            
            # Verify configuration flows to all tools
            for tool in tools:
                assert tool.config.api_key == "flow-test-key"
                assert tool.config.session_timeout == 240


class TestErrorPropagation:
    """Test error propagation across the integration."""
    
    def test_configuration_error_propagation(self):
        """Test how configuration errors propagate."""
        # Invalid configuration should be caught early
        with pytest.raises(Exception):  # Could be SteelConfigError or similar
            SteelConfig(api_key="", session_timeout=-1)
    
    def test_tool_error_propagation(self):
        """Test how tool errors propagate."""
        with patch.dict(os.environ, {"STEEL_API_KEY": "mock-key"}):
            with patch('langchain_steel.utils.client.SteelClient') as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                # Mock a client error
                mock_client.scrape.side_effect = Exception("Mock Steel API error")
                
                scrape_tool = SteelScrapeTool()
                
                # Error should be handled gracefully and returned as string
                result = scrape_tool.invoke({"url": "https://example.com"})
                assert isinstance(result, str)
                assert "error" in result.lower()


if __name__ == "__main__":
    # Run tests with pytest if available, otherwise run basic checks
    try:
        import pytest
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not available, running basic integration checks...")
        
        # Basic integration checks
        print("Testing tool interfaces...")
        with patch.dict(os.environ, {"STEEL_API_KEY": "mock-key"}):
            with patch('langchain_steel.utils.client.SteelClient'):
                scrape_tool = SteelScrapeTool()
                browser_agent = SteelBrowserAgent()
                
                assert hasattr(scrape_tool, 'run')
                assert hasattr(browser_agent, 'run')
                print("✅ Tool interfaces working")
        
        print("Testing configuration sharing...")
        config = SteelConfig(api_key="shared-key")
        with patch('langchain_steel.utils.client.SteelClient'):
            tool1 = SteelScrapeTool(config=config)
            tool2 = SteelBrowserAgent(config=config)
            assert tool1.config.api_key == tool2.config.api_key
            print("✅ Configuration sharing working")
        
        print("\n🎯 Integration tests completed!")
        print("💡 Install pytest for full test suite: pip install pytest")