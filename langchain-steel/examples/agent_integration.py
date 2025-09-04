#!/usr/bin/env python3
"""
LangChain Agent Integration Example using Steel-LangChain Integration

This example demonstrates how to integrate Steel tools with LangChain agents
for complex AI-driven workflows and conversational interfaces.

Requirements:
- Set STEEL_API_KEY environment variable
- Set OPENAI_API_KEY environment variable (for LLM integration)
- Install langchain-steel, langchain, and langchain-openai packages
"""

import os
import sys
from typing import List, Optional

# Add the parent directory to sys.path so we can import langchain_steel
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from langchain_steel import SteelScrapeTool, SteelBrowserAgent, SteelConfig


def check_environment():
    """Check if required API keys and packages are available."""
    print("🔍 Environment Check")
    print("=" * 30)
    
    # Check Steel API key
    steel_key = os.environ.get('STEEL_API_KEY')
    if steel_key:
        print("✅ STEEL_API_KEY found")
    else:
        print("⚠️  STEEL_API_KEY not set - using mock behavior")
    
    # Check OpenAI API key
    openai_key = os.environ.get('OPENAI_API_KEY')
    if openai_key:
        print("✅ OPENAI_API_KEY found")
    else:
        print("⚠️  OPENAI_API_KEY not set - will skip LLM integration")
    
    # Check LangChain packages
    packages_to_check = [
        ('langchain', 'LangChain core'),
        ('langchain_openai', 'OpenAI integration'),
        ('langchain_community', 'Community tools')
    ]
    
    available_packages = []
    for package, description in packages_to_check:
        try:
            __import__(package)
            print(f"✅ {description} available")
            available_packages.append(package)
        except ImportError:
            print(f"❌ {description} not available")
    
    return steel_key, openai_key, available_packages


def basic_tool_integration_example():
    """Demonstrate basic Steel tool integration with LangChain."""
    print("\n🔧 Basic Tool Integration Example")
    print("=" * 50)
    
    # Create Steel tools
    try:
        scrape_tool = SteelScrapeTool()
        browser_agent = SteelBrowserAgent()
        
        tools = [scrape_tool, browser_agent]
        
        print("✅ Steel tools created successfully:")
        for tool in tools:
            print(f"   • {tool.name}: {tool.description[:60]}...")
        
        # Show tool schemas
        print(f"\n📋 Tool Schemas:")
        for tool in tools:
            print(f"\n🔧 {tool.name}:")
            print(f"   Args schema: {tool.args_schema.__name__}")
            if hasattr(tool.args_schema, '__fields__'):
                print(f"   Fields: {list(tool.args_schema.__fields__.keys())}")
        
    except Exception as e:
        print(f"❌ Tool integration failed: {e}")
        return None
    
    return tools


def mock_agent_example(tools):
    """Demonstrate agent behavior without requiring OpenAI API key."""
    print("\n🔧 Mock Agent Example (No OpenAI API Required)")
    print("=" * 50)
    
    if not tools:
        print("❌ No tools available for mock agent")
        return
    
    # Simulate agent queries and responses
    mock_queries = [
        {
            "query": "Scrape the content from example.com",
            "expected_tool": "steel_scrape",
            "mock_response": "I would use the steel_scrape tool to extract content from example.com in markdown format."
        },
        {
            "query": "Go to Google and search for 'Steel automation'",
            "expected_tool": "steel_browser_agent",
            "mock_response": "I would use the steel_browser_agent tool to navigate to Google and perform a search."
        },
        {
            "query": "Find all links on a webpage and summarize the content",
            "expected_tool": "steel_scrape",
            "mock_response": "I would use steel_scrape with extract_links=True to get both content and links, then summarize."
        }
    ]
    
    for i, query_info in enumerate(mock_queries, 1):
        query = query_info["query"]
        expected_tool = query_info["expected_tool"]
        mock_response = query_info["mock_response"]
        
        print(f"\n🤖 Query {i}: {query}")
        print(f"🎯 Expected tool: {expected_tool}")
        print(f"💭 Mock response: {mock_response}")
        
        # Find the matching tool
        matching_tool = None
        for tool in tools:
            if tool.name == expected_tool:
                matching_tool = tool
                break
        
        if matching_tool:
            print(f"✅ Tool '{expected_tool}' is available and ready")
        else:
            print(f"❌ Tool '{expected_tool}' not found")
    
    print("\n🎯 Mock agent examples completed!")


def real_agent_example(tools, openai_key):
    """Demonstrate real LangChain agent integration with OpenAI."""
    print("\n🔧 Real Agent Integration Example")
    print("=" * 50)
    
    if not openai_key:
        print("⚠️  Skipping real agent example - OPENAI_API_KEY not set")
        return
    
    if not tools:
        print("❌ No tools available for real agent")
        return
    
    try:
        from langchain.agents import AgentType, initialize_agent
        from langchain_openai import OpenAI
        
        # Initialize LLM
        llm = OpenAI(temperature=0, openai_api_key=openai_key)
        print("✅ OpenAI LLM initialized")
        
        # Create agent
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )
        print("✅ LangChain agent created with Steel tools")
        
        # Example queries
        queries = [
            "What is the main content of example.com?",
            "Can you browse to httpbin.org and tell me what services it offers?"
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"\n🤖 Agent Query {i}: {query}")
            print("-" * 40)
            
            try:
                response = agent.run(query)
                print(f"✅ Agent Response: {response}")
            except Exception as e:
                print(f"❌ Agent query failed: {e}")
        
        print("\n🎯 Real agent integration completed!")
        
    except ImportError as e:
        print(f"❌ Required packages not available: {e}")
    except Exception as e:
        print(f"❌ Real agent integration failed: {e}")


