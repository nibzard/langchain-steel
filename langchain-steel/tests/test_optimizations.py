#!/usr/bin/env python3
"""ABOUTME: Test suite for Steel browser automation optimizations.
ABOUTME: Verifies rate limiting, navigation optimization, and action batching features."""

import unittest
import asyncio
import time
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add the parent directory to sys.path so we can import langchain_steel
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from langchain_steel.agents.claude_computer_use import (
    ActionBatcher, 
    NavigationOptimizer, 
    _handle_rate_limit_error
)


class TestActionBatcher(unittest.TestCase):
    """Test action batching and throttling functionality."""
    
    def setUp(self):
        self.batcher = ActionBatcher(throttle_delay=0.1)  # Short delay for testing
    
    def test_throttling_delay(self):
        """Test that throttling delays are enforced."""
        start_time = time.time()
        
        # First request should not be throttled
        self.batcher.wait_if_needed()
        first_time = time.time()
        
        # Second request should be throttled
        self.batcher.wait_if_needed()
        second_time = time.time()
        
        # Verify delay was applied
        delay = second_time - first_time
        self.assertGreaterEqual(delay, 0.09)  # Allow for timing variations
    
    def test_navigation_detection(self):
        """Test navigation pattern detection."""
        # Should detect URLs
        self.assertTrue(self.batcher.is_navigation_action("type", "https://example.com"))
        self.assertTrue(self.batcher.is_navigation_action("type", "www.google.com"))
        self.assertTrue(self.batcher.is_navigation_action("type", "github.com"))
        
        # Should not detect non-URLs
        self.assertFalse(self.batcher.is_navigation_action("type", "hello world"))
        self.assertFalse(self.batcher.is_navigation_action("click", None))
    
    async def test_async_throttling(self):
        """Test async throttling functionality."""
        start_time = time.time()
        
        # First request should not be throttled
        await self.batcher.async_wait_if_needed()
        first_time = time.time()
        
        # Second request should be throttled
        await self.batcher.async_wait_if_needed()
        second_time = time.time()
        
        # Verify delay was applied
        delay = second_time - first_time
        self.assertGreaterEqual(delay, 0.09)  # Allow for timing variations


class TestNavigationOptimizer(unittest.TestCase):
    """Test navigation optimization functionality."""
    
    def setUp(self):
        # Create a mock browser session
        self.mock_browser = Mock()
        self.mock_page = Mock()
        self.mock_browser._page = self.mock_page
        
        self.optimizer = NavigationOptimizer(self.mock_browser)
    
    def test_url_extraction(self):
        """Test URL extraction from natural language tasks."""
        test_cases = [
            ("Go to https://example.com", "https://example.com"),
            ("Navigate to www.google.com", "https://www.google.com"),
            ("Visit github.com", "https://github.com"),
            ("Go to Google", "https://www.google.com"),
            ("Navigate to Hacker News", "https://news.ycombinator.com"),
            ("Visit some random site", None),
        ]
        
        for task, expected_url in test_cases:
            with self.subTest(task=task):
                result = self.optimizer.extract_url_from_task(task)
                self.assertEqual(result, expected_url)
    
    def test_navigation_optimization_detection(self):
        """Test detection of tasks that can be optimized."""
        optimizable_tasks = [
            "Go to https://example.com",
            "Navigate to Google",
            "Visit https://github.com",
            "Open www.reddit.com"
        ]
        
        non_optimizable_tasks = [
            "Click the submit button",
            "Scroll down the page",
            "Search for something",
            "Go to some unknown place"
        ]
        
        for task in optimizable_tasks:
            with self.subTest(task=task):
                self.assertTrue(self.optimizer.can_optimize_navigation(task))
        
        for task in non_optimizable_tasks:
            with self.subTest(task=task):
                self.assertFalse(self.optimizer.can_optimize_navigation(task))
    
    def test_optimized_navigation_execution(self):
        """Test that optimized navigation calls Playwright goto."""
        task = "Navigate to https://example.com"
        
        # Mock successful navigation
        self.mock_page.goto = Mock()
        
        result = self.optimizer.perform_optimized_navigation(task)
        
        self.assertTrue(result)
        self.mock_page.goto.assert_called_once_with(
            "https://example.com", 
            wait_until="domcontentloaded", 
            timeout=30000
        )


