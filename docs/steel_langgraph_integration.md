# Steel + LangGraph Integration

LangGraph is LangChain's framework for building stateful, multi-actor applications with LLMs. Steel's browser automation tools integrate seamlessly with LangGraph to create sophisticated web automation workflows with state management, error recovery, and complex decision trees.

## Overview

Steel + LangGraph enables:

- **Stateful web automation**: Maintain context across multiple browser interactions
- **Multi-step workflows**: Complex automation with decision points and branching
- **Error recovery**: Automatic retry and fallback mechanisms  
- **Parallel processing**: Concurrent web operations with state coordination
- **Human-in-the-loop**: Interactive workflows requiring human intervention

## Basic LangGraph Integration

### Simple Web Scraping Workflow

```python
from langgraph import StateGraph, END
from langchain_steel import SteelScrapeTool, SteelExtractTool
from typing_extensions import TypedDict
from typing import List, Dict, Any

class WebScrapingState(TypedDict):
    url: str
    raw_content: str
    structured_data: Dict[str, Any]
    errors: List[str]
    status: str

def scrape_content(state: WebScrapingState) -> WebScrapingState:
    """Scrape raw content from URL."""
    scrape_tool = SteelScrapeTool()
    
    try:
        content = scrape_tool.run({
            "url": state["url"],
            "format": "markdown",
            "wait_for_selector": ".main-content"
        })
        
        return {
            **state,
            "raw_content": content,
            "status": "content_scraped"
        }
    except Exception as e:
        return {
            **state,
            "errors": state["errors"] + [f"Scraping failed: {str(e)}"],
            "status": "scraping_error"
        }

def extract_structured_data(state: WebScrapingState) -> WebScrapingState:
    """Extract structured data from scraped content."""
    extract_tool = SteelExtractTool()
    
    # Define schema for extraction
    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Page title"},
            "summary": {"type": "string", "description": "Brief summary"},
            "key_points": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Main points from content"
            }
        }
    }
    
    try:
        result = extract_tool.run({
            "content": state["raw_content"],
            "schema": schema,
            "instructions": "Extract key information from this content"
        })
        
        return {
            **state,
            "structured_data": result,
            "status": "completed"
        }
    except Exception as e:
        return {
            **state,
            "errors": state["errors"] + [f"Extraction failed: {str(e)}"],
            "status": "extraction_error"
        }

def handle_error(state: WebScrapingState) -> WebScrapingState:
    """Handle errors in the workflow."""
    return {
        **state,
        "status": "failed",
        "errors": state["errors"] + ["Workflow terminated due to errors"]
    }

# Build the workflow
workflow = StateGraph(WebScrapingState)

# Add nodes
workflow.add_node("scrape", scrape_content)
workflow.add_node("extract", extract_structured_data)
workflow.add_node("error_handler", handle_error)

# Add edges
workflow.add_edge("scrape", "extract")
workflow.add_edge("extract", END)

# Add conditional routing for errors
workflow.add_conditional_edges(
    "scrape",
    lambda x: "extract" if x["status"] == "content_scraped" else "error_handler"
)

workflow.add_conditional_edges(
    "extract", 
    lambda x: END if x["status"] == "completed" else "error_handler"
)

workflow.add_edge("error_handler", END)
workflow.set_entry_point("scrape")

# Compile and use
app = workflow.compile()

# Execute workflow
result = app.invoke({
    "url": "https://example.com/article",
    "raw_content": "",
    "structured_data": {},
    "errors": [],
    "status": "initialized"
})

print(f"Final status: {result['status']}")
print(f"Structured data: {result['structured_data']}")
```

## Advanced Multi-Step Automation

### E-commerce Research Pipeline

