# Labs 13–18: Tools and the Model Context Protocol (MCP)

These labs show how an agent finds and calls tools. Lab 13 explains tool schemas and routing inside one app.
Labs 14–15 split the same idea into a real MCP server and client. Labs 16–18 turn the Part 1 local models
into MCP tools and let a cloud model (GPT or Claude) call them.

Run from the repo root (`GenAI_APIs_Cloud_Local`):

```bash
streamlit run Agents_MCP_Skills/Agents_lab13_mcp_tutorial.py         # concepts, no model needed
streamlit run Agents_MCP_Skills/Agents_lab15_mcp_skills_client.py    # starts the Lab 14 server itself
python Agents_MCP_Skills/Agents_lab16_mcp_openvino_server.py --self-test
python Agents_MCP_Skills/Agents_lab17_mcp_agent_gpt.py               # GPT on Microsoft Foundry + Lab 16
python Agents_MCP_Skills/Agents_lab18_mcp_agent_claude.py            # Claude Opus 5.5 + Lab 16
```

---

## Setup

1. Finish the Part 1 setup in the repo root `README.md` (venv, models).
2. Install the Part 2 packages from the repo root: `pip install -r Agents_MCP_Skills/requirements.txt`.
   It adds `mcp` (server and client SDK), `requests` and `duckduckgo_search` (web search in Labs 14–15).
   `mcp` is pinned to `mcp>=1.20,<2`: mcp 2.x renamed `FastMCP` and changed the low-level server API, so
   Labs 14–18 break on 2.x.
3. For the MCP Inspector (`mcp dev`), also run `pip install "mcp[cli]"`.
4. Keys in `.env` in the repo root:
   - Labs 14–15 (`ask_cloud_model`, `image2mermaid`) and Lab 17: the same keys as Lab 01: `AZURE_OPENAI_ENDPOINT`,
     `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT`.
   - Lab 18: `ANTHROPIC_API_KEY`, as in Lab 02.
5. Lab 16 uses the model folders from Part 1: `Phi-3.5-vision-instruct-int4-ov`, `whisper-base`,
   `stable-diffusion-v1-5-int8-ov`, all in the repo root.

Behind a corporate proxy with a private Foundry resource, add `.openai.azure.com` to `NO_PROXY` and open a new
terminal; see [README_Reproduce_Demo.md](../README_Reproduce_Demo.md#proxy-set-check-unset) in the repo root.

---

## MCP in one page

MCP is a standard way for an AI application (the client) to discover and call tools offered by a server.

| Concept | Meaning |
| --- | --- |
| Tool | A function the model can ask to run. It has a name, a description and a JSON input schema. |
| Resource | Data the client can read (files, database rows). Not used in these labs. |
| Prompt | A reusable prompt template offered by the server. Not used in these labs. |
| `tools/list` | Client asks the server which tools exist. |
| `tools/call` | Client asks the server to run one tool with arguments. |
| Transport | How messages travel. These labs use **stdio**: the client starts the server as a subprocess. |

```text
User request --> Agent (decides which tool) --> MCP server (runs the tool) --> result --> Agent --> answer
```

The model never runs the tool. It reads the tool descriptions, picks one, and fills in the arguments.
Your code runs the call and sends the result back. Good descriptions decide whether the model picks the right tool.

A tool schema, as Lab 13 prints it:

```json
{
  "name": "weather",
  "description": "Get current weather information for a location. Use this when the user asks about weather, temperature, or climate conditions.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "location": {"type": "string", "description": "City name or location to get weather for"},
      "unit": {"type": "string", "description": "Temperature unit", "enum": ["celsius", "fahrenheit"]}
    },
    "required": ["location"]
  }
}
```

| Field | Purpose |
| --- | --- |
| `name` | Unique tool id |
| `description` | Tells the model when to use the tool |
| `properties` | One entry per argument, with a type |
| `enum` | Allowed values |
| `required` | Arguments the caller must send |

---

## Lab 13: schemas and routing, in one app

Lab 13 runs everything in one process. No LLM and no network: a regex router plays the role of the model,
so you can see each decision.

| Tool | What it does | Example |
| --- | --- | --- |
| `weather` | Random simulated weather | "What's the weather in Paris?" |
| `calculator` | Evaluates `+ - * / ( )` expressions | "Calculate 125 * 4 + 50" -> 550 |
| `text_analyzer` | Word count, simple sentiment or keywords | "Analyze this text for sentiment: I love it!" |
| `unit_converter` | m/ft, km/mi, °C/°F, kg/lb | "Convert 100 kilometers to miles" -> 62.14 miles |
| `task_manager` | Add, list, complete, clear tasks (session state) | "Add a task: Complete homework" |

How the router works (`AgenticRouter.route`):

1. Lower-case the input and try each tool's regex patterns, in the order weather, calculator,
   text_analyzer, unit_converter, task_manager. The first match wins: confidence `high`, arguments extracted from the match.
2. No match: look for a keyword (`rain`, `convert`, `task`, ...). The tool is chosen with confidence `low`
   and **no arguments**, so the call usually fails with "missing required argument".
3. Nothing found: "I couldn't determine which tool to use".

UI: the sidebar has **Show Tool Schemas**, **Show Routing Logic**, **Show Raw JSON Output**, six example
buttons and **🗑️ Clear History**. Type in **Your message:** and press **🚀 Send**. Expand
**📚 What is MCP? (Click to Learn)** for the intro.

### Demo script (15 minutes)

All results below were checked against the Lab 13 code.

| Query | Tool, arguments | Result |
| --- | --- | --- |
| What's the weather in Paris? | weather, `location=paris` | random temperature and condition |
| Temperature in Tokyo | weather, `location=tokyo` | works without the word "weather" |
| Calculate 125 * 4 + 50 | calculator, `125 * 4 + 50` | 550 |
| Compute 15 + 27 | calculator, `15 + 27` | 42 |
| What is 100 / 5? | calculator, `100 / 5` | 20.0 |
| Analyze this text for sentiment: I love this course! It's amazing! | text_analyzer, sentiment | positive |
| Sentiment of: This product is terrible, worst purchase ever! | text_analyzer, sentiment | negative |
| Find keywords in: Machine learning and artificial intelligence are transforming software. | text_analyzer, keywords | top words (includes "find", "keywords") |
| Convert 100 kilometers to miles | unit_converter | 62.14 miles |
| Convert 50 fahrenheit to celsius | unit_converter | 10.00 celsius |

The location is lower-case because the router matches on the lower-cased input.

**Stateful tool.** Run these in order:

1. `Add a task: Complete homework`
2. `Add a task: Study for exam (high priority)` (the word "high" sets priority high)
3. `Remind me to call mom`
4. `Show my tasks` (three tasks)
5. `Complete task homework`
6. `Show my tasks` (homework is now done)

Phrase step 5 exactly like that. "Complete the homework task" does not match the pattern
`complete (the) task`, falls to the keyword fallback, and fails with no arguments.
Tasks live in Streamlit session state; a page refresh or **🗑️ Clear History** clears them.

**Where regex routing breaks.** These are good discussion points: an LLM router would handle all of them.

| Query | What happens | Why |
| --- | --- | --- |
| Is it raining in Seattle? | weather, `location=e` | greedy regex captures one letter |
| How hot is it in Dubai? | no tool | no pattern or keyword matches "hot" |
| What is 100 divided by 5? | calculator, result 100 | "divided by" is not an operator; only "100" is captured |
| What is 32 degrees Fahrenheit in Celsius? | calculator, result 32 | the calculator pattern `what is <number>` matches first |
| What's 50 degrees Fahrenheit in Celsius? | unit_converter (low), fails | keyword match, no arguments |
| How many feet are in 10 meters? | unit_converter (low), fails | the "how many" pattern expects "how many feet in 10 meters" |
| Weather | weather (low), fails | no location |
| Hello! | no tool | fallback message |

Exercises: (1) fix the Seattle case by making the last group lazy or by matching a capitalized word;
(2) add a `currency_converter` tool to `create_tool_registry()` with its schema and a pattern;
(3) list three queries an LLM would route correctly where the regex fails.

---

## Labs 14–15: a real MCP server and client

Lab 14 is an MCP server written with the low-level `mcp.server.Server` API. Lab 15 is a Streamlit client
that starts Lab 14 over stdio, lists its tools and calls them. You do not start Lab 14 yourself.

### Server (Lab 14)

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("course-skills-server")

@server.list_tools()                      # answers tools/list
async def list_tools() -> list[Tool]:
    return [Tool(name="calculator", description="Perform mathematical calculations. ...",
                 inputSchema={"type": "object",
                              "properties": {"expression": {"type": "string"}},
                              "required": ["expression"]}),
            ...]

@server.call_tool()                       # answers tools/call
async def call_tool(name: str, arguments: dict):
    if name == "calculator":
        result = calculator_execute(arguments["expression"])
    ...
    return [TextContent(type="text", text=json.dumps(result))]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, ...)