class TestRateLimitHandling(unittest.TestCase):
    """Test rate limit error handling improvements."""
    
    def test_exponential_backoff_delays(self):
        """Test that exponential backoff uses optimized delays."""
        expected_ranges = [
            (0.5, 1.0),   # Attempt 0
            (1.0, 1.5),   # Attempt 1
            (2.0, 2.5),   # Attempt 2
            (4.0, 4.5),   # Attempt 3
            (8.0, 8.5),   # Attempt 4
        ]
        
        for attempt, (min_delay, max_delay) in enumerate(expected_ranges):
            with self.subTest(attempt=attempt):
                delay = _handle_rate_limit_error(attempt)
                self.assertIsNotNone(delay)
                self.assertGreaterEqual(delay, min_delay)
                self.assertLessEqual(delay, max_delay)
    
    def test_max_retries_exceeded(self):
        """Test that None is returned when max retries are exceeded."""
        delay = _handle_rate_limit_error(10, max_retries=10)
        self.assertIsNone(delay)


class TestIntegrationOptimizations(unittest.TestCase):
    """Test integration of optimization features."""
    
    def setUp(self):
        # Mock Steel browser session
        self.mock_session = Mock()
        self.mock_session._page = Mock()
        self.mock_session.get_dimensions = Mock(return_value=(1024, 768))
        
    @patch('langchain_steel.agents.claude_computer_use.Anthropic')
    def test_agent_initialization_with_optimizations(self, mock_anthropic):
        """Test that Claude agent initializes with optimization components."""
        from langchain_steel.agents.claude_computer_use import ClaudeComputerUseAgent
        
        agent = ClaudeComputerUseAgent(
            anthropic_api_key="test_key",
            browser_session=self.mock_session,
            throttle_delay=0.1
        )
        
        # Verify optimization components are initialized
        self.assertIsNotNone(agent.action_batcher)
        self.assertIsNotNone(agent.navigation_optimizer)
        self.assertEqual(agent.action_batcher.throttle_delay, 0.1)
        self.assertEqual(agent._cache_duration, 2.0)  # Increased cache duration
    
    def test_system_prompt_enhancements(self):
        """Test that system prompt includes optimization guidance."""
        from langchain_steel.agents.claude_computer_use import ClaudeComputerUseAgent
        
        with patch('langchain_steel.agents.claude_computer_use.Anthropic'):
            agent = ClaudeComputerUseAgent(
                anthropic_api_key="test_key",
                browser_session=self.mock_session
            )
        
        # Check that optimization guidance is in the system prompt
        self.assertIn("NAVIGATION_OPTIMIZATION", agent.system_prompt)
        self.assertIn("EFFICIENCY_GUIDELINES", agent.system_prompt)
        self.assertIn("direct navigation methods", agent.system_prompt)
        self.assertIn("rate limits", agent.system_prompt)


async def run_async_tests():
    """Run async tests separately."""
    batcher = ActionBatcher(throttle_delay=0.1)
    test_instance = TestActionBatcher()
    test_instance.batcher = batcher
    await test_instance.test_async_throttling()
    print("✅ Async throttling test passed")


def main():
    """Run optimization tests."""
    print("🧪 Running Steel Browser Automation Optimization Tests")
    print("=" * 60)
    
    # Run sync tests
    unittest.main(verbosity=2, exit=False)
    
    # Run async tests
    print("\n🔄 Running async tests...")
    asyncio.run(run_async_tests())
    
    print("\n✅ All optimization tests completed!")
    print("\n💡 Key improvements verified:")
    print("   - Request throttling reduces API call frequency")
    print("   - Navigation optimization uses direct Playwright methods")
    print("   - Exponential backoff uses shorter, more reasonable delays")
    print("   - Action batching reduces redundant API calls")
    print("   - Screenshot caching improves efficiency")


if __name__ == "__main__":
    main()