```python
from langgraph import StateGraph, END
from langchain_steel import SteelBrowserAgent, SteelExtractTool, SteelScreenshotTool
from typing_extensions import TypedDict
from typing import List, Dict, Any, Optional

class EcommerceResearchState(TypedDict):
    search_terms: List[str]
    current_term: str
    retailers: List[str]
    current_retailer: str
    products: Dict[str, List[Dict]]
    screenshots: Dict[str, str]
    comparison_data: Optional[Dict]
    errors: List[str]
    step: str

def initialize_research(state: EcommerceResearchState) -> EcommerceResearchState:
    """Initialize research parameters."""
    return {
        **state,
        "current_term": state["search_terms"][0] if state["search_terms"] else "",
        "current_retailer": state["retailers"][0] if state["retailers"] else "",
        "products": {},
        "screenshots": {},
        "step": "search_products"
    }

def search_products(state: EcommerceResearchState) -> EcommerceResearchState:
    """Search for products on current retailer."""
    browser_agent = SteelBrowserAgent()
    
    search_task = f"""
    1. Navigate to {state["current_retailer"]}
    2. Search for '{state["current_term"]}'
    3. Apply relevant filters (price, rating, availability)
    4. Get first 10 product results with:
       - Product name and price
       - Rating and review count
       - Availability status
       - Product URL
    5. Return structured product data
    """
    
    try:
        result = browser_agent.run(search_task)
        
        # Store products for current retailer
        products = state["products"].copy()
        products[state["current_retailer"]] = result.get("products", [])
        
        return {
            **state,
            "products": products,
            "step": "take_screenshot"
        }
    except Exception as e:
        return {
            **state,
            "errors": state["errors"] + [f"Search failed for {state['current_retailer']}: {str(e)}"],
            "step": "handle_search_error"
        }

def take_screenshot(state: EcommerceResearchState) -> EcommerceResearchState:
    """Capture screenshot of search results."""
    screenshot_tool = SteelScreenshotTool()
    
    try:
        result = screenshot_tool.run({
            "url": f"{state['current_retailer']}/search?q={state['current_term']}",
            "viewport_size": {"width": 1280, "height": 720},
            "wait_for_selector": ".search-results"
        })
        
        screenshots = state["screenshots"].copy()
        screenshots[state["current_retailer"]] = result.get("screenshot")
        
        return {
            **state,
            "screenshots": screenshots,
            "step": "next_retailer"
        }
    except Exception as e:
        return {
            **state,
            "errors": state["errors"] + [f"Screenshot failed: {str(e)}"],
            "step": "next_retailer"  # Continue despite screenshot failure
        }

def next_retailer(state: EcommerceResearchState) -> EcommerceResearchState:
    """Move to next retailer or complete search."""
    current_index = state["retailers"].index(state["current_retailer"])
    
    if current_index + 1 < len(state["retailers"]):
        # Move to next retailer
        return {
            **state,
            "current_retailer": state["retailers"][current_index + 1],
            "step": "search_products"
        }
    else:
        # All retailers processed, move to comparison
        return {
            **state,
            "step": "compare_results"
        }

def compare_results(state: EcommerceResearchState) -> EcommerceResearchState:
    """Compare products across retailers."""
    all_products = []
    
    for retailer, products in state["products"].items():
        for product in products:
            product["retailer"] = retailer
            all_products.append(product)
    
    # Sort by price, rating, etc.
    all_products.sort(key=lambda x: x.get("price", 0))
    
    comparison = {
        "search_term": state["current_term"],
        "total_products": len(all_products),
        "retailers_searched": len(state["products"]),
        "best_deals": all_products[:5],
        "highest_rated": sorted(all_products, key=lambda x: x.get("rating", 0), reverse=True)[:5],
        "price_range": {
            "min": min(p.get("price", 0) for p in all_products) if all_products else 0,
            "max": max(p.get("price", 0) for p in all_products) if all_products else 0
        }
    }
    
    return {
        **state,
        "comparison_data": comparison,
        "step": "completed"
    }

def handle_search_error(state: EcommerceResearchState) -> EcommerceResearchState:
    """Handle search errors and continue with next retailer."""
    return {
        **state,
        "step": "next_retailer"
    }

# Build the workflow
ecommerce_workflow = StateGraph(EcommerceResearchState)

# Add nodes
ecommerce_workflow.add_node("initialize", initialize_research)
ecommerce_workflow.add_node("search", search_products)
ecommerce_workflow.add_node("screenshot", take_screenshot)
ecommerce_workflow.add_node("next", next_retailer)
ecommerce_workflow.add_node("compare", compare_results)
ecommerce_workflow.add_node("error_handler", handle_search_error)

# Add edges and routing
ecommerce_workflow.set_entry_point("initialize")
ecommerce_workflow.add_edge("initialize", "search")

ecommerce_workflow.add_conditional_edges(
    "search",
    lambda x: "screenshot" if x["step"] == "take_screenshot" else "error_handler"
)

ecommerce_workflow.add_edge("screenshot", "next")
ecommerce_workflow.add_edge("error_handler", "next")

ecommerce_workflow.add_conditional_edges(
    "next",
    lambda x: "search" if x["step"] == "search_products" else "compare"
)

ecommerce_workflow.add_edge("compare", END)

# Compile workflow
ecommerce_app = ecommerce_workflow.compile()

# Execute research
research_result = ecommerce_app.invoke({
    "search_terms": ["wireless headphones"],
    "current_term": "",
    "retailers": [
        "https://amazon.com",
        "https://bestbuy.com", 
        "https://target.com"
    ],
    "current_retailer": "",
    "products": {},
    "screenshots": {},
    "comparison_data": None,
    "errors": [],
    "step": "initialized"
})

print(f"Research completed: {research_result['comparison_data']}")
```