```

Lab 14 offers five tools:

| Tool | What it does | Needs |
| --- | --- | --- |
| `image2mermaid` | Turns a diagram image into Mermaid code with the cloud model's vision (`image_path`, optional `diagram_type`) | the Lab 01 `.env` keys |
| `ask_cloud_model` | Answers a technical question (Wi-Fi, Bluetooth, AI, ...) with your Foundry deployment | the Lab 01 `.env` keys |
| `calculator` | Evaluates an arithmetic expression | nothing |
| `text_analyzer` | Word count, simple sentiment, keywords or a one-line summary | nothing |
| `web_search` | Weather questions use wttr.in; others try DuckDuckGo, then Google, then open a browser | internet |

The two cloud tools call `cloud_model.py` (next to the labs): `ask_cloud_model(question)` and
`image_to_mermaid(image_path, diagram_type)` on your Microsoft Foundry deployment (Azure OpenAI v1 API, Responses
API, reasoning effort `low`). Measured on 2026-11-23 on the instructor laptop with deployment `gpt-5.4`:
"What is MLD in Wi-Fi 7?" answered in 4.4 s; a 3-box flowchart image became
`flowchart LR  Camera --> VLM --> Decision` in 2.7 s.

### Client (Lab 15)

1. Click **🔍 Discover MCP Tools** in the sidebar. The client sends `tools/list` and shows five tools with their schemas.
2. Type a request in **Your request:** and click **🚀 Execute via MCP**.
3. A regex router picks the tool (as in Lab 13). The client opens a stdio session, sends `tools/call`, and shows
   the JSON reply under **Raw MCP Response**.

```python
server_params = StdioServerParameters(command=sys.executable, args=[str(MCP_SERVER_SCRIPT)], env={**os.environ})
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = (await session.list_tools()).tools
        result = await session.call_tool("calculator", {"expression": "(17 + 25) * 2"})
```

Try `calculate (17 + 25) * 2` (returns 84), `What is the capital of France?` (goes to `web_search`) and
`What is MLD in WiFi 7?` (goes to `ask_cloud_model`). Questions about Wi-Fi, Bluetooth, MLD or LE Audio, and
requests that start with "explain", go to `ask_cloud_model`. Every tool, including the cloud ones, is called
through MCP. Each discovery and each call starts a fresh server subprocess; that is simple but slower than keeping
one session open.

---

## Labs 16–18: local models as MCP tools, cloud model as the brain

### Lab 16: the OpenVINO MCP server

Lab 16 uses the high-level FastMCP API. A type-hinted function with a docstring becomes a tool;
the SDK builds the JSON schema from the signature.

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("openvino-local-models", log_level="WARNING")

@mcp.tool()
def calculate(expression: str) -> str:
    """Evaluate an arithmetic expression exactly, e.g. "(17 + 25) * 2" or "0.15 * 240"."""
    return str(_eval(ast.parse(expression, mode="eval").body))

if __name__ == "__main__":
    mcp.run()          # stdio transport by default
```

| Tool | Model (Part 1 lab) | Notes |
| --- | --- | --- |
| `list_data_files()` | none | Files in `Data/` as repo-relative paths |
| `describe_image(image_path, question)` | Phi-3.5-vision (Lab 04) | `max_new_tokens=200`, stop token 32007 |
| `transcribe_audio(wav_path)` | Whisper base (Lab 07) | 16 kHz, mono, 16-bit WAV only |
| `generate_image(prompt, steps=20)` | Stable Diffusion (Lab 09) | 512x512, steps capped 1–50, saved to `output/agent_image_<time>.png`; about a minute on CPU |
| `calculate(expression)` | none | Safe arithmetic via `ast`: numbers and `+ - * / // % **` only |

Details worth noticing:

- **stdout is the protocol.** Logging goes to stderr (`log()`), or it would corrupt the MCP messages.
- **Lazy loading.** Each pipeline loads on its first call and is reused.
- **Path guard.** File arguments must resolve inside the repo, so the model cannot read other files.
- **Settings.** `LAB_DEVICE` (default `CPU`; set `GPU` for the integrated GPU) and `LAB_MODELS_DIR`
  (default: the repo root) are environment variables.
- `Data/` ships with `Robot.jpg` and `all_animals.mp4` but no WAV file. To test `transcribe_audio`, record a
  16 kHz mono WAV with Lab 07/08 and save it inside the repo.

Try the server without a client:

```bash
python Agents_MCP_Skills/Agents_lab16_mcp_openvino_server.py --self-test   # list_data_files, calculate, describe_image
mcp dev Agents_MCP_Skills/Agents_lab16_mcp_openvino_server.py              # MCP Inspector in the browser (needs Node.js)
```

On 2026-11-23 the self-test answered "The robot is holding a cup of coffee." for `Data/Robot.jpg`; loading the
VLM took 16 s on the integrated GPU (`README_Workshop_Demo.md`).

Any MCP client that can start a stdio server can use Lab 16: command `python`, argument the path to the file.

### Labs 17 and 18: the agent loop

Both scripts run the same loop, written out by hand:

1. Start Lab 16 as a subprocess and call `tools/list`.
2. Send the user request and the tool schemas to the cloud model.
3. The model answers with tool calls. Run each one on the MCP server with `tools/call`.
4. Send all results back. Repeat until the model answers in plain text (at most `--max-turns`, default 6).

The images, audio and models stay on the laptop. Only the tool results (short text) go to the cloud.

```bash
python Agents_MCP_Skills/Agents_lab17_mcp_agent_gpt.py --prompt "What is in Data/Robot.jpg? How many cups would 17 such robots hold?"
python Agents_MCP_Skills/Agents_lab18_mcp_agent_claude.py --effort medium --prompt "..."
```

Options for both: `--prompt` (default: describe `Data/Robot.jpg` and compute 17 * 24),
`--effort` (`low` default, `medium`, `high`, `xhigh`, `max`), `--max-turns`.

Same loop, different API shapes (from the Lab 18 docstring):

| Lab 17 (OpenAI Responses) | Lab 18 (Anthropic Messages) |
| --- | --- |
| `tools=[{"type": "function", ...}]` | `tools=[{"name", "description", "input_schema"}]` |
| output item `"function_call"` | content block `"tool_use"` (`stop_reason == "tool_use"`) |
| `"function_call_output"` item | `"tool_result"` block in the next user message |
| `reasoning={"effort": ...}` | `output_config={"effort": ...}` |

Other differences you will see in the code:

- Lab 17 talks to Foundry through the v1 endpoint: `OpenAI(base_url=AZURE_OPENAI_ENDPOINT + "/openai/v1/")`,
  model = your `AZURE_OPENAI_DEPLOYMENT`. The tools are sent with `"strict": False` because MCP schemas have optional arguments.
- Lab 18 uses model `claude-opus-5-5` with `max_tokens=16000`. Thinking is always on for this model; effort sets
  its depth. Claude's full turn (thinking and `tool_use` blocks) is appended to the history, and all
  `tool_result` blocks go back in one user message, with `is_error` set when a tool failed.
- Lab 18 first asks for the server-side refusal fallback (beta). If the workspace has not enabled it, it prints a
  note and runs without it. A `refusal` stop reason is printed as "Declined (category)".

### Measured result

Measured on 2026-11-23 with the default prompt ("look at Data/Robot.jpg ... then compute 17 * 24"):

| Lab | Model | Tools called (one turn) | Answer | Time |
| --- | --- | --- | --- | --- |
| 17 | GPT on Microsoft Foundry | `describe_image`, `calculate` | robot holding/serving a cup of coffee; 408 | 23 s |
| 18 | Claude Opus 5.5 | `describe_image`, `calculate` | robot holding/serving a cup of coffee; 408 | 24 s |

Both models asked for both tools in the same turn. The time is printed at the end of each run. It starts after
`tools/list`, so it includes the model calls and loading Phi-3.5-vision on the first `describe_image` call.

### Exercises

1. Add a `summarize_text` tool to Lab 16 backed by the Lab 03 `LLMPipeline` (TinyLlama), then ask the agent to
   "describe Data/Robot.jpg and summarize it in five words".
2. Run both agents at `--effort low` and `--effort high`. Compare tool calls, answer and time.
3. Lab 18: replace the hand-written loop with the SDK's `client.beta.messages.tool_runner(...)` and
   `anthropic.lib.tools.mcp.async_mcp_tool(...)`.
4. Ask for a file that does not exist. Check that the error is sent back to the model and how it recovers.

---

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `ModuleNotFoundError: mcp` | `pip install -r Agents_MCP_Skills/requirements.txt` |
| Labs 14–18: `ImportError` for `FastMCP` or `mcp.server` | You have mcp 2.x (`pip show mcp`). The labs need 1.x: `pip install "mcp>=1.20,<2"`. |
| Lab 15: "Failed to discover tools" | Run from the repo root; check that `Agents_lab14_mcp_skills_server.py` and `cloud_model.py` are next to the client. |
| Lab 15: `ask_cloud_model` or `image2mermaid` errors | Set the Lab 01 `.env` keys (`AZURE_OPENAI_*`). Behind a proxy with a private Foundry resource, add `.openai.azure.com` to `NO_PROXY` (see Setup). |
| Lab 16: "Model folder not found" | Download the model into the repo root, or set `LAB_MODELS_DIR`. |
| Labs 15, 17: `403 Public access is disabled` | Add `.openai.azure.com` to `NO_PROXY` and open a new terminal (see Setup). |
| Lab 18: authentication error | Set `ANTHROPIC_API_KEY` in `.env`. |
| `mcp dev` fails | Install Node.js; the Inspector is a Node app. |
| Streamlit port in use | `streamlit run ... --server.port 8502` |

Further reading: [MCP specification](https://modelcontextprotocol.io) ·
[MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk). Next: `README_Skills.md` (Labs 19–22).