def conversational_agent_example(tools, openai_key):
    """Demonstrate conversational agent with Steel tools."""
    print("\n🔧 Conversational Agent Example")
    print("=" * 50)
    
    if not openai_key:
        print("⚠️  Skipping conversational agent - OPENAI_API_KEY not set")
        return
    
    try:
        from langchain.agents import AgentType, initialize_agent
        from langchain.memory import ConversationBufferMemory
        from langchain_openai import OpenAI
        
        # Initialize LLM with memory
        memory = ConversationBufferMemory(memory_key="chat_history")
        llm = OpenAI(temperature=0.1, openai_api_key=openai_key)
        
        # Create conversational agent
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=memory,
            verbose=True
        )
        
        print("✅ Conversational agent with memory created")
        
        # Simulate conversation
        conversation = [
            "Hi! Can you help me scrape some web content?",
            "Please get the content from example.com",
            "Now can you also check what's on httpbin.org?",
            "Compare the two websites you just visited"
        ]
        
        for i, message in enumerate(conversation, 1):
            print(f"\n👤 User {i}: {message}")
            print("-" * 40)
            
            try:
                response = agent.run(input=message)
                print(f"🤖 Assistant: {response}")
            except Exception as e:
                print(f"❌ Conversation failed: {e}")
                break
        
        print("\n🎯 Conversational agent example completed!")
        
    except ImportError as e:
        print(f"❌ Required packages for conversation not available: {e}")
    except Exception as e:
        print(f"❌ Conversational agent failed: {e}")


def custom_workflow_example(tools):
    """Demonstrate custom workflow using Steel tools."""
    print("\n🔧 Custom Workflow Example")
    print("=" * 50)
    
    if not tools:
        print("❌ No tools available for workflow")
        return
    
    # Find available tools
    scrape_tool = None
    browser_agent = None
    
    for tool in tools:
        if tool.name == "steel_scrape":
            scrape_tool = tool
        elif tool.name == "steel_browser_agent":
            browser_agent = tool
    
    print("🔄 Simulating a custom research workflow...")
    
    # Step 1: Initial scraping
    if scrape_tool:
        print(f"\n1️⃣ Step 1: Basic content extraction")
        try:
            # This would be a real call with API key
            print(f"   🔧 Using {scrape_tool.name} to scrape example.com")
            print(f"   ✅ Content extracted (simulated)")
        except Exception as e:
            print(f"   ❌ Scraping failed: {e}")
    
    # Step 2: Interactive browsing
    if browser_agent:
        print(f"\n2️⃣ Step 2: Interactive browsing")
        try:
            print(f"   🔧 Using {browser_agent.name} for complex navigation")
            print(f"   ✅ Navigation completed (simulated)")
        except Exception as e:
            print(f"   ❌ Browsing failed: {e}")
    
    # Step 3: Data synthesis
    print(f"\n3️⃣ Step 3: Data synthesis")
    print(f"   🔄 Combining results from multiple sources")
    print(f"   ✅ Synthesis completed (simulated)")
    
    # Step 4: Report generation
    print(f"\n4️⃣ Step 4: Report generation")
    print(f"   📊 Generating comprehensive report")
    print(f"   ✅ Report ready (simulated)")
    
    print("\n🎯 Custom workflow example completed!")
    print("💡 This demonstrates how Steel tools can be orchestrated in complex workflows")


def performance_monitoring_example(tools):
    """Demonstrate performance monitoring of Steel tools."""
    print("\n🔧 Performance Monitoring Example")
    print("=" * 50)
    
    if not tools:
        print("❌ No tools available for monitoring")
        return
    
    import time
    
    print("📊 Simulating performance monitoring...")
    
    for tool in tools:
        print(f"\n🔧 Monitoring {tool.name}:")
        
        # Simulate performance metrics
        simulated_metrics = {
            "response_time": f"{round(0.5 + (hash(tool.name) % 100) / 100, 2)}s",
            "success_rate": f"{95 + (hash(tool.name) % 5)}%",
            "average_content_size": f"{1000 + (hash(tool.name) % 2000)} chars",
            "sessions_active": hash(tool.name) % 10,
            "last_error": None if hash(tool.name) % 3 else "Rate limit exceeded"
        }
        
        for metric, value in simulated_metrics.items():
            status = "✅" if metric != "last_error" or value is None else "⚠️ "
            print(f"   {status} {metric}: {value}")
    
    print(f"\n📈 Performance Summary:")
    print(f"   • All tools operational: ✅")
    print(f"   • Average response time: <1s")
    print(f"   • Overall success rate: >95%")
    
    print("\n🎯 Performance monitoring example completed!")


def main():
    """Run all agent integration examples."""
    print("🚀 Steel-LangChain Agent Integration Examples")
    print("=" * 60)
    
    try:
        # Check environment
        steel_key, openai_key, packages = check_environment()
        
        # Run examples based on available resources
        tools = basic_tool_integration_example()
        
        if tools:
            mock_agent_example(tools)
            
            if 'langchain' in packages and 'langchain_openai' in packages:
                real_agent_example(tools, openai_key)
                conversational_agent_example(tools, openai_key)
            else:
                print("\n⚠️  Skipping LLM-based examples - LangChain packages not available")
            
            custom_workflow_example(tools)
            performance_monitoring_example(tools)
        
        print("\n✅ Agent integration examples completed!")
        print("\n💡 Next steps:")
        print("   - Set STEEL_API_KEY and OPENAI_API_KEY for full functionality")
        print("   - Install missing packages: pip install langchain langchain-openai")
        print("   - Create custom agents for your specific use cases")
        print("   - Integrate with vector databases for RAG applications")
        
    except KeyboardInterrupt:
        print("\n⚠️  Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Examples failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()