"""
Lab 14 - A real MCP server (low-level mcp.server.Server API, stdio).

Run from the repo root:
    Started by Lab 15; on its own: python Agents_MCP_Skills/Agents_lab14_mcp_skills_server.py

Tools: ask_cloud_model and image2mermaid (your Foundry deployment, Lab 01 .env keys),
calculator, text_analyzer, web_search.
"""
# 🔌 MCP Skills Server
# ====================
# A Model Context Protocol (MCP) server that exposes course skills as tools.
# 
# This server implements the MCP specification, allowing any MCP-compatible
# client to discover and execute skills.
# 
# Run this server with:
#     python Agents_lab14_mcp_skills_server.py
# 
# Or use with MCP stdio transport:
#     python -m mcp run Agents_lab14_mcp_skills_server.py
# 


import asyncio
import json
import os
import sys
import re
from pathlib import Path
from typing import Any, Sequence
from dotenv import load_dotenv

# Load environment variables from the correct location
# (important when running as MCP subprocess)
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Also try loading from current working directory
load_dotenv()

# Suppress SSL warnings (corporate proxies can intercept SSL)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# MCP SDK imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
)

# ============================================================================
# 📁 CONFIGURATION
# ============================================================================

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cloud_model import ask_cloud_model, image_to_mermaid, deployment   # Foundry deployment (Lab 01 keys)

# ============================================================================
# 🛠️ SKILL IMPLEMENTATIONS
# ============================================================================

async def image2mermaid_execute(image_path: str, diagram_type: str = "") -> dict:
    """Convert a diagram image to Mermaid code with the Foundry deployment's vision input."""
    return await asyncio.get_running_loop().run_in_executor(None, image_to_mermaid, image_path, diagram_type)


async def ask_cloud_model_execute(question: str) -> dict:
    """Answer a technical question with the Foundry deployment (Azure OpenAI v1 API)."""
    return await asyncio.get_running_loop().run_in_executor(None, ask_cloud_model, question)


def calculator_execute(expression: str) -> dict:
    """Safe mathematical expression evaluator"""
    try:
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            return {"error": "Invalid characters in expression", "success": False}
        result = eval(expression)
        return {"success": True, "expression": expression, "result": result}
    except Exception as e:
        return {"error": str(e), "success": False}


def text_analyzer_execute(text: str, analysis_type: str = "summary") -> dict:
    """Analyze text properties"""
    word_count = len(text.split())
    char_count = len(text)
    sentence_count = len(re.split(r'[.!?]+', text.strip())) if text.strip() else 0
    
    result = {
        "success": True,
        "word_count": word_count,
        "character_count": char_count,
        "sentence_count": sentence_count,
        "analysis_type": analysis_type
    }
    
    if analysis_type == "sentiment":
        positive = ["good", "great", "excellent", "happy", "love", "amazing"]
        negative = ["bad", "terrible", "hate", "awful", "sad", "poor"]
        text_lower = text.lower()
        pos = sum(1 for w in positive if w in text_lower)
        neg = sum(1 for w in negative if w in text_lower)
        result["sentiment"] = "positive" if pos > neg else "negative" if neg > pos else "neutral"
    elif analysis_type == "keywords":
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        word_freq = {}
        for w in words:
            word_freq[w] = word_freq.get(w, 0) + 1
        top = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        result["keywords"] = [w[0] for w in top]
    else:
        result["summary"] = f"Text contains {word_count} words in {sentence_count} sentences."
    
    return result