## Human-in-the-Loop Workflows

### Content Moderation Pipeline

```python
from langgraph import StateGraph, END
from langchain_steel import SteelScrapeTool, SteelExtractTool
from typing_extensions import TypedDict
import json

class ContentModerationState(TypedDict):
    urls_to_check: List[str]
    current_url: str
    content: str
    analysis: Dict[str, Any]
    human_decision: Optional[str]
    flagged_content: List[Dict]
    approved_content: List[Dict]
    step: str

def scrape_content_for_review(state: ContentModerationState) -> ContentModerationState:
    """Scrape content that needs moderation."""
    scrape_tool = SteelScrapeTool()
    
    current_url = state["urls_to_check"][0] if state["urls_to_check"] else ""
    
    try:
        content = scrape_tool.run({
            "url": current_url,
            "format": "markdown",
            "extract_images": True
        })
        
        return {
            **state,
            "current_url": current_url,
            "content": content,
            "step": "analyze_content"
        }
    except Exception as e:
        return {
            **state,
            "step": "skip_url",
            "errors": state.get("errors", []) + [f"Failed to scrape {current_url}: {e}"]
        }

def analyze_content(state: ContentModerationState) -> ContentModerationState:
    """Analyze content for potential issues."""
    extract_tool = SteelExtractTool()
    
    analysis_schema = {
        "type": "object",
        "properties": {
            "content_type": {"type": "string", "description": "Type of content (article, product, forum post, etc.)"},
            "potential_issues": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of potential content issues"
            },
            "confidence_score": {"type": "number", "description": "Confidence in analysis (0-1)"},
            "requires_human_review": {"type": "boolean", "description": "Whether human review is needed"},
            "summary": {"type": "string", "description": "Brief content summary"}
        }
    }
    
    try:
        analysis = extract_tool.run({
            "content": state["content"],
            "schema": analysis_schema,
            "instructions": """
            Analyze this content for potential policy violations including:
            - Inappropriate language or hate speech
            - Misinformation or false claims
            - Spam or promotional content
            - Copyright violations
            - Privacy concerns
            """
        })
        
        return {
            **state,
            "analysis": analysis,
            "step": "human_review" if analysis.get("requires_human_review") else "auto_approve"
        }
    except Exception as e:
        return {
            **state,
            "step": "human_review",  # Default to human review on error
            "analysis": {"error": str(e)}
        }

def request_human_review(state: ContentModerationState) -> ContentModerationState:
    """Request human input for content decision."""
    
    print("\n" + "="*50)
    print("CONTENT REQUIRING HUMAN REVIEW")
    print("="*50)
    print(f"URL: {state['current_url']}")
    print(f"Content Type: {state['analysis'].get('content_type', 'Unknown')}")
    print(f"Potential Issues: {state['analysis'].get('potential_issues', [])}")
    print(f"Summary: {state['analysis'].get('summary', 'No summary available')}")
    print("\nContent Preview:")
    print(state["content"][:500] + "..." if len(state["content"]) > 500 else state["content"])
    print("\nOptions:")
    print("1. approve - Approve content")
    print("2. reject - Reject content")
    print("3. flag - Flag for further review")
    print("4. edit - Request content changes")
    
    decision = input("\nYour decision: ").lower().strip()
    
    return {
        **state,
        "human_decision": decision,
        "step": "process_decision"
    }

def process_human_decision(state: ContentModerationState) -> ContentModerationState:
    """Process human moderation decision."""
    
    content_item = {
        "url": state["current_url"],
        "analysis": state["analysis"],
        "human_decision": state["human_decision"],
        "timestamp": "2024-01-15T10:30:00Z"
    }
    
    if state["human_decision"] in ["approve", "1"]:
        approved = state["approved_content"] + [content_item]
        return {**state, "approved_content": approved, "step": "next_url"}
    
    else:  # reject, flag, edit, or any other input
        flagged = state["flagged_content"] + [content_item]
        return {**state, "flagged_content": flagged, "step": "next_url"}

def auto_approve_content(state: ContentModerationState) -> ContentModerationState:
    """Automatically approve content that passes analysis."""
    
    content_item = {
        "url": state["current_url"],
        "analysis": state["analysis"],
        "human_decision": "auto_approved",
        "timestamp": "2024-01-15T10:30:00Z"
    }
    
    approved = state["approved_content"] + [content_item]
    
    return {
        **state,
        "approved_content": approved,
        "step": "next_url"
    }

def process_next_url(state: ContentModerationState) -> ContentModerationState:
    """Move to next URL or complete workflow."""
    
    remaining_urls = state["urls_to_check"][1:]  # Remove current URL
    
    if remaining_urls:
        return {
            **state,
            "urls_to_check": remaining_urls,
            "step": "scrape_content"
        }
    else:
        return {
            **state,
            "step": "completed"
        }

# Build moderation workflow
moderation_workflow = StateGraph(ContentModerationState)

moderation_workflow.add_node("scrape", scrape_content_for_review)
moderation_workflow.add_node("analyze", analyze_content)
moderation_workflow.add_node("human_review", request_human_review)
moderation_workflow.add_node("process_decision", process_human_decision)
moderation_workflow.add_node("auto_approve", auto_approve_content)
moderation_workflow.add_node("next_url", process_next_url)

moderation_workflow.set_entry_point("scrape")

moderation_workflow.add_conditional_edges(
    "scrape",
    lambda x: "analyze" if x["step"] == "analyze_content" else "next_url"
)

moderation_workflow.add_conditional_edges(
    "analyze",
    lambda x: "human_review" if x["step"] == "human_review" else "auto_approve"
)

moderation_workflow.add_edge("human_review", "process_decision")
moderation_workflow.add_edge("process_decision", "next_url")
moderation_workflow.add_edge("auto_approve", "next_url")

moderation_workflow.add_conditional_edges(
    "next_url",
    lambda x: "scrape" if x["step"] == "scrape_content" else END
)

# Compile and run
moderation_app = moderation_workflow.compile()

# Execute moderation workflow
moderation_result = moderation_app.invoke({
    "urls_to_check": [
        "https://forum.example.com/post/123",
        "https://blog.example.com/controversial-topic",
        "https://news.example.com/breaking-news"
    ],
    "current_url": "",
    "content": "",
    "analysis": {},
    "human_decision": None,
    "flagged_content": [],
    "approved_content": [],
    "step": "initialized"
})

print(f"Moderation completed:")
print(f"Approved: {len(moderation_result['approved_content'])} items")
print(f"Flagged: {len(moderation_result['flagged_content'])} items")
```

