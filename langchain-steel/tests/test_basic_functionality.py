#!/usr/bin/env python3
"""
Basic functionality tests for Steel-LangChain integration.

This test suite covers the core functionality without requiring a real Steel API key.
It focuses on initialization, configuration, and structural validation.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from langchain_steel import SteelScrapeTool, SteelBrowserAgent, SteelConfig
from langchain_steel.utils.errors import SteelError, SteelContentError, SteelConfigError
from langchain_steel.tools.scrape import SteelScrapeInput
from langchain_steel.agents.browser_agent import SteelBrowserAgentInput


class TestSteelConfig:
    """Test Steel configuration management."""
    
    def test_config_creation_with_api_key(self):
        """Test creating configuration with API key."""
        config = SteelConfig(api_key="test-key")
        assert config.api_key == "test-key"
        assert config.default_format.value == "markdown"
        assert config.session_timeout == 300
        
    def test_config_validation_missing_api_key(self):
        """Test validation fails with missing API key."""
        with pytest.raises(SteelConfigError):
            SteelConfig(api_key="")
    
    def test_config_from_env_with_mock_key(self):
        """Test configuration from environment variables."""
        with patch.dict(os.environ, {"STEEL_API_KEY": "mock-key"}):
            config = SteelConfig.from_env()
            assert config.api_key == "mock-key"
    
    def test_config_defaults(self):
        """Test default configuration values."""
        config = SteelConfig(api_key="test")
        assert config.base_url == "https://api.steel.dev"
        assert config.use_proxy is False  # Default to False for hobby plan compatibility
        assert config.solve_captcha is False  # Default to False for hobby plan compatibility
        assert config.stealth_mode is False  # Default to False for hobby plan compatibility
        assert config.max_retries == 3
        
    def test_config_invalid_values(self):
        """Test configuration validation with invalid values."""
        with pytest.raises(SteelConfigError):
            SteelConfig(api_key="test", session_timeout=-1)
            
        with pytest.raises(SteelConfigError):
            SteelConfig(api_key="test", api_timeout=-1)


class TestSteelScrapeTool:
    """Test Steel scrape tool functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Provide a mock configuration."""
        return SteelConfig(api_key="mock-api-key")
    
    @pytest.fixture
    def scrape_tool(self, mock_config):
        """Provide a configured scrape tool."""
        with patch('langchain_steel.utils.client.SteelClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            tool = SteelScrapeTool(config=mock_config)
            tool._client = mock_client
            return tool
    
    def test_tool_initialization(self, mock_config):
        """Test basic tool initialization."""
        with patch('langchain_steel.utils.client.SteelClient'):
            tool = SteelScrapeTool(config=mock_config)
            assert tool.name == "steel_scrape"
            assert "scrape content" in tool.description.lower()
            assert tool.args_schema == SteelScrapeInput
    
    def test_input_schema_validation(self):
        """Test input schema validation."""
        # Valid input
        valid_input = SteelScrapeInput(url="https://example.com")
        assert valid_input.url == "https://example.com"
        assert valid_input.format == "markdown"
        assert valid_input.screenshot is False
        
        # Input with all fields
        full_input = SteelScrapeInput(
            url="https://example.com",
            format="html",
            wait_for_selector=".content",
            delay_ms=1000,
            screenshot=True,
            extract_images=True,
            extract_links=True,
            custom_headers={"X-Test": "value"}
        )
        assert full_input.format == "html"
        assert full_input.screenshot is True
        assert full_input.custom_headers["X-Test"] == "value"
    
    def test_format_validation(self, scrape_tool):
        """Test output format validation."""
        # Mock the client scrape method
        scrape_tool._client.scrape.return_value = {"content": "test content"}
        
        # Valid format should work
        result = scrape_tool._run("https://example.com", format="markdown")
        assert isinstance(result, str)
        
        # Invalid format should return error message
        result = scrape_tool._run("https://example.com", format="invalid")
        assert "Invalid format" in result
    
    def test_content_extraction(self, scrape_tool):
        """Test content extraction from Steel responses."""
        # Test dict response with content
        response = {"content": "test content"}
        content = scrape_tool._extract_content_from_response(response, "https://example.com", "markdown")
        assert content == "test content"
        
        # Test dict response with alternative keys
        response = {"data": "alternative content"}
        content = scrape_tool._extract_content_from_response(response, "https://example.com", "markdown")
        assert content == "alternative content"
        
        # Test string response
        response = "direct string content"
        content = scrape_tool._extract_content_from_response(response, "https://example.com", "markdown")
        assert content == "direct string content"
    
    def test_metadata_extraction(self, scrape_tool):
        """Test metadata extraction from responses."""
        response = {
            "title": "Test Page",
            "final_url": "https://example.com/final",
            "status_code": 200,
            "load_time": 1500,
            "images": [{"src": "image1.jpg"}, {"src": "image2.jpg"}],
            "links": [{"href": "link1.html", "text": "Link 1"}],
            "screenshot": "screenshot.png"
        }
        
        metadata = scrape_tool._extract_metadata_summary(response)
        assert "Title: Test Page" in metadata
        assert "Status Code: 200" in metadata
        assert "Images Found: 2" in metadata
        assert "Links Found: 1" in metadata
        assert "Screenshot: screenshot.png" in metadata


class TestSteelBrowserAgent:
    """Test Steel browser agent functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Provide a mock configuration."""
        return SteelConfig(api_key="mock-api-key")
    
    @pytest.fixture
    def browser_agent(self, mock_config):
        """Provide a configured browser agent."""
        with patch('langchain_steel.utils.client.SteelClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            agent = SteelBrowserAgent(config=mock_config)
            agent._client = mock_client
            return agent
    
    def test_agent_initialization(self, mock_config):
        """Test basic agent initialization."""
        with patch('langchain_steel.utils.client.SteelClient'):
            agent = SteelBrowserAgent(config=mock_config)
            assert "steel_browser_agent" in agent.name
            assert "browser automation" in agent.description.lower()
            assert agent.args_schema == SteelBrowserAgentInput
    
    def test_input_schema_validation(self):
        """Test browser agent input validation."""
        # Basic input
        basic_input = SteelBrowserAgentInput(task="Go to Google and search")
        assert basic_input.task == "Go to Google and search"
        assert basic_input.max_steps == 50
        assert basic_input.return_format == "text"
        
        # Advanced input
        advanced_input = SteelBrowserAgentInput(
            task="Complex navigation task",
            session_id="test-session",
            max_steps=100,
            session_options={"stealth_mode": True},
            return_format="json"
        )
        assert advanced_input.session_id == "test-session"
        assert advanced_input.max_steps == 100
        assert advanced_input.session_options["stealth_mode"] is True
        assert advanced_input.return_format == "json"


class TestErrorHandling:
    """Test error handling functionality."""
    
    def test_steel_error_creation(self):
        """Test Steel error creation."""
        error = SteelError("Test error message")
        assert str(error) == "Test error message"
    
    def test_steel_content_error_creation(self):
        """Test Steel content error with metadata."""
        error = SteelContentError(
            "Content extraction failed",
            url="https://example.com",
            format_requested="markdown"
        )
        assert "Content extraction failed" in str(error)
        assert error.url == "https://example.com"
        assert error.format_requested == "markdown"
    
    def test_steel_config_error_creation(self):
        """Test Steel configuration error."""
        error = SteelConfigError("Invalid configuration")
        assert "Invalid configuration" in str(error)


class TestIntegrationStructure:
    """Test overall integration structure and imports."""
    
    def test_main_imports(self):
        """Test that main components can be imported."""
        from langchain_steel import SteelScrapeTool, SteelBrowserAgent, SteelConfig
        from langchain_steel import __version__
        
        assert __version__ == "0.1.0"
        assert SteelScrapeTool is not None
        assert SteelBrowserAgent is not None
        assert SteelConfig is not None
    
    def test_tool_imports(self):
        """Test tool-specific imports."""
        from langchain_steel.tools import SteelScrapeTool, BaseSteelTool
        from langchain_steel.tools.scrape import SteelScrapeInput
        
        assert SteelScrapeTool is not None
        assert BaseSteelTool is not None
        assert SteelScrapeInput is not None
    
    def test_agent_imports(self):
        """Test agent-specific imports."""
        from langchain_steel.agents import SteelBrowserAgent
        from langchain_steel.agents.browser_agent import SteelBrowserAgentInput
        
        assert SteelBrowserAgent is not None
        assert SteelBrowserAgentInput is not None
    
    def test_utils_imports(self):
        """Test utility imports."""
        from langchain_steel.utils import SteelConfig
        from langchain_steel.utils.config import OutputFormat
        from langchain_steel.utils.errors import SteelError, SteelContentError, SteelConfigError
        
        assert SteelConfig is not None
        assert OutputFormat is not None
        assert SteelError is not None
        assert SteelContentError is not None
        assert SteelConfigError is not None


class TestMockIntegration:
    """Test integration behavior with mock Steel API."""
    
    def test_tool_creation_with_mock_key(self):
        """Test tool creation with mock API key."""
        with patch.dict(os.environ, {"STEEL_API_KEY": "mock-key"}):
            with patch('langchain_steel.utils.client.SteelClient'):
                tool = SteelScrapeTool()
                assert tool.name == "steel_scrape"
    
    def test_agent_creation_with_mock_key(self):
        """Test agent creation with mock API key."""
        with patch.dict(os.environ, {"STEEL_API_KEY": "mock-key"}):
            with patch('langchain_steel.utils.client.SteelClient'):
                agent = SteelBrowserAgent()
                assert "steel_browser_agent" in agent.name
    
    def test_config_with_all_options(self):
        """Test configuration with all options."""
        config = SteelConfig(
            api_key="test-key",
            base_url="https://custom.api.com",
            default_format="html",
            session_timeout=600,
            api_timeout=120000,
            use_proxy=False,
            solve_captcha=False,
            stealth_mode=False,
            max_retries=5,
            retry_delay=2.0,
            user_agent="Custom Agent",
            enable_logging=True
        )
        
        assert config.api_key == "test-key"
        assert config.base_url == "https://custom.api.com"
        assert config.default_format == "html" or config.default_format.value == "html"
        assert config.session_timeout == 600
        assert config.use_proxy is False
        assert config.max_retries == 5


if __name__ == "__main__":
    # Run tests with pytest if available, otherwise run basic checks
    try:
        import pytest
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not available, running basic functionality checks...")
        
        # Basic functionality checks
        print("Testing imports...")
        from langchain_steel import SteelScrapeTool, SteelBrowserAgent, SteelConfig
        print("✅ All imports successful")
        
        print("Testing configuration...")
        config = SteelConfig(api_key="test-key")
        print(f"✅ Configuration created: {config.api_key}")
        
        print("Testing input schemas...")
        scrape_input = SteelScrapeInput(url="https://example.com")
        browser_input = SteelBrowserAgentInput(task="test task")
        print("✅ Input schemas working")
        
        print("\n🎯 Basic functionality tests completed!")
        print("💡 Install pytest for full test suite: pip install pytest")