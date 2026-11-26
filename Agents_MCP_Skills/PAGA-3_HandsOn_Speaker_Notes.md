# PAGA-3 hands-on: speaker notes (Agents, MCP and Skills)

Notes for presenting [PAGA-3_Agents_MCP_Skills.pptx](PAGA-3_Agents_MCP_Skills.pptx) (21 slides) together with
Labs 11–23. Each slide below lists the concepts to stress, what to say, which code to show, a question for the
class, and the bridge to the next slide.

How this file relates to the others:

- **This file:** what to *say* and which *concept* each slide and lab carries.
- **[README_Workshop_Demo.md](README_Workshop_Demo.md):** what to *click*, the expected output, timings, and fixes
  when something breaks. Keep it open in a second window during the demos.
- **The notes inside the .pptx:** a short version of the notes below, for the presenter view.

Code links open the file on GitHub (`main` branch) at the function to show on screen. Line numbers are from
2026-11-23 and can drift as the labs change. If one is off, search for the function name.

---

## The five threads

Every slide adds to one of these five ideas. Name the thread out loud when a lab illustrates it, and come back
to all five in the recap (slide 17). At the end, students should be able to explain each one in a sentence.

| # | Thread | One sentence to repeat | Where it shows up |
| --- | --- | --- | --- |
| T1 | **The loop** | A model answers once; an agent loops (reason → act → observe) until the goal is met or a turn limit stops it. | Slide 3; Lab 12 retry; Labs 17–18 `for turn in range(max_turns)`; Lab 23 self-check |
| T2 | **Who decides the next step?** | Your code, a rule, or the model, and each choice gives a different amount of control and flexibility. | Lab 12 edges · Labs 13, 15, 19, 21 regex/trigger rules · Labs 17, 18, 20 the LLM · Lab 22 the coding agent |
| T3 | **The model sees only the contract** | The model never reads your code, only a name, a description and a schema. Write them for the model. | Slide 7; Lab 16 docstrings; Lab 22 `description:` front matter |
| T4 | **Where does state live?** | Someone has to remember what happened: a typed state, a message list, a context object, or nobody. | Lab 12 `AgentState`; Labs 17–18 `messages`/`items`; Lab 19 `SkillContext`; MCP calls hold no state |
| T5 | **Cloud reasoning, local data** | Send the cloud a sentence, not your data. Decide placement on cost, latency and privacy. | Labs 16–18 (the image stays on the laptop); Lab 20 local vs Foundry; slide 16 design challenge |

Guardrails come up alongside these threads: turn limits, input validation, and returning errors as results.
They are collected on slide 17.

### T2 across the session (useful on slides 8, 12 and 14)

| Who picks the next step | Labs | Strength | Weakness |
| --- | --- | --- | --- |
| Your edges and conditions | 11, 12, 23 | Predictable, testable | Only does what you drew |
| Rules: regex patterns, keyword triggers, confidence scores | 13, 15, 19, 21 | Fast, free, explainable | Brittle: misses rephrasings |
| An LLM, from tool schemas or a routing prompt | 17, 18, 20 | Handles open-ended requests | Slower and costs money; small models choose badly (Lab 20 TinyLlama) |
| A coding agent, from a `SKILL.md` description | 22 | Reuses team know-how in any agent | Only as good as the description |

Students often assume every app with "agent" in the title asks an LLM. Labs 13, 15 and 21 do not. Their routers
are regex tables that stand in for the model, so the protocol can be shown without API cost. Say this when you
reach those labs. It sets up Labs 17–18, where a real model makes the same choice from the same schemas.

---

## Suggested timing (about 3 hours with a break)

These times are a suggestion. Adjust them to your slot. The demo lengths come from the measured runs in the
run sheet plus time to talk.

| Block | Slides | Labs | Minutes |
| --- | --- | --- | --- |
| Opening and agent concepts | 1–4 | — | 15 |
| LangGraph | 5–6 | 11–12 | 20 |
| MCP | 7–10 | 13–18 | 50 |
| *Break* | | | 10 |
| Skills | 11–13 | 19–22 | 35 |
| Choosing, capstone, practices | 14–17 | 23 | 30 |
| Lab map, homework, questions | 18–21 | — | 15 |

If you are short on time, skip Lab 11 side by side, Lab 13 (go straight to 15) and the optional Lab 21. Do not
cut Labs 17–18: they are the payoff where all five threads meet.

---

## Slide 1: Title: Agents · MCP · Skills

**Concepts:** where this session sits: Part 1 *called* models; Part 2 *builds agents* around them.

**Say:**

- "In Labs 01–10 every program made one call: prompt in, answer out. Today the same models plan, call tools
  and check their own results."
- Everything is in `Agents_MCP_Skills/`, Labs 11–23, and every command runs from the repo root.

**Before you speak** (from the run sheet, *Before class*): `check_setup.py` output on screen, one dry run of
Lab 18, and `$env:NO_PROXY += ",.openai.azure.com"` in the demo terminal only.

**Bridge:** "Here is the path through the session."

---

## Slide 2: Today's session map

**Concepts:** the three building blocks (LangGraph, MCP, Skills) plus the capstone. Introduce the five threads
here in one breath.

**Say:**

- Five blocks, each with labs students can rerun at home. Lab numbers continue from Part 1, so each lab number
  is unique in the course.
- "Keep five questions in mind all session: Is it looping? Who decides the next step? What does the model
  actually see? Where is the state? What runs in the cloud and what stays on the laptop?"
- Check the *Bring* line: Labs 01–10 run, `.env` keys from Labs 01–02, `requirements.txt` installed.

**Ask:** "Hands up if Lab 04 (vision) ran on your GPU." This tells you who will hit model-load delays later.

**Bridge:** "So what makes something an agent instead of a model call?"

---

## Slide 3: What is an agent? (T1)

**Concepts:** **T1, the loop**: perceive → reason → act → observe, with a **stop condition**.

**Say:**

- Key sentence: *a model answers once; an agent loops until the goal is met.*
- Walk the five boxes. Stress **Observe**: the agent reads the tool result and decides whether it is done.
  That self-check is what separates an agent from a script.
- The two terminal lines are the whole algorithm. The second line matters as much as the first: **always cap
  the loop**. Labs 17–18 stop after 6 turns (`--max-turns 6`).
- Why tools: an LLM alone has no live data, approximates arithmetic, and can only produce text.

**Ask:** "Name a task you would hand to an agent. Which tools would it need, and when should it stop?" Write two
answers on the board. Come back to them on slide 16.

**Bridge:** "Same model, two setups. What actually changes?"

---

## Slide 4: LLM alone vs agent with tools

**Concepts:** the model is the same. The difference is **the loop plus the tools** (T1). Introduces T5: tools
reach *your* data.

**Say:**

- Go row by row. The *Math* row makes the point quickly: a model predicts digits; an agent calls a calculator
  and gets an exact answer. Labs 17–18 compute 17 × 24 = 408 with a tool, not from the model's memory.
- *Mistakes* row: an agent can only fix what it can observe. That is why tool results go back into the
  conversation.

**Ask:** "Which right-hand rows did Labs 01–03 do?" *None. Each was a single call.*

**Bridge:** "Once you have a loop, you need to write its control flow somewhere. LangGraph writes it as a graph."

---

## Slide 5: LangGraph: agents as graphs (T2, T4)

**Concepts::**

- **T2:** with LangGraph, *your edges* decide the next step. The model fills in each step but does not choose
  the path.
- **T4:** one typed state object (`TypedDict`) is the contract between nodes. Nothing is hidden in globals.

**Say:**

- Nodes are plain functions, small and testable. Edges say what runs next. Conditional edges are the decisions.
  Cycles allow retries. Streaming shows each step as it finishes.
- Building blocks: `StateGraph(AgentState)` → `add_node` → `add_edge` / `add_conditional_edges` → `compile()` →
  `invoke(state)`.

**Show:** the state type in [Agents_lab12_visual_agent_langgraph.py:43](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab12_visual_agent_langgraph.py#L43),
`AgentState`. Point at `results: Annotated[List, operator.add]`: LangGraph *appends* each node's results
instead of overwriting them. That is a reducer, and it is how state builds up across steps.

**Bridge:** "Here is the same visual-inspection agent written two ways."

---

## Slide 6: Labs 11–12: agentic workflows with LangGraph

**Concepts::**

- **T1 in practice:** a retry loop. Lab 12 retries a low-quality answer up to 2 times. Lab 11 has no self-check.
- **T2:** a routing function only *reads* state and returns a branch name.
- Trade-off: for three fixed questions, the plain loop is shorter. The graph pays off when the flow has branches
  and retries.

**Demo:** run sheet, *Labs 11–12*. Lab 12 on GPU, `Data/Robot.jpg`, *Safety Inspection*, about 8 s for 3 VLM calls.

**Show in code:**

- Lab 11, the plain loop:
  [Agents_lab11_visual_agent.py:79](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab11_visual_agent.py#L79) `execute_workflow`, a `for` loop with a
  local list as its state.
- Lab 12, the conditional edge:
  [Agents_lab12_visual_agent_langgraph.py:159](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab12_visual_agent_langgraph.py#L159) `should_continue`
  returns `"complete"` or `"continue"`.
- Lab 12, the retry bookkeeping:
  [Agents_lab12_visual_agent_langgraph.py:101](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab12_visual_agent_langgraph.py#L101)
  `execute_analysis_step_node`. On a low-quality answer it increases `retry_count` and does *not* advance
  `current_step`, so the graph loops back and asks again.
- **Common mistake to point out:** changes made inside a routing function are not saved. That is why the retry
  counter is updated in the node and not in `should_continue`. Students who add a node in the exercise will
  run into this.

**Ask:** "Where would you add a `safety_check` node that runs only when a person is detected? Is that a new edge
or a new conditional edge?" *A conditional edge after the analysis step that reads the result from the state.*

**Exercise (slide):** add the `safety_check` node.

**Bridge:** "In LangGraph we decided every step ourselves. Next, the model decides which tool to use, and for
that it needs a standard description of each tool."

---

## Slide 7: MCP: one standard way to describe tools (T3)

**Concepts::**

- **T3, the most important idea of the MCP block:** the model never sees your code, only `name`,
  `description` and `inputSchema`. A vague description means the tool will not be picked.
- Two verbs: `tools/list` (discover) and `tools/call` (run). The transport here is **stdio**: the server runs as a
  subprocess of the client.
- MCP calls are **stateless** (T4). Each call stands alone, and the agent keeps any memory.

**Say:**

- "MCP works like USB for tools. Write the server once, and Claude Desktop, VS Code, your own Python agent or
  any other MCP client can use it."
- Read the JSON on the slide as the model would: "Which argument is required? What happens if I leave out
  `question`?" *The default is used.*

**Ask:** "Rewrite the description `'Image tool'` so a model would pick it for 'what's in this photo?'". Collect one
or two answers. This is the core skill of tool design.

**Bridge:** "Lab 13 shows these pieces in one screen. Labs 14–15 split them into a real server and client."

---

## Slide 8: Labs 13–15: give agents tools with MCP (T2, T3)

**Concepts::**

- The client/server split: the server *offers* tools, the client *discovers* and *calls* them.
- **T2, say it plainly:** in Labs 13 and 15 a **regex router** picks the tool, not an LLM. The routing table
  stands in for the model so the protocol is visible and free to run. In Labs 17–18 a real model makes this
  choice from the same schemas.
- One request box can reach a local tool or a cloud model. The client sees only tool names and schemas.

**Demo:** run sheet, *Lab 13* and *Labs 14–15*. Lab 15: *Discover MCP Tools* (5 tools), `Calculate 256 * 4 + 128`
→ 1152, then `What is MLD in WiFi 7?` → `ask_cloud_model`.

**Show in code:**

- Server advertises: [Agents_lab14_mcp_skills_server.py:311](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab14_mcp_skills_server.py#L311)
  `list_tools`. Server executes: [line 407](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab14_mcp_skills_server.py#L407) `call_tool`.
- Client discovers and calls: [Agents_lab15_mcp_skills_client.py:113](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab15_mcp_skills_client.py#L113)
  `session.list_tools()` and [line 149](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab15_mcp_skills_client.py#L149) `session.call_tool(...)`.
- The router: [Agents_lab15_mcp_skills_client.py:198](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab15_mcp_skills_client.py#L198) `MCPRouter`.
  Point at the Wi-Fi/MLD regex that sends the question to `ask_cloud_model`.
- The cloud tool itself is one Responses API call to your Foundry deployment:
  [cloud_model.py:42](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/cloud_model.py#L42) `ask_cloud_model`.

**Ask:** "Type `How does multi-link operation work?` Where will it go?" *It is the same Wi-Fi topic as MLD, but no
pattern mentions 'multi-link', so the router sends it to `web_search`, with confidence "high". Rules break on
rephrasing and still report high confidence. That is the reason to let a model route.* (Checked against the
Lab 15 router on 2026-11-23.)

**Watch out:** `403 Public access is disabled` means the `NO_PROXY` line is missing in this terminal.

**Bridge:** "These tools were toy functions. Next, the models from Part 1 become tools."

---

## Slide 9: Lab 16: your laptop's models become MCP tools (T3, guardrails)

**Concepts::**

- **T3:** *signature → schema, docstring → description.* With FastMCP the Python function is the contract.
- **Guardrail:** an agent's arguments are **untrusted input**. The tools read only files inside the repo.
- **Engineering lesson:** in a stdio server, stdout *is* the protocol. Anything printed to stdout corrupts it.
  Native libraries are imported at start-up, so nothing blocks or writes to stdout during a tool call.
- Load once, reuse: models load on first use and stay cached in `_pipes`.

**Demo:** `python Agents_MCP_Skills/Agents_lab16_mcp_openvino_server.py --self-test` (`LAB_DEVICE=GPU`): about
16 s model load, then "The robot is holding a cup of coffee."

**Show in code:**

- A tool: [Agents_lab16_mcp_openvino_server.py:93](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab16_mcp_openvino_server.py#L93) `describe_image`.
  Read the docstring aloud: "this sentence is all the model will know about this function."
- The guardrail: [line 76](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab16_mcp_openvino_server.py#L76) `_inside_repo` resolves the path and refuses
  anything outside the repo.
- The other tools: `transcribe_audio` (Whisper), `generate_image` (Stable Diffusion), `calculate`,
  `list_data_files`.

**Ask:** "What could go wrong if `describe_image` accepted any path?" *An agent, or a prompt injected into a
document it read, could ask for files such as `~/.ssh/id_rsa`.* Tie this to slide 17.

**Bridge:** "The server is ready. Now a cloud model gets to drive it."

---

## Slide 10: Labs 17–18: cloud reasoning, local tools (all five threads)

This slide is where all five threads meet. Allow the most time here.

**Concepts::**

- **T1:** the real agent loop: ask the model → if it requested tools, run them → append the results → ask again,
  capped at `max_turns`.
- **T2:** now the **LLM** picks the tools, from the same MCP schemas the regex router ignored.
- **T3:** the MCP `inputSchema` is passed to the model unchanged.
- **T4:** state is the growing message list (`messages` for Claude, `items` for GPT).
- **T5:** the image never leaves the laptop. The cloud sees one sentence of tool output.
- **Parallel tool calls:** both tools are requested in the *same* turn.
- **Errors as results:** a failed tool is reported back to the model, not dropped.

**Demo:** run sheet, *Labs 17–18*. Run Lab 18 (Claude) then Lab 17 (GPT). Point at the `turn 1:` lines.
Expect about 24 s and 23 s, "holding a cup of coffee" and 17 × 24 = 408.

**Show in code:**

- Schemas → model tools: [Agents_lab18_mcp_agent_claude.py:78](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab18_mcp_agent_claude.py#L78) (one list
  comprehension, schema unchanged) and [Agents_lab17_mcp_agent_gpt.py:60](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab17_mcp_agent_gpt.py#L60).
- The loop and its cap: [Agents_lab18_mcp_agent_claude.py:83](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab18_mcp_agent_claude.py#L83)
  `for turn in range(1, args.max_turns + 1)`, and the stop test at
  [line 92](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab18_mcp_agent_claude.py#L92) `if resp.stop_reason != "tool_use"`.
- Errors as results: [Agents_lab17_mcp_agent_gpt.py:82](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab17_mcp_agent_gpt.py#L82)
  `except Exception as e: text, is_error = f"Error: {e}", True`.
- The two API shapes side by side are summarized in the docstring at the top of
  [Agents_lab18_mcp_agent_claude.py:8](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab18_mcp_agent_claude.py#L8):
  `function_call` / `function_call_output` vs `tool_use` / `tool_result`; `reasoning={...}` vs
  `output_config={...}`.

**Say:**

- "This loop is twenty lines. Every agent framework has this loop inside it."
- "The model asked for `describe_image` and `calculate` at once, because it saw that they don't depend on each
  other."
- "Count what crossed the network: the prompt, two short tool results, the answer. No pixels."

**Ask:**

- "What would happen with `--max-turns 1`?" *The model requests tools, and the loop ends before it can use the
  results: "Stopped after 1 turns".*
- "Which costs more: sending the image to a cloud vision model, or this?" Discuss tokens, latency and privacy.

**Live variation if time allows:** `--prompt "Transcribe and summarize Data/<your>.wav"` with a Lab 07 recording.

**Bridge:** "Tools are single functions with no memory. What if we want packaged capabilities that remember
and build on each other? Those are skills."

---

## Slide 11: Skills: packaged know-how that chains (T2, T4)

**Concepts::**

- A skill = **triggers + logic + shared context**.
- **T4:** `SkillContext` is the memory that MCP tools lack. One skill writes, the next one reads.
- **T2:** the orchestrator scores every skill (confidence) and runs the best one, a rule-based router.
- **Chaining:** the user does not repeat themselves. "What should I wear?" already knows the weather.

**Show in code:**

- [Agents_lab19_skills_tutorial.py:112](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab19_skills_tutorial.py#L112) `SkillContext`: `variables`
  and `previous_results`.
- [line 556](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab19_skills_tutorial.py#L556) `select_skill`: loop over skills, keep the highest
  `get_confidence`. Compare with the LLM router coming up in Lab 20.

**Say:** "Weather writes `current_weather`; recommendation reads it. After *Reset Context* the same question gets
generic tips. The difference is the memory, not the model."

**Bridge:** "Let's see it live, then replace the rules with an LLM."

---

## Slide 12: Labs 19–21: composable skills (T2, T5)

**Concepts::**

- **Tool vs skill** (table on the slide): a tool is a stateless function routed by schema; a skill is a
  capability with shared context and built-in chaining.
- **T2 progression in one slide:** Lab 19 uses keyword triggers, Lab 20 uses an **LLM router** inside a LangGraph
  graph, and Lab 21 uses regex routing to real local tools plus the cloud model.
- **T5:** Lab 20 changes the brain: local Qwen3-1.7B or your Foundry deployment. **Model size matters for
  routing.** TinyLlama chose the right skill 1 time in 6 in testing.

**Demo:** run sheet, *Lab 19* (weather → wear → reset) and *Lab 20* (Qwen3 on GPU, about 2.6 s per request; Foundry
about 2.4 s; then TinyLlama). Lab 21 is optional, also listed under *Part 4* in the run sheet.

**Show in code:**

- Lab 20 graph: [Agents_lab20_skills_langgraph.py:614](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab20_skills_langgraph.py#L614) `_build_graph`
  (LangGraph again, T2 by edges) and the LLM selection node at
  [line 717](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab20_skills_langgraph.py#L717) `_select_skill_node`. The model is asked to pick a skill name.
- Lab 21 router: [Agents_lab21_skills_demo.py:560](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab21_skills_demo.py#L560) `route`, the same regex
  approach as Lab 15 but without MCP.

**Ask:** "Lab 20 combines two of today's three ideas. Which two?" *LangGraph for the workflow and Skills for the
logic. The LLM is only the router.*

**Avoid live:** "Remember that…" and sentiment requests on Qwen3, which were misrouted in testing.

**Exercise (slide):** a `TranslateSkill` chained after `TextAnalysisSkill`.

**Bridge:** "Those skills live inside our app. The same word also names something for coding agents."

---

## Slide 13: Lab 22: Agent Skills, SKILL.md for coding agents (T3)

**Concepts::**

- **Same word, two things:** Labs 19–21 are skills *inside your app*. Agent Skills are an **open format** (a folder
  with `SKILL.md`) that Claude Code, Copilot in VS Code and other agents load.
- **Progressive disclosure:** at start-up the agent reads only `name` + `description`. When a request matches, it
  loads the body. It runs bundled scripts only when needed. This keeps the context small with many skills
  installed.
- **T3 again:** the `description` decides when the skill loads, just as a tool description decides when a tool
  is called.

**Show:**

- [Agents_lab22_agent_skills/openvino-course-labs/SKILL.md](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab22_agent_skills/openvino-course-labs/SKILL.md),
  the front matter. Read the description aloud and point at the phrase "Use when a student asks…": a trigger
  written for a model.
- The `check_setup.py` output left on screen from *Before class*.
- Optional live: copy the folder to `.claude/skills/` or `.github/skills/` and ask the coding agent *"Is my laptop
  ready for Lab 16?"*.

**Ask:** "Write a one-line description for a `lab-report-writer` skill. When should it load, and when should it
*not*?"

**Bridge:** "We now have three ways to give an agent abilities. How do you choose?"

---

## Slide 14: LangGraph, MCP or Skills?

**Concepts:** the comparison as a summary of the threads. Read the table *by rows*, because each row is a thread:
*Next step chosen by* = T2, *State* = T4.

**Say:**

- They are not competitors. **LangGraph orchestrates, Skills hold the logic, MCP connects to the outside world.**
- Lab 20 already combined LangGraph and Skills. Labs 17–18 combined an LLM loop and MCP.

**Ask:** "In Lab 18, which column was in charge of the next step?" *The model, through MCP schemas. There is no
LangGraph there; the loop is a plain `for`.*

**Bridge:** "Here are the same three, plus Agent Skills, as decisions you'd make on a project."

---

## Slide 15: When to use what

**Concepts:** choose based on the problem, not on what is popular.

**Say** (one line each):

- **MCP:** an external service other agents should reuse.
- **Python Skills:** your own logic must share context and chain.
- **LangGraph:** branches, retries or loops that you want to see and test.
- **Agent Skills:** a coding agent should follow your team's procedure and run your scripts.

**Ask:** "For your project, which one do you start with, and why?" Take two or three answers. Push back on
"all of them". The best practice on slide 17 is *start simple*.

**Bridge:** "Now let's put the stages together."

---

## Slide 16: Lab 23: the multimodal agent (T1, T5)

**Concepts::**

- **Hear → See → Reason → Act → Create**, where each stage maps to a lab students have already run.
- **T1:** Lab 23 has the same self-check as Lab 12 (`_is_low_quality_result`).
- **T5:** the design challenge is a placement decision. What runs in the cloud and what stays local, justified
  by cost, latency and privacy.

**Demo:** run sheet, *Lab 23*. GPU, *Full Agentic Pipeline*, `Data/Robot.jpg`. About 29 s for 3 analysis steps plus a
generated image prompt.

**Show in code:**

- [Agents_lab23_multimodal_agent.py:228](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab23_multimodal_agent.py#L228) `execute_analysis_workflow` and
  [line 307](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab23_multimodal_agent.py#L307) `_is_low_quality_result`, the observe step.
- [line 395](https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local/blob/main/Agents_MCP_Skills/Agents_lab23_multimodal_agent.py#L395) `generate_creative_prompt`: See feeds Create.

**Say:** "The app covers See, decide and Create-prompt. Hear is Lab 07, Reason is Labs 17–18, Act is Labs 14–16,
Create is Lab 09. Connecting the whole chain is your team's job."

**Ask:** go back to the two agent ideas from slide 3. "Which stages would each need? What would you keep local?"

**Design challenge (teams):** one real user, one pain point, at least two stages wired together, and a
cloud/local split justified with cost, latency and privacy.

---

## Slide 17: Best practices for agentic systems (recap of the threads)

**Concepts:** use this slide to tie the session together. For each quadrant, name the lab where the class saw it.

| Practice | Where students saw it |
| --- | --- |
| Cap the loop | Labs 17–18 `--max-turns 6` (T1) |
| Log every tool call and result | The `turn 1: describe_image(...) -> ...` lines in Labs 17–18 |
| Keep raw data on device, send summaries | Labs 16–18: the image stays local (T5) |
| Small local models route worse | Lab 20 TinyLlama vs Qwen3 vs Foundry (T2, T5) |
| Clear names, specific descriptions | Slide 7, Lab 16 docstrings, Lab 22 `description:` (T3) |
| Validate inputs | Lab 16 `_inside_repo` |
| Return errors as results | Lab 17 `except` → `is_error` back to the model |
| Start simple; add steps when measured | Lab 11 vs Lab 12: the loop was enough for three fixed steps |

**Ask (quick recap round):** ask one student per thread for its one sentence (T1–T5 in the table at the top).

---

## Slide 18: Lab map, Labs 11–23

**Say:**

- One folder; run every command from the repo root (the model folders and `Data/` are there).
- `mcp` is pinned below 2.0 because 2.x changed the server API. If Labs 14–18 fail on import, check `pip show mcp`.
- Labs 14, 15, 17, 20 and 21 use the cloud model: the Lab 01 `.env` keys. Lab 18 needs `ANTHROPIC_API_KEY`.
- The run sheet lists the expected output and timing for every lab, so students can check their own runs.

---

## Slide 19: Homework

**Tie each item to a thread**, so students see why it is assigned:

1. **Run Labs 17 and 18 with your own prompt.** Compare tool calls, time and answers (T1, T2).
2. **Add a `summarize_text` tool** to the Lab 16 server and call it from Lab 17 or 18 (T3: the docstring decides
   whether the model uses it).
3. **Write a `TranslateSkill` or a `SKILL.md`** (T4 chaining, or T3 description).
4. **Project design slide:** your agent's tools and the cloud/local split, with reasons (T5).

**Tip for item 2:** "If the model never calls your new tool, fix the description before you touch the code."

---

## Slide 20: Resources

Point out two links: the **MCP Inspector**, which lets students call their Lab 16 tool without an agent and is the
first thing to try when the model does not call it, and the **Agent Skills standard** for homework item 3.

---

## Slide 21: Questions?

**Next session:** retrieval-augmented generation. Bridge: "Today the agent reached your *tools*. Next time it
reaches your *documents*. Retrieval is one more tool in the loop."

**After class:** close the demo terminal (this undoes `NO_PROXY`) and stop any Streamlit apps. See the run sheet,
*After class*.

---

## Questions students ask, with short answers

| Question | Answer |
| --- | --- |
| "Lab 15 calls itself an agent, but where's the LLM?" | Its router is regex rules standing in for the model (T2). Lab 17/18 is the same idea with a real model choosing from the same schemas. |
| "Why MCP if I can just call the Python function?" | Inside one program you can. MCP matters when *other* agents (Claude Desktop, VS Code, a teammate's app) should use your tool without your code. |
| "Is a skill just a tool with extra steps?" | A tool is one stateless function. A skill bundles logic with shared context and chains with other skills. A `SKILL.md` is instructions plus scripts for a coding agent. |
| "Do I need LangGraph for an agent?" | No. Labs 17–18 are a plain `for` loop. Use LangGraph when the flow has branches and retries you want to see and test (Lab 11 vs 12). |
| "Why did the model call two tools at once?" | They were independent, so the model requested both in one turn (parallel tool calls). The loop runs them all and returns all results together. |
| "Why is the first GPU call so slow?" | The model is compiled on first load (about 16 s for Phi-3.5-vision). It stays loaded, so later calls are fast. |
| "Why not send the image to GPT directly?" | You can, but then the image leaves the device and you pay for image tokens. Here the local model looks and the cloud model reasons over one sentence (T5). |
| "Why is TinyLlama so bad at routing?" | Choosing among skills means following a format and comparing options. A 1.1B model does this poorly; Qwen3-1.7B does it reliably on the requests we tested. |

---

*Timings are from the instructor laptop (Intel CPU with integrated GPU and NPU), measured 2026-11-09 and
2026-11-23. The run sheet has the per-lab measurements. Your numbers will differ.*