def web_search_execute(query: str, num_results: int = 5) -> dict:
    """Search the web - Weather API first, then DuckDuckGo, then Google, then browser"""
    query_clean = query.strip()
    query_lower = query_clean.lower()
    
    # Debug
    print(f"[DEBUG] web_search_execute: query='{query_clean}'", file=sys.stderr)
    
    # Method 0: Weather API for weather queries
    if any(word in query_lower for word in ["weather", "temperature", "rain", "sunny", "forecast", "wetaher"]):
        print(f"[DEBUG] Detected weather query, using wttr.in", file=sys.stderr)
        try:
            import requests
            
            # Extract location - be careful not to match within words
            location = "Tel Aviv"  # Default
            # Use word boundaries for matching
            import re
            for word in [" in ", " at ", " for "]:
                if word in query_lower:
                    parts = query_lower.split(word)
                    if len(parts) > 1:
                        # Clean up the location
                        loc = parts[-1].strip().strip("?").strip()
                        # Remove trailing words like "today", "this month", etc.
                        loc = re.sub(r'\s+(today|tomorrow|this\s+\w+|next\s+\w+|now).*$', '', loc, flags=re.IGNORECASE)
                        if loc and len(loc) > 1:
                            location = loc
                        break
            
            print(f"[DEBUG] Extracted location: {location}", file=sys.stderr)
            
            weather_url = f"https://wttr.in/{location}?format=j1"
            # Use proxy for external sites (only if HTTP(S)_PROXY is set, e.g. on a corporate network)
            proxy = os.environ.get('HTTP_PROXY') or os.environ.get('HTTPS_PROXY')
            print(f"[DEBUG] Proxy: {proxy}", file=sys.stderr)
            print(f"[DEBUG] Weather URL: {weather_url}", file=sys.stderr)
            proxies = {"http": proxy, "https": proxy} if proxy else None
            
            # Disable SSL verification for proxy (corporate proxies can intercept SSL)
            response = requests.get(
                weather_url, 
                timeout=15, 
                headers={'User-Agent': 'curl/7.68.0'},
                proxies=proxies,
                verify=False  # Skip SSL verification for proxy
            )
            print(f"[DEBUG] Weather response status: {response.status_code}", file=sys.stderr)
            
            if response.status_code == 200:
                data = response.json()
                current = data.get("current_condition", [{}])[0]
                area = data.get("nearest_area", [{}])[0]
                
                temp_c = current.get("temp_C", "N/A")
                temp_f = current.get("temp_F", "N/A")
                condition = current.get("weatherDesc", [{}])[0].get("value", "N/A")
                humidity = current.get("humidity", "N/A")
                wind = current.get("windspeedKmph", "N/A")
                city = area.get("areaName", [{}])[0].get("value", location)
                country = area.get("country", [{}])[0].get("value", "")
                
                weather_info = f"🌡️ **Weather in {city}, {country}**\n\n"
                weather_info += f"- Temperature: {temp_c}°C ({temp_f}°F)\n"
                weather_info += f"- Condition: {condition}\n"
                weather_info += f"- Humidity: {humidity}%\n"
                weather_info += f"- Wind: {wind} km/h"
                
                return {
                    "success": True,
                    "query": query,
                    "source": "wttr.in Weather API",
                    "num_results": 1,
                    "results": [{
                        "title": f"Weather in {city}, {country}",
                        "snippet": weather_info,
                        "url": f"https://wttr.in/{location}"
                    }],
                    "weather_data": {
                        "location": f"{city}, {country}",
                        "temp_c": temp_c,
                        "temp_f": temp_f,
                        "condition": condition,
                        "humidity": humidity,
                        "wind_kmph": wind
                    }
                }
        except Exception as e:
            print(f"[DEBUG] wttr.in failed: {e}", file=sys.stderr)
    
    # Method 1: Try DuckDuckGo (more reliable)
    try:
        from duckduckgo_search import DDGS
        print(f"[DEBUG] Trying DuckDuckGo...", file=sys.stderr)
        
        # Use proxy for external sites (only if HTTP(S)_PROXY is set, e.g. on a corporate network)
        proxy = os.environ.get('HTTP_PROXY') or os.environ.get('HTTPS_PROXY')
        with DDGS(proxy=proxy) as ddgs:
            results = list(ddgs.text(query_clean, max_results=num_results))
        
        if results:
            formatted_results = []
            for r in results:
                formatted_results.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", "")
                })
            
            return {
                "success": True,
                "query": query,
                "source": "DuckDuckGo",
                "num_results": len(formatted_results),
                "results": formatted_results
            }
    except:
        pass
    
    # Method 2: Try Google via requests
    try:
        import requests
        from urllib.parse import quote_plus
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        search_url = f"https://www.google.com/search?q={quote_plus(query_clean)}&num={num_results}&hl=en"
        # Use proxy for external sites (only if HTTP(S)_PROXY is set, e.g. on a corporate network)
        proxy = os.environ.get('HTTP_PROXY') or os.environ.get('HTTPS_PROXY')
        proxies = {"http": proxy, "https": proxy} if proxy else None
        response = requests.get(search_url, headers=headers, timeout=10, proxies=proxies)
        
        if response.status_code == 200:
            patterns = [
                r'<h3[^>]*>([^<]+)</h3>',
                r'class="[^"]*LC20lb[^"]*"[^>]*>([^<]+)<',
            ]
            
            for pattern in patterns:
                titles = re.findall(pattern, response.text)
                if titles:
                    formatted_results = [{"title": t.strip(), "snippet": "", "url": search_url} for t in titles[:num_results] if len(t.strip()) > 5]
                    if formatted_results:
                        return {
                            "success": True,
                            "query": query,
                            "source": "Google",
                            "num_results": len(formatted_results),
                            "results": formatted_results
                        }
    except:
        pass
    
    # Method 3: Open browser
    try:
        import webbrowser
        from urllib.parse import quote_plus
        
        search_url = f"https://www.google.com/search?q={quote_plus(query_clean)}"
        webbrowser.open(search_url)
        
        return {
            "success": True,
            "query": query,
            "source": "Browser",
            "message": "Opened Google search in browser",
            "url": search_url,
            "results": [{"title": f"Google Search: {query}", "snippet": "Opened in browser", "url": search_url}]
        }
    except Exception as e:
        return {"success": False, "error": str(e), "query": query}


