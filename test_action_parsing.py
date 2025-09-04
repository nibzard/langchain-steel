#!/usr/bin/env python3
"""Quick test of the action parsing fix."""

import sys
import os
sys.path.append('langchain-steel')

from langchain_steel.agents.claude_computer_use import ActionBatcher

# Test the action parsing logic
def test_action_parsing():
    """Test how we parse different Claude tool input formats."""
    
    test_cases = [
        # Standard format (expected)
        {"action": "screenshot"}, 
        
        # Alternative format Claude sometimes sends
        {"screenshot": True},
        
        # Other possible formats
        {"left_click": [100, 200]},
        {"type": "hello world"},
        {"key": "Enter"},
        
        # Edge case
        {"unknown_field": "value"}
    ]
    
    for i, tool_input in enumerate(test_cases):
        print(f"\nTest {i+1}: {tool_input}")
        
        # Simulate the action detection logic from our fix
        action = tool_input.get("action")
        
        if action is None:
            action_keys = ["screenshot", "left_click", "right_click", "type", "key", 
                         "scroll", "mouse_move", "left_click_drag", "double_click",
                         "triple_click", "middle_click", "cursor_position"]
            for key in action_keys:
                if key in tool_input:
                    action = key
                    break
        
        if action is None:
            action = "screenshot"  # Default fallback
        
        print(f"  → Detected action: '{action}'")

if __name__ == "__main__":
    print("🧪 Testing Action Parsing Logic")
    print("=" * 40)
    test_action_parsing()
    print("\n✅ Action parsing test completed!")