"""
Lab 18 - The same agent on Claude Opus 5.5: Anthropic Messages API + the Lab 16 MCP server.

Same loop as Lab 17, different API shapes - compare them side by side:

    Lab 17 (OpenAI Responses)            Lab 18 (Anthropic Messages)
    tools=[{"type": "function", ...}]    tools=[{"name", "description", "input_schema"}]
    output item "function_call"          content block "tool_use"   (stop_reason == "tool_use")
    "function_call_output" item          "tool_result" block in the next user message
    reasoning={"effort": ...}            output_config={"effort": ...}

The loop is written by hand so you can see it. The SDK can also run it for you:
client.beta.messages.tool_runner(...) with anthropic.lib.tools.mcp.async_mcp_tool(...) - try it as an exercise.

Setup: ANTHROPIC_API_KEY in .env (same as Lab 02).
Run from the repo root:
    python Agents_MCP_Skills/Agents_lab18_mcp_agent_claude.py
    python Agents_MCP_Skills/Agents_lab18_mcp_agent_claude.py --effort medium --prompt "..."
"""
import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

MODEL = "claude-opus-5-5"
SERVER = Path(__file__).with_name("Agents_lab16_mcp_openvino_server.py")
SYSTEM = ("You are a helpful assistant running on a student's laptop. Use the tools for anything about "
          "local files and for arithmetic; never guess file contents. Answer concisely.")


class Claude:
    """Messages API with server-side refusal fallback; runs without it if the workspace hasn't enabled it."""

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.fallback = True

    def create(self, **request):
        if self.fallback:
            try:
                return self.client.beta.messages.create(
                    **request, betas=["server-side-fallback-2026-07-01"], fallbacks="default")
            except anthropic.BadRequestError as e:
                if "server_side_fallback" not in str(e):
                    raise
                print("(server-side fallback not enabled for this workspace - running without it)")
                self.fallback = False
        return self.client.messages.create(**request)


async def call_mcp_tool(session, name, arguments):
    """tools/call on the MCP server; returns (text, is_error)."""
    result = await session.call_tool(name, arguments)
    text = "\n".join(c.text for c in result.content if c.type == "text")
    return text, bool(result.isError)


async def run(args):
    load_dotenv()
    claude = Claude()

    server = StdioServerParameters(command=sys.executable, args=[str(SERVER)], env=dict(os.environ))
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Discover the tools: an MCP inputSchema is already a JSON Schema Claude accepts
            mcp_tools = (await session.list_tools()).tools
            print("Tools from the MCP server:", ", ".join(t.name for t in mcp_tools))
            tools = [{"name": t.name, "description": t.description or "", "input_schema": t.inputSchema}
                     for t in mcp_tools]

            messages = [{"role": "user", "content": args.prompt}]
            start = time.time()
            for turn in range(1, args.max_turns + 1):
                # 2. Ask Claude; thinking is always on for Opus 5.5 - tune depth with effort
                resp = claude.create(model=MODEL, max_tokens=16000, system=SYSTEM, tools=tools,
                                     messages=messages, output_config={"effort": args.effort})

                if resp.stop_reason == "refusal":
                    category = resp.stop_details.category if resp.stop_details else None
                    print(f"\nDeclined ({category})")
                    break
                if resp.stop_reason != "tool_use":       # end_turn (or max_tokens): final answer
                    print("\n" + "".join(b.text for b in resp.content if b.type == "text"))
                    break

                # 3. Keep Claude's full turn (thinking + tool_use blocks), run every call,
                #    and send ALL results back in one user message
                messages.append({"role": "assistant", "content": resp.content})
                results = []
                for block in (b for b in resp.content if b.type == "tool_use"):
                    print(f"  turn {turn}: {block.name}({json.dumps(block.input)})")
                    try:
                        text, is_error = await call_mcp_tool(session, block.name, block.input)
                    except Exception as e:               # a failed tool is reported back, not dropped
                        text, is_error = f"Error: {e}", True
                    print(f"           -> {'ERROR ' if is_error else ''}{text[:120]}")
                    results.append({"type": "tool_result", "tool_use_id": block.id,
                                    "content": text, "is_error": is_error})
                messages.append({"role": "user", "content": results})
            else:
                print(f"\nStopped after {args.max_turns} turns without a final answer.")

            print(f"\n--- served by {resp.model} | effort={args.effort} | {time.time() - start:.1f}s")


def main():
    parser = argparse.ArgumentParser(description="Lab 18: Claude agent with local MCP tools")
    parser.add_argument("--prompt", default="Look at Data/Robot.jpg and tell me what the robot is doing. "
                                            "Then compute 17 * 24 for me.")
    parser.add_argument("--effort", default="low", choices=["low", "medium", "high", "xhigh", "max"])
    parser.add_argument("--max-turns", type=int, default=6)
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