## Parallel Processing with State Coordination

### Competitive Intelligence Gathering

```python
from langgraph import StateGraph, END
from langchain_steel import SteelBrowserAgent, SteelExtractTool
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing_extensions import TypedDict

class CompetitiveIntelligenceState(TypedDict):
    competitors: List[Dict[str, str]]  # [{"name": "Company A", "website": "..."}]
    intelligence_data: Dict[str, Dict]
    analysis_complete: List[str]
    errors: Dict[str, List[str]]
    step: str

def gather_competitor_data(state: CompetitiveIntelligenceState) -> CompetitiveIntelligenceState:
    """Gather data from all competitors in parallel."""
    
    def analyze_single_competitor(competitor: Dict[str, str]) -> Dict[str, Any]:
        """Analyze a single competitor."""
        browser_agent = SteelBrowserAgent()
        
        analysis_task = f"""
        Research {competitor['name']} at {competitor['website']}:
        
        1. Visit their homepage and main product pages
        2. Gather information about:
           - Product offerings and pricing
           - Company size and team information  
           - Recent news and announcements
           - Customer testimonials or case studies
           - Technology stack or methodology
        3. Visit their careers page for hiring insights
        4. Check their blog for thought leadership content
        5. Return comprehensive competitive intelligence
        """
        
        try:
            result = browser_agent.run(analysis_task)
            return {
                "success": True,
                "data": result,
                "competitor": competitor["name"]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "competitor": competitor["name"]
            }
    
    # Process competitors in parallel
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(analyze_single_competitor, comp) 
            for comp in state["competitors"]
        ]
        
        results = [future.result() for future in futures]
    
    # Process results
    intelligence_data = {}
    errors = {}
    analysis_complete = []
    
    for result in results:
        comp_name = result["competitor"]
        
        if result["success"]:
            intelligence_data[comp_name] = result["data"]
            analysis_complete.append(comp_name)
        else:
            errors[comp_name] = [result["error"]]
    
    return {
        **state,
        "intelligence_data": intelligence_data,
        "analysis_complete": analysis_complete,
        "errors": errors,
        "step": "synthesize_insights"
    }

def synthesize_competitive_insights(state: CompetitiveIntelligenceState) -> CompetitiveIntelligenceState:
    """Synthesize insights across all competitive data."""
    
    extract_tool = SteelExtractTool()
    
    # Combine all competitive intelligence
    all_data = "\n\n".join([
        f"=== {comp_name} ===\n{data}"
        for comp_name, data in state["intelligence_data"].items()
    ])
    
    synthesis_schema = {
        "type": "object",
        "properties": {
            "market_positioning": {
                "type": "object",
                "properties": {
                    "premium_players": {"type": "array", "items": {"type": "string"}},
                    "budget_options": {"type": "array", "items": {"type": "string"}},
                    "feature_leaders": {"type": "array", "items": {"type": "string"}}
                }
            },
            "pricing_analysis": {
                "type": "object", 
                "properties": {
                    "price_ranges": {"type": "object"},
                    "pricing_strategies": {"type": "array", "items": {"type": "string"}}
                }
            },
            "technology_trends": {"type": "array", "items": {"type": "string"}},
            "market_opportunities": {"type": "array", "items": {"type": "string"}},
            "competitive_threats": {"type": "array", "items": {"type": "string"}},
            "key_differentiators": {
                "type": "object",
                "description": "What makes each competitor unique"
            }
        }
    }
    
    try:
        synthesis = extract_tool.run({
            "content": all_data,
            "schema": synthesis_schema,
            "instructions": """
            Analyze the competitive landscape data and provide strategic insights:
            - Identify market positioning of each competitor
            - Analyze pricing strategies and ranges
            - Spot technology trends and innovations
            - Highlight market opportunities and threats
            - Determine key differentiators for each player
            """
        })
        
        return {
            **state,
            "competitive_synthesis": synthesis,
            "step": "completed"
        }
        
    except Exception as e:
        return {
            **state,
            "errors": {**state["errors"], "synthesis": [str(e)]},
            "step": "completed"
        }

# Build competitive intelligence workflow
ci_workflow = StateGraph(CompetitiveIntelligenceState)

ci_workflow.add_node("gather", gather_competitor_data)
ci_workflow.add_node("synthesize", synthesize_competitive_insights)

ci_workflow.set_entry_point("gather")
ci_workflow.add_edge("gather", "synthesize") 
ci_workflow.add_edge("synthesize", END)

# Compile workflow
ci_app = ci_workflow.compile()

# Execute competitive intelligence gathering
competitors = [
    {"name": "OpenAI", "website": "https://openai.com"},
    {"name": "Anthropic", "website": "https://anthropic.com"},
    {"name": "Google AI", "website": "https://ai.google"}
]

ci_result = ci_app.invoke({
    "competitors": competitors,
    "intelligence_data": {},
    "analysis_complete": [],
    "errors": {},
    "step": "initialized"
})

print(f"Intelligence gathering completed for {len(ci_result['analysis_complete'])} competitors")
print(f"Synthesis: {ci_result.get('competitive_synthesis', {})}")
```