# ============================================================================
# 🔌 MCP SERVER SETUP
# ============================================================================

# Create the MCP server
server = Server("course-skills-server")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    List all available tools (MCP tools/list handler).
    This is called by MCP clients to discover available tools.
    """
    return [
        Tool(
            name="image2mermaid",
            description="Convert a diagram image (PNG, JPG, etc.) to Mermaid diagram code using the cloud model's vision. Use this when the user wants to convert an image to mermaid, create a mermaid diagram from an image, or turn a picture/diagram/flowchart into code.",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "Full path to the image file to convert"
                    },
                    "diagram_type": {
                        "type": "string",
                        "description": "Optional hint for the diagram type (flowchart LR, sequenceDiagram, ...)",
                        "default": ""
                    }
                },
                "required": ["image_path"]
            }
        ),
        Tool(
            name="ask_cloud_model",
            description="Answer a technical question (Wi-Fi, Bluetooth, networking, AI, engineering) with the course's cloud model (Azure OpenAI on Microsoft Foundry). Use for explanations such as 'What is MLD in Wi-Fi 7?' or 'Explain LE Audio'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The question to answer"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="calculator",
            description="Perform mathematical calculations. Use when the user wants to calculate, compute, or do math operations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate (e.g., '2 + 2', '10 * 5')"
                    }
                },
                "required": ["expression"]
            }
        ),
        Tool(
            name="text_analyzer",
            description="Analyze text for various properties like word count, sentiment, or keywords.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to analyze"
                    },
                    "analysis_type": {
                        "type": "string",
                        "description": "Type of analysis: summary, sentiment, or keywords",
                        "enum": ["summary", "sentiment", "keywords"],
                        "default": "summary"
                    }
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="web_search",
            description="Search the web for general knowledge questions. Use this for general facts (not Wi-Fi/Bluetooth technical questions, which go to ask_cloud_model) - such as history, science, current events, definitions, 'what is', 'who is', 'how does', general facts, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return (default 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """
    Execute a tool (MCP tools/call handler).
    This is called by MCP clients to execute a specific tool.
    """
    try:
        if name == "image2mermaid":
            result = await image2mermaid_execute(
                image_path=arguments["image_path"],
                diagram_type=arguments.get("diagram_type", "")
            )
        elif name == "ask_cloud_model":
            result = await ask_cloud_model_execute(arguments["query"])
        elif name == "calculator":
            result = calculator_execute(arguments["expression"])
        elif name == "text_analyzer":
            result = text_analyzer_execute(
                text=arguments["text"],
                analysis_type=arguments.get("analysis_type", "summary")
            )
        elif name == "web_search":
            result = web_search_execute(
                query=arguments["query"],
                num_results=arguments.get("num_results", 5)
            )
        else:
            result = {"error": f"Unknown tool: {name}", "success": False}
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e), "success": False}))]


# ============================================================================
# 🚀 SERVER ENTRY POINT
# ============================================================================

async def main():
    """Run the MCP server using stdio transport"""
    print(f"🔌 Starting course skills MCP server (cloud model: {deployment()})...", file=sys.stderr)
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
