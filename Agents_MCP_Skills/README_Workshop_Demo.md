# Workshop live demo guide (PAGA-3: Agents, MCP and Skills)

A run sheet for demoing Labs 11–23 live, in the order of the PAGA-3 hands-on deck
([PAGA-3_Agents_MCP_Skills.pptx](PAGA-3_Agents_MCP_Skills.pptx), in this folder; slide numbers below refer to it).
Each step gives the command, what to show, what students should see, how long it takes and the talking points.
Timings were measured on the instructor laptop (Intel CPU, integrated GPU and NPU, OpenVINO GenAI 2025.4):
Labs 16–18 and 20 on 2026-11-23, the others on 2026-11-09. The cloud helpers in `cloud_model.py` (used by Labs 14,
15 and 21) were timed on 2026-11-23 with the Foundry deployment `gpt-5.4`. Your numbers will differ.

What to say on each slide, and which concepts each lab illustrates: [PAGA-3_HandsOn_Speaker_Notes.md](PAGA-3_HandsOn_Speaker_Notes.md).
For student self-study, use the [lab table in README.md](README.md#labs) and [Reproduce every lab](#reproduce-every-lab) below.

---

## Reproduce every lab

Run from the repo root.

| Lab | Command | Expected | Measured |
| --- | --- | --- | --- |
| 11 | `streamlit run Agents_MCP_Skills/Agents_lab11_visual_agent.py` | multi-step visual analysis, plain loop | — |
| 12 | `streamlit run Agents_MCP_Skills/Agents_lab12_visual_agent_langgraph.py` | 3-step workflow, 3 VLM calls | ≈ 8 s (GPU) |
| 13 | `streamlit run Agents_MCP_Skills/Agents_lab13_mcp_tutorial.py` | request → tool schema match → result | instant |
| 15 | `streamlit run Agents_MCP_Skills/Agents_lab15_mcp_skills_client.py` | 5 tools discovered over stdio; `Calculate 256 * 4 + 128` → 1152; `What is MLD in WiFi 7?` → `ask_cloud_model` answer | `ask_cloud_model` 4.4 s (helper alone) |
| 16 | `python Agents_MCP_Skills/Agents_lab16_mcp_openvino_server.py --self-test` | `Data/Robot.jpg` → "The robot is holding a cup of coffee." | model load 16 s (GPU) |
| 17 | `python Agents_MCP_Skills/Agents_lab17_mcp_agent_gpt.py` | GPT calls `describe_image` and `calculate` in one turn; 17 × 24 = 408 | 23 s |
| 18 | `python Agents_MCP_Skills/Agents_lab18_mcp_agent_claude.py` | Claude calls the same two tools; same answers | 24 s |
| 19 | `streamlit run Agents_MCP_Skills/Agents_lab19_skills_tutorial.py` | skill routing; weather → recommendation chaining | instant |
| 20 | `streamlit run Agents_MCP_Skills/Agents_lab20_skills_langgraph.py` | LLM router picks the skill | Qwen3 ≈ 2.6 s · Foundry 2.4 s per request |
| 21 | `streamlit run Agents_MCP_Skills/Agents_lab21_skills_demo.py` | `calculate (3 + 4) * 6` → 42; `What is MLD in WiFi 7?` → cloud model answer; a 3-box flowchart image → `flowchart LR  Camera --> VLM --> Decision` | `ask_cloud_model` 4.4 s · `image_to_mermaid` 2.7 s (helpers alone) |
| 22 | `python Agents_MCP_Skills/Agents_lab22_agent_skills/openvino-course-labs/scripts/check_setup.py` | one OK / MISSING / WARN line per check | 2 s |
| 23 | `streamlit run Agents_MCP_Skills/Agents_lab23_multimodal_agent.py` | 3 analysis steps + a generated image prompt | ≈ 29 s per image (GPU) |

The two cloud tools (`ask_cloud_model`, `image2mermaid`) in Labs 15 and 21 use your Foundry deployment: the
Lab 01 `.env` keys. Labs 14–18 need `mcp` 1.x; `requirements.txt` pins `mcp>=1.20,<2`.

---

## Before class (15 minutes)

1. **Proxy (Labs 15, 17, 20, 21: the ones that call Foundry) — set it in the demo terminal, nowhere else.** A private Foundry resource answers
   `403 Public access is disabled` to requests that go through the corporate proxy. In the **PowerShell** terminal
   you will demo from:

   ```powershell
   $env:NO_PROXY += ",.openai.azure.com"     # set (this terminal only)
   $env:NO_PROXY -split ','                  # check: the list ends with .openai.azure.com
   ```

   This changes nothing on the computer: closing the terminal is the undo (see [After class](#after-class)).
   Do **not** use `setx` and do **not** delete `NO_PROXY` — it also holds the company list (localhost, internal
   domains). Other shells and the permanent variant: [Proxy: set, check, unset](../README_Reproduce_Demo.md#proxy-set-check-unset).
   Students on their own Azure for Students resources don't need this.
2. **Activate the environment and check the setup** (this is also the Lab 22 demo, so leave the output on screen):

   ```bash
   cd GenAI_APIs_Cloud_Local
   .venv\Scripts\activate
   python Agents_MCP_Skills/Agents_lab22_agent_skills/openvino-course-labs/scripts/check_setup.py
   ```

   Every line should be `OK` (the proxy `WARN` is fine if you did step 1 in this terminal).
3. **Dry-run the cloud agent once**, so you know the keys and tools work before anyone is watching:

   ```bash
   set LAB_DEVICE=GPU
   python Agents_MCP_Skills/Agents_lab18_mcp_agent_claude.py
   ```

   Expect two tool calls and "17 × 24 = 408" in about 25 s.
4. **Open two terminals** at the repo root: one for Streamlit apps, one for the command-line agents (Labs 16–18).
   Use `--server.port 8502` for the second Streamlit app if the first is still running.

---

## Part 1: Workflows with LangGraph (slides 5–6)

### Labs 11–12: the same agent, two ways (slide 6)

```bash
streamlit run Agents_MCP_Skills/Agents_lab12_visual_agent_langgraph.py
```

1. In the sidebar, choose **GPU** and click **🚀 Initialize LangGraph Agent**.
2. Upload `Data/Robot.jpg` and select the **Safety Inspection** workflow.
3. Click **🚀 Execute LangGraph Agent Workflow**.

- **Expect:** 3 steps and 3 VLM calls in about 8 s on GPU.
- **Talking point:** the graph on the slide — the conditional edge loops back to retry a low-quality answer.
  In Lab 11 the same logic is a hand-written `for` loop with manual state; in Lab 12 the state is a typed
  `AgentState` that flows through every node.
- **Optional:** open Lab 11 side by side (`--server.port 8502`) to show the plain-loop version.

---

## Part 2: Tools with MCP (slides 7–10)

### Lab 13: MCP concepts in one screen (slide 7)

```bash
streamlit run Agents_MCP_Skills/Agents_lab13_mcp_tutorial.py
```

- **Show:** click the example **What's the weather in Paris?**, then **Convert 100 kilometers to miles**.
  Point at the JSON schema of the chosen tool and the extracted parameters.
- **Talking point:** the model never sees your code — only the tool's name, description and `inputSchema`.
  Good descriptions are the whole game.

### Labs 14–15: a real server and client (slide 8)

```bash
streamlit run Agents_MCP_Skills/Agents_lab15_mcp_skills_client.py
```

1. Click **🔍 Discover MCP Tools** — the client starts Lab 14 as a subprocess and calls `tools/list`.
2. Click the example **Calculate 256 * 4 + 128**, then **🚀 Execute via MCP**.
3. Right after it, click **What is MLD in WiFi 7?** and **🚀 Execute via MCP** again.

- **Expect:** 5 tools listed (`image2mermaid`, `ask_cloud_model`, `calculator`, `text_analyzer`, `web_search`);
  the calculator returns 1152; the MLD question goes to `ask_cloud_model` and your Foundry deployment answers
  (4.4 s for the helper alone on 2026-11-23, plus the server start).
- **Talking point:** routing — the arithmetic runs locally in the server, the Wi-Fi question goes to the cloud
  model, and both travel the same `tools/call` path.
- **Talking point:** the same server works with Claude Desktop, VS Code or any MCP client — that is the point of a protocol.
- **Needs:** the Lab 01 `.env` keys for `ask_cloud_model` and `image2mermaid` (and the proxy step above behind a
  corporate proxy). Without them, demo `calculator`, `text_analyzer` and `web_search` only.

### Lab 16: your laptop's models become tools (slide 9)

```bash
python Agents_MCP_Skills/Agents_lab16_mcp_openvino_server.py --self-test
```

- **Expect:** `list_data_files`, `calculate('(17 + 25) * 2') -> 84`, then
  "The robot is holding a cup of coffee." after a 16 s model load on GPU (`LAB_DEVICE=GPU`).
- **Talking point:** each tool is a plain Python function with a docstring. `@mcp.tool()` turns the signature
  into a JSON schema and the docstring into the description.
- **Talking point:** models load lazily on the first call and stay loaded — the second `describe_image` is fast.

### Labs 17–18: cloud reasoning, local tools (slide 10)

```bash
python Agents_MCP_Skills/Agents_lab18_mcp_agent_claude.py
python Agents_MCP_Skills/Agents_lab17_mcp_agent_gpt.py
```

- **Show:** the `turn 1:` lines — both tools are requested in the *same* turn (parallel tool calls), run on the
  laptop, and only their short text results go back to the cloud.
- **Expect:** Claude 24 s, GPT 23 s; "holding/serving a cup of coffee" and 408.
- **Talking point:** walk the comparison table on the slide — same loop, different API shapes
  (`tool_use` / `tool_result` vs `function_call` / `function_call_output`).
- **Talking point:** privacy and cost — the image never leaves the device; the cloud model sees one sentence.
- **Live variation:** `--prompt "Transcribe and summarize Data/your_recording.wav"` after recording a 16 kHz WAV with
  Lab 07, or ask it to `generate_image` (about a minute on CPU — start it and move on).

---

## Part 3: Skills (slides 11–13)

### Lab 19: the Skills pattern (slide 12)

```bash
streamlit run Agents_MCP_Skills/Agents_lab19_skills_tutorial.py
```

1. Click **What's the weather in London?** → the weather skill runs and stores `current_weather` and
   `current_location` in `SkillContext`.
2. Type `What should I wear today?` and click **🚀 Execute** → the recommendation skill answers from that context,
   e.g. "☔ Bring an umbrella today!" with `context_used: current_weather, current_location`.
3. Click **🔄 Reset Context** and ask the same question again → `context_used` is empty and you get generic tips
   ("Try asking about the weather first, then ask for recommendations!").

- **Talking point:** that is chaining — the second skill builds on the first without the user repeating anything.
- **Note:** weather data is simulated and random, so the recommendation changes from run to run.

### Lab 20: a real LLM as the router (slide 12)

```bash
streamlit run Agents_MCP_Skills/Agents_lab20_skills_langgraph.py
```

1. In the sidebar, select **Qwen3 1.7B (Local, recommended)**, device **GPU**, and click **🚀 Initialize Agent**.
2. Ask (these routed correctly in testing):
   - `What's the weather in Jerusalem?` → weather skill
   - `calculate 12 * 7` → calculator, 84
   - `What is 15% of 240?` → calculator, 36

- **Expect:** about 2.6 s per request on GPU.
- **Talking point:** switch to **Microsoft Foundry deployment (Cloud, Lab 01)** and **🔄 Reload** — 2.4 s per
  request with your Lab 01 keys. Then **TinyLlama 1.1B** — it picks the wrong skill (1 of 6 correct in testing):
  routing quality depends on model size.
- **Avoid live:** "Remember that…" and sentiment requests on Qwen3 — they were sent to the wrong skill in testing.

### Lab 22: Agent Skills for coding agents (slide 13)

- **Show:** the `SKILL.md` front matter on the slide, then the `check_setup.py` output from *Before class*.
- **Optional live:** copy `Agents_MCP_Skills/Agents_lab22_agent_skills/openvino-course-labs` to `.claude/skills/`
  (Claude Code) or `.github/skills/` (Copilot in VS Code) and ask *"Is my laptop ready for Lab 16?"*.
- **Talking point:** same word, two things — Labs 19–21 are skills *inside your app*; Lab 22 is know-how *for any agent*,
  loaded only when its `description` matches the request.

---

## Part 4: Put it together (slide 16)

### Lab 23: the multimodal agent

```bash
streamlit run Agents_MCP_Skills/Agents_lab23_multimodal_agent.py
```

1. In the sidebar, click **🚀 Load Model** (choose GPU) and select the **🔄 Full Agentic Pipeline** demo mode.
2. Upload `Data/Robot.jpg` and click **▶️ Run Full Pipeline**.

- **Expect:** 3 analysis steps plus a generated image prompt, in about 29 s on GPU.
- **Talking point:** this covers *See → decide → Create-prompt*. Hear is Lab 07, Reason is Labs 01–02 / 17–18,
  Act is Labs 14–18, Create is Lab 09 — wiring the whole chain is the team design challenge.
- **Optional (Lab 21):** `streamlit run Agents_MCP_Skills/Agents_lab21_skills_demo.py` and try `calculate (3 + 4) * 6`
  (42), then `What is MLD in WiFi 7?` (cloud model) — the same local-tool vs cloud-model routing as Lab 15, without
  MCP — and a web search. Upload a diagram in the sidebar and click **🔄 Convert to Mermaid** to show `image2mermaid`.

---

## After class

1. **Proxy — undo.** Close the demo terminal. That is all you need after the session-only setting.
   To undo in a terminal you keep open:

   ```powershell
   $env:NO_PROXY = ($env:NO_PROXY -split ',' | ? { $_ -ne '.openai.azure.com' }) -join ','
   ```

2. **Only if you made the permanent change** (Option B in the Part 1 guide), remove just that entry and keep the rest:

   ```powershell
   $v = [Environment]::GetEnvironmentVariable('NO_PROXY','User')
   [Environment]::SetEnvironmentVariable('NO_PROXY', (($v -split ',') | ? { $_ -and $_ -ne '.openai.azure.com' }) -join ',', 'User')
   ```

3. **Verify in a new terminal:** `[Environment]::GetEnvironmentVariable('NO_PROXY','User')` must **not** contain
   `.openai.azure.com` and must still contain your original entries (localhost, 127.0.0.1, your company domains).
   If entries are missing, restore your backup:
   `[Environment]::SetEnvironmentVariable('NO_PROXY', (Get-Content "$HOME\no_proxy_backup.txt" -Raw).Trim(), 'User')`.
4. Stop any Streamlit apps still running (Ctrl+C in their terminals).

---

## If something goes wrong

| Symptom | Fix |
| --- | --- |
| Labs 15, 17, 20, 21: `403 Public access is disabled` | This terminal still uses the corporate proxy: `$env:NO_PROXY += ",.openai.azure.com"`, then re-run. Undo: see [After class](#after-class). |
| Lab 17: `404 DeploymentNotFound` | `AZURE_OPENAI_DEPLOYMENT` must name a deployment that exists on your resource. |
| Lab 18: `server-side fallback not enabled` | Expected on some workspaces; the script continues without it. |
| Lab 16/17/18: `Model folder not found` | Download the model into the repo root, or set `LAB_MODELS_DIR` to where it is. |
| Lab 16 tool: `Only files inside the course repo are allowed` | Use repo-relative paths such as `Data/Robot.jpg` (by design: tools validate their inputs). |
| Lab 17/18 ends with `Exception ignored ... I/O operation on closed pipe` | Harmless Windows asyncio message at interpreter exit, printed after the answer. Ignore it. |
| First GPU call takes 15+ s | Model compilation on first load. Do the dry run before class, or use CPU. |
| `ask_cloud_model` / `image2mermaid` fails (Labs 15, 21) | They use your Foundry deployment: check the Lab 01 `.env` keys (`AZURE_OPENAI_*`) and, behind a proxy, `NO_PROXY` as above. |
| Labs 14–18: `ImportError` for `FastMCP` or `mcp.server` | mcp 2.x is installed; the labs need `pip install "mcp>=1.20,<2"`. |
| Streamlit: port already in use | Add `--server.port 8502`, or close the previous app. |