## Error Recovery and Resilience

### Robust Web Automation with Fallbacks

```python
from langgraph import StateGraph, END
from langchain_steel import SteelBrowserAgent, SteelScrapeTool
from typing_extensions import TypedDict

class ResilientAutomationState(TypedDict):
    target_url: str
    task_description: str
    attempt_count: int
    max_attempts: int
    strategies: List[str]
    current_strategy: str
    result: Optional[Dict]
    errors: List[str]
    step: str

def attempt_primary_strategy(state: ResilientAutomationState) -> ResilientAutomationState:
    """Try the primary automation strategy."""
    
    browser_agent = SteelBrowserAgent()
    
    try:
        result = browser_agent.run(
            task=state["task_description"],
            url=state["target_url"]
        )
        
        return {
            **state,
            "result": result,
            "step": "completed"
        }
        
    except Exception as e:
        return {
            **state,
            "attempt_count": state["attempt_count"] + 1,
            "errors": state["errors"] + [f"Primary strategy failed: {str(e)}"],
            "step": "try_fallback_strategy"
        }

def try_fallback_strategy(state: ResilientAutomationState) -> ResilientAutomationState:
    """Try alternative approaches when primary fails."""
    
    if state["attempt_count"] >= state["max_attempts"]:
        return {
            **state,
            "step": "max_attempts_reached"
        }
    
    # Choose next strategy
    available_strategies = [s for s in state["strategies"] if s != state["current_strategy"]]
    
    if not available_strategies:
        return {
            **state,
            "step": "no_more_strategies"
        }
    
    next_strategy = available_strategies[0]
    
    if next_strategy == "simple_scraping":
        # Fall back to simple content scraping
        scrape_tool = SteelScrapeTool()
        
        try:
            content = scrape_tool.run({
                "url": state["target_url"],
                "format": "markdown",
                "delay_ms": 3000  # Wait longer
            })
            
            return {
                **state,
                "result": {"content": content, "strategy": "simple_scraping"},
                "current_strategy": next_strategy,
                "step": "completed"
            }
            
        except Exception as e:
            return {
                **state,
                "attempt_count": state["attempt_count"] + 1,
                "current_strategy": next_strategy,
                "errors": state["errors"] + [f"Simple scraping failed: {str(e)}"],
                "step": "try_fallback_strategy"
            }
    
    elif next_strategy == "stealth_mode":
        # Try with enhanced stealth settings
        from langchain_steel import SteelConfig
        
        stealth_config = SteelConfig(
            api_key="your-key",
            stealth_mode=True,
            use_proxy=True,
            solve_captcha=True,
            session_timeout=600
        )
        
        browser_agent = SteelBrowserAgent(config=stealth_config)
        
        try:
            result = browser_agent.run(
                task=state["task_description"],
                url=state["target_url"]
            )
            
            return {
                **state,
                "result": result,
                "current_strategy": next_strategy,
                "step": "completed"
            }
            
        except Exception as e:
            return {
                **state,
                "attempt_count": state["attempt_count"] + 1,
                "current_strategy": next_strategy,
                "errors": state["errors"] + [f"Stealth mode failed: {str(e)}"],
                "step": "try_fallback_strategy"
            }
    
    elif next_strategy == "manual_intervention":
        # Request manual intervention
        print("\n" + "="*50)
        print("AUTOMATION FAILED - MANUAL INTERVENTION REQUIRED")
        print("="*50)
        print(f"URL: {state['target_url']}")
        print(f"Task: {state['task_description']}")
        print(f"Attempts made: {state['attempt_count']}")
        print(f"Errors: {state['errors']}")
        print("\nOptions:")
        print("1. retry - Try primary strategy again")
        print("2. skip - Skip this task")
        print("3. manual - Provide manual result")
        
        intervention = input("\nChoose intervention: ").lower().strip()
        
        if intervention == "retry":
            return {
                **state,
                "attempt_count": 0,  # Reset attempts
                "current_strategy": "primary",
                "step": "attempt_primary"
            }
        elif intervention == "manual":
            manual_result = input("Enter manual result/data: ")
            return {
                **state,
                "result": {"content": manual_result, "strategy": "manual"},
                "step": "completed"
            }
        else:  # skip
            return {
                **state,
                "result": {"skipped": True, "reason": "manual_intervention"},
                "step": "completed"
            }

def handle_max_attempts(state: ResilientAutomationState) -> ResilientAutomationState:
    """Handle case where max attempts reached."""
    return {
        **state,
        "result": {
            "failed": True,
            "reason": "max_attempts_exceeded",
            "attempts": state["attempt_count"],
            "errors": state["errors"]
        },
        "step": "failed"
    }

def handle_no_strategies(state: ResilientAutomationState) -> ResilientAutomationState:
    """Handle case where no more strategies available."""
    return {
        **state,
        "result": {
            "failed": True,
            "reason": "all_strategies_exhausted",
            "attempts": state["attempt_count"],
            "errors": state["errors"]
        },
        "step": "failed"
    }

# Build resilient automation workflow
resilient_workflow = StateGraph(ResilientAutomationState)

resilient_workflow.add_node("primary", attempt_primary_strategy)
resilient_workflow.add_node("fallback", try_fallback_strategy)
resilient_workflow.add_node("max_attempts", handle_max_attempts)
resilient_workflow.add_node("no_strategies", handle_no_strategies)

resilient_workflow.set_entry_point("primary")

resilient_workflow.add_conditional_edges(
    "primary",
    lambda x: END if x["step"] == "completed" else "fallback"
)

resilient_workflow.add_conditional_edges(
    "fallback",
    lambda x: {
        "completed": END,
        "max_attempts_reached": "max_attempts", 
        "no_more_strategies": "no_strategies",
        "try_fallback_strategy": "fallback"
    }[x["step"]]
)

resilient_workflow.add_edge("max_attempts", END)
resilient_workflow.add_edge("no_strategies", END)

# Compile workflow
resilient_app = resilient_workflow.compile()

# Execute resilient automation
automation_result = resilient_app.invoke({
    "target_url": "https://difficult-site.com",
    "task_description": "Navigate to dashboard and extract user metrics",
    "attempt_count": 0,
    "max_attempts": 3,
    "strategies": ["primary", "simple_scraping", "stealth_mode", "manual_intervention"],
    "current_strategy": "primary",
    "result": None,
    "errors": [],
    "step": "initialized"
})

print(f"Automation result: {automation_result['result']}")
```

