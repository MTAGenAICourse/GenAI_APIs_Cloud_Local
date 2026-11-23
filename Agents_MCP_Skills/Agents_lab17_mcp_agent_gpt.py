"""
Lab 17 - A cloud agent with local tools: GPT (Microsoft Foundry) + the Lab 16 MCP server.

The agent loop, written out so you can see every step:
    1. start the MCP server (Lab 16) as a subprocess and ask it for its tools   (tools/list)
    2. send the user request + the tool schemas to GPT                       (Responses API)
    3. GPT answers with function calls -> run each one on the MCP server     (tools/call)
    4. send the results back; repeat until GPT answers in plain text

The reasoning runs in the cloud; the images, audio and models never leave your laptop -
only the tool results (short text) are sent to the model.

Setup: the same .env as Lab 01 (AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT).
Run from the repo root:
    python Agents_MCP_Skills/Agents_lab17_mcp_agent_gpt.py
    python Agents_MCP_Skills/Agents_lab17_mcp_agent_gpt.py --prompt "What is in Data/Robot.jpg? How many cups would 17 such robots hold?"

Compare with Lab 18 (the same loop on Claude Opus 5.5).
Behind a corporate proxy with a private Foundry resource? See Agents_MCP_Skills/README_Workshop_Demo.md (NO_PROXY).
"""
import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from openai import OpenAI

SERVER = Path(__file__).with_name("Agents_lab16_mcp_openvino_server.py")
INSTRUCTIONS = ("You are a helpful assistant running on a student's laptop. Use the tools for anything about "
                "local files and for arithmetic; never guess file contents. Answer concisely.")


async def call_mcp_tool(session, name, arguments):
    """tools/call on the MCP server; returns (text, is_error)."""
    result = await session.call_tool(name, arguments)
    text = "\n".join(c.text for c in result.content if c.type == "text")
    return text, bool(result.isError)


async def run(args):
    load_dotenv()
    client = OpenAI(api_key=os.environ["AZURE_OPENAI_API_KEY"],
                    base_url=os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/") + "/openai/v1/")
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-6.1-sol")

    server = StdioServerParameters(command=sys.executable, args=[str(SERVER)], env=dict(os.environ))
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Discover the tools: MCP schemas become OpenAI function tools
            mcp_tools = (await session.list_tools()).tools
            print("Tools from the MCP server:", ", ".join(t.name for t in mcp_tools))
            tools = [{"type": "function", "name": t.name, "description": t.description or "",
                      "parameters": t.inputSchema, "strict": False}   # MCP schemas have optional args
                     for t in mcp_tools]

            items = [{"role": "user", "content": args.prompt}]
            start = time.time()
            for turn in range(1, args.max_turns + 1):
                # 2. Ask the model; it may answer or ask for tool calls
                resp = client.responses.create(model=deployment, instructions=INSTRUCTIONS, input=items,
                                               tools=tools, reasoning={"effort": args.effort})
                calls = [o for o in resp.output if o.type == "function_call"]
                if not calls:
                    print(f"\n{resp.output_text}")
                    break
                items += resp.output            # keep reasoning + function_call items in the history

                # 3. Run every requested call on the MCP server and return all results
                for call in calls:
                    arguments = json.loads(call.arguments or "{}")
                    print(f"  turn {turn}: {call.name}({json.dumps(arguments)})")
                    try:
                        text, is_error = await call_mcp_tool(session, call.name, arguments)
                    except Exception as e:      # a failed tool is reported back, not dropped
                        text, is_error = f"Error: {e}", True
                    print(f"           -> {'ERROR ' if is_error else ''}{text[:120]}")
                    items.append({"type": "function_call_output", "call_id": call.call_id, "output": text})
            else:
                print(f"\nStopped after {args.max_turns} turns without a final answer.")

            print(f"\n--- {deployment} | effort={args.effort} | {time.time() - start:.1f}s")


def main():
    parser = argparse.ArgumentParser(description="Lab 17: GPT agent with local MCP tools")
    parser.add_argument("--prompt", default="Look at Data/Robot.jpg and tell me what the robot is doing. "
                                            "Then compute 17 * 24 for me.")
    parser.add_argument("--effort", default="low", choices=["low", "medium", "high", "xhigh", "max"])
    parser.add_argument("--max-turns", type=int, default=6)
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