## Best Practices for Steel + LangGraph

### 1. State Management

- Keep state minimal and focused
- Use TypedDict for clear state structure
- Handle partial failures gracefully
- Implement proper error accumulation

### 2. Node Design

- Make each node focused on a single responsibility
- Handle exceptions within nodes
- Return consistent state structure
- Use descriptive step names for routing

### 3. Error Recovery

- Implement multiple fallback strategies
- Use exponential backoff for retries
- Provide human-in-the-loop options
- Log errors for debugging

### 4. Performance

- Use parallel processing for independent operations
- Implement session reuse across related nodes
- Cache expensive operations when possible
- Monitor workflow execution times

### 5. Testing

```python
# Test individual nodes
def test_scrape_node():
    initial_state = {
        "url": "https://example.com",
        "content": "",
        "status": "initialized"
    }
    
    result = scrape_content(initial_state)
    assert result["status"] == "content_scraped"
    assert len(result["content"]) > 0

# Test workflow paths
def test_error_handling():
    error_state = {
        "url": "https://invalid-url",
        "content": "",
        "status": "initialized"
    }
    
    result = app.invoke(error_state)
    assert "error" in result["status"]
```

Steel's integration with LangGraph enables sophisticated web automation workflows that can handle complex scenarios, recover from failures, and coordinate multiple operations while maintaining state consistency throughout the process.