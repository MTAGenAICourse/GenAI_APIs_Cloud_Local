# Labs 19–22: Skills — Shared Context, Chaining and Agent Skills

A skill is a unit of agent capability that can read and write a shared context, so one skill can build on
another's result. Lab 19 shows the pattern with keyword routing. Lab 20 puts the same skills in a LangGraph
graph with a real LLM as the router. Lab 21 routes requests to local tools and to your cloud model.
Lab 22 shows the other meaning of "skill": the `SKILL.md` open format.

Run from the repo root (`GenAI_APIs_Cloud_Local`):

```bash
streamlit run Agents_MCP_Skills/Agents_lab19_skills_tutorial.py
streamlit run Agents_MCP_Skills/Agents_lab20_skills_langgraph.py
streamlit run Agents_MCP_Skills/Agents_lab21_skills_demo.py
python Agents_MCP_Skills/Agents_lab22_agent_skills/openvino-course-labs/scripts/check_setup.py
```

To run two apps at once, give the second one its own port: `--server.port 8502`.

---

## Setup

1. Finish the Part 1 setup in the repo root `README.md` (venv, models).
2. Install the Part 2 packages from the repo root: `pip install -r Agents_MCP_Skills/requirements.txt`
   (adds `langgraph` for Lab 20, and the web search packages for Lab 21).
3. Lab 20 brains (pick at least one):
   - **Local:** download a small LLM into the repo root. TinyLlama is the Lab 03 model:
     `hf download OpenVINO/TinyLlama-1.1B-Chat-v1.0-int4-ov --local-dir TinyLlama-1.1B-Chat-v1.0`.
     Qwen3-1.7B is expected at `./Qwen3-1.7B-int4-ov`
     (for example `hf download OpenVINO/Qwen3-1.7B-int4-ov --local-dir Qwen3-1.7B-int4-ov`).
   - **Cloud:** the same `.env` keys as Lab 01: `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT`.

4. Lab 21's cloud skills (`ask_cloud_model`, `image2mermaid`) use the same Lab 01 `.env` keys. The other
   Lab 21 skills need no keys.

Lab 19 needs no model and no network.

---

## Skills vs tools

| | MCP tools (Labs 13–18) | Skills (Labs 19–20) |
| --- | --- | --- |
| Interface | Name, description, JSON schema | A Python class with triggers and `execute()` |
| State | Each call stands alone in these labs | Shared `SkillContext` that every skill can read and write |
| Chaining | The caller passes results by hand | A skill reads what an earlier skill stored |
| Selection | The model reads the descriptions | Lab 19: trigger words and a score. Lab 20: an LLM |
| Prerequisites | Not part of the spec | `skill.prerequisites`, checked by the orchestrator |
| Standard | Yes (MCP specification) | No, a design pattern |
| Good for | Tools shared across apps and clients | Internal logic of one agent |

The MCP spec allows servers to keep state; the "stands alone" row describes the servers in these labs.
Real agents often use both: MCP for outside tools, skills for memory and reasoning inside the agent.

---

## Lab 19: the Skills pattern

### The pieces

```python
@dataclass
class SkillContext:
    user_input: str = ""
    previous_results: List[Dict] = field(default_factory=list)   # history of skill outputs
    variables: Dict[str, Any] = field(default_factory=dict)       # shared state between skills
    conversation_history: List[Dict] = field(default_factory=list)

    def set_variable(self, name, value): self.variables[name] = value
    def get_variable(self, name, default=None): return self.variables.get(name, default)
```

Each skill subclasses `Skill` and implements `can_execute()` and `execute()`; `post_process()` is optional.

```python
class MyCustomSkill(Skill):
    def __init__(self):
        super().__init__(name="my_skill", description="What my skill does", category=SkillCategory.UTILITY)
        self.triggers = ["keyword1", "keyword2"]
        self.prerequisites = []            # e.g. ["text_analysis"]: must have run earlier

    def can_execute(self, context):
        return any(t in context.user_input.lower() for t in self.triggers)

    def execute(self, context, **kwargs):
        result = do_something()
        context.set_variable("my_result", result)   # other skills can now read it
        return {"data": result}
```

The `SkillOrchestrator` runs one request like this:

1. Store the input in the context.
2. Ask every skill `can_execute()`. Among those that say yes, pick the highest `get_confidence()`.
3. Check prerequisites. Run `execute()`, then `post_process()`.
4. Add the result to `previous_results`.

Confidence is `min(matches / number_of_triggers * 2, 1.0)`, where `matches` counts trigger words found in the
input. A skill with many triggers gets a lower score per match, so the score is a ranking, not a probability.

### The five skills

| Skill | Triggers (substring match) | Stores in context |
| --- | --- | --- |
| `weather` | weather, temperature, forecast, rain, sunny, cold, hot, climate | `current_weather`, `current_location` |
| `calculator` | calculate, compute, math, sum, multiply, divide, add, subtract, what is, + - * / | `last_calculation` |
| `text_analysis` | analyze, sentiment, keywords, summarize, summary, count words, statistics | `text_analysis_result` |
| `memory` | remember, recall, forget, what did, store, save, note | `st.session_state.agent_memory` (not the context) |
| `recommendation` | recommend, suggest, what should, advice, best | reads all of the above |

Weather is simulated: temperature (10–35 °C) and condition are random. The recommendation rules are:
rain in the condition -> umbrella; above 25 °C -> sunscreen and water; below 10 °C -> dress warmly;
negative text -> "consider a more positive tone"; positive text -> "great positive tone";
last calculation above 1000 -> "double-check". With no matching context it suggests what to try first.

UI: sidebar checkboxes **Show Available Skills**, **Show Context State**, **Show MCP Comparison**, six example
buttons, and **🔄 Reset Context**. Type in the message box and press **🚀 Execute**. The **📦 Context State**
panel lists the stored variables and the last three skills that ran.

### Demo script (20 minutes)

The skills and scores below were checked against the Lab 19 code.

**1. Single skills.**

| Query | Skill | Score |
| --- | --- | --- |
| What's the weather in London? | weather | 0.25 |
| Calculate 25 * 4 | calculator (100) | 0.31 |
| Analyze this text for sentiment: I love learning AI! | text_analysis (positive) | 0.57 |

After each one, point at the **📦 Context State** panel: the variables are what makes chaining possible.

**2. Chaining.**

1. `What's the weather in Paris?` stores `current_weather` and `current_location`.
2. `What do you recommend?` The recommendation skill never asked for the weather; it read it from the context.
   Because the weather is random, you may get an umbrella, sunscreen or "dress warmly" line, or none.
3. `Analyze this text for sentiment: This product is terrible and disappointing!`
4. `Any recommendations?` now includes "The text seems negative. Consider a more positive tone?"

The newest result for each variable wins: after step 3 the earlier positive analysis is replaced.

**3. Memory.**

1. `Remember that my name is Alex`
2. `Remember that I'm planning a trip to Tokyo`
3. `Recall my memories` (or `What did I tell you?`) lists both with timestamps.

The sidebar example "What do you remember?" works too: the skill checks recall phrases before "remember"
(an earlier version treated it as a store request).
Memory lives in Streamlit session state, so **🔄 Reset Context** does not clear it; `Forget everything` does.

**4. Where keyword routing breaks.**

| Query | Result | Why |
| --- | --- | --- |
| is it cold outside? | weather, location New York | "cold" is a trigger; New York is the default city |
| what's happening in london? | no skill | no trigger word |
| What is 50? | calculator, error | "what is" is a trigger, but there is no expression |
| Analyze 100 + 50 | text_analysis (0.29 beats calculator 0.15) | calculator has 13 triggers, so one match scores low |
| Calculate how much 7 days of vacation costs at $150 per day | calculator, error | words, not an expression |

**5. Full chain.** `What's the weather in Miami?`, then `Calculate 7 * 150` (1050),
`Analyze: I love my beach vacation, it is great!`, then `What do you recommend?`. The answer uses the weather,
the large-number rule and the positive tone. Sentiment uses a short word list
(love, great, amazing, wonderful, ...); "excited" is not on it, so "I'm so excited" counts as neutral.

Exercises: write a `TranslateSkill` and chain it after `TextAnalysisSkill`; give `RecommendationSkill`
a prerequisite and watch the orchestrator refuse it until the other skill has run.

---

## Lab 20: Skills + LangGraph + an LLM router

Lab 20 keeps the five skills and replaces keyword selection with an LLM inside a LangGraph graph.

```text
analyze_intent (LLM) --> select_skill (LLM) --+-- no skill --> generate_response (LLM) --> END
                                              |
                                              v
                                  execute_skill --> validate_result --(error, up to 2 retries)--> execute_skill
                                              ^           |
                                              |           v
                                              +-- chain -- decide_chain (LLM) -- finish --> generate_response
```

| Node | LLM call? | What it does |
| --- | --- | --- |
| `analyze_intent` | yes | Short analysis of the request, given the skill list |
| `select_skill` | yes | Answer one skill name. If the reply names no skill, fall back to Lab 19's trigger score |
| `execute_skill` | no | Runs the skill on the shared `SkillContext` |
| `validate_result` | no | On an exception, retry the skill (up to 2 times) |
| `decide_chain` | yes | "Should we use another skill?" Up to 2 extra skills per request, each run once |
| `generate_response` | yes | Turns the skill result into a short reply |

So one request costs at least four LLM calls. Measured on 2026-11-23 (`README_Workshop_Demo.md`):
about 2.6 s per request with Qwen3 and 2.4 s with the Foundry deployment. Tick **Show Workflow** to see the node trace under
**🔗 LangGraph Execution Trace**.

### Choosing the brain

Sidebar **Select Model**, then **🚀 Initialize Agent**:

| Option | Model path or keys | Notes |
| --- | --- | --- |
| Qwen3 1.7B (Local, recommended) | `./Qwen3-1.7B-int4-ov` | `/no_think` is appended so it answers without a `<think>` section |
| TinyLlama 1.1B (Local) | `./TinyLlama-1.1B-Chat-v1.0/` | Lab 03 model; weaker at following the "one word" instruction |
| Microsoft Foundry deployment (Cloud, Lab 01) | Lab 01 `.env` keys | Responses API on the v1 endpoint, `reasoning={"effort": "low"}`; model = `AZURE_OPENAI_DEPLOYMENT` |
| Simulation Mode | none | Canned replies, no LLM |

The **Device** radio (CPU/GPU) applies to the local models. If a local model folder is missing, the app falls
back to simulation mode and shows a warning. The cloud option uses whatever `AZURE_OPENAI_DEPLOYMENT` names.

In **Simulation Mode** the selector is keyword-based: `_simulate_llm_response` extracts the `User request: "…"`
line from the prompt and matches only that (the prompt also lists every skill name, so matching the whole prompt
would always find "weather"). Good for a dry run; use a real brain to see actual LLM routing.

### What to compare with Lab 19

- `Calculate how much 7 days at $150 per day cost` fails in Lab 19. Does the LLM pick `calculator`, and does the
  skill still fail because it extracts digits with a regex? (The LLM selects; the skill still parses.)
- Ask an indirect question, such as "Should I take an umbrella in London?". Watch `select_skill` and `decide_chain`.
- Compare TinyLlama, Qwen3 and the cloud brain on the same five queries: right skill? how long?

---

## Lab 21: skills that call real tools

Lab 21 routes requests to five skills. Three run locally and two call your cloud model through `cloud_model.py`
(your Microsoft Foundry deployment, the Lab 01 `.env` keys):

| Skill | Runs on | Example |
| --- | --- | --- |
| `image2mermaid` | cloud model (vision) | upload a diagram in the sidebar and press **🔄 Convert to Mermaid** |
| `ask_cloud_model` | cloud model | `What is MLD in WiFi 7?`, `Explain LE Audio in Bluetooth` |
| `calculator` | local | `calculate (3 + 4) * 6` -> 42 |
| `text_analyzer` | local | `Analyze sentiment: This product is amazing!` |
| `web_search` | internet | `What is the capital of France?` |

Type a request and press **🚀 Execute**, or **🔍 Analyze Only** to see the routing without running it.
Wi-Fi, Bluetooth, MLD and LE Audio questions go to `ask_cloud_model`; general "what is" questions go to
`web_search`. Measured on 2026-11-23 on the instructor laptop with deployment `gpt-5.4`, `ask_cloud_model`
answered "What is MLD in Wi-Fi 7?" in 4.4 s, and `image_to_mermaid` turned a 3-box flowchart image into
`flowchart LR  Camera --> VLM --> Decision` in 2.7 s. These are the same helpers as the Lab 14 MCP tools.

---

## Lab 22: Agent Skills (`SKILL.md`)

Labs 19–21 build skills as Python classes inside your own agent. Lab 22 shows the open **Agent Skills** format:
a folder with a `SKILL.md` file (YAML front matter with `name` and `description`, then Markdown instructions)
plus optional scripts. Claude Code, GitHub Copilot in VS Code and other agents load these on demand.

```text
Agents_lab22_agent_skills/openvino-course-labs/
├── SKILL.md
└── scripts/
    └── check_setup.py
```

The agent reads only each skill's name and description at start-up. When a request matches the description,
it loads the full `SKILL.md`, and runs the bundled script only if needed. This keeps many skills from filling the
context window. To install, copy the `openvino-course-labs` folder to `.claude/skills/` (Claude Code) or
`.github/skills/` (Copilot in VS Code), then ask "Is my laptop ready for Lab 16?".

| | Python Skills pattern (19–21) | Agent Skills (22) |
| --- | --- | --- |
| What it is | A class in your agent's code | A folder of instructions and scripts |
| Who uses it | Your own agent | Any compatible agent |
| Selected by | Triggers, score or an LLM router | The agent, by matching the `description` |
| State | Shared `SkillContext` | The agent's conversation |
| Good for | Logic inside an app you build | Reusable know-how for coding agents |

Details and the exercise are in `Agents_lab22_agent_skills/README.md`.

---

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Context panel is empty | Run a skill first; the context starts empty. |
| Recommendations ignore the weather | The random weather may not hit a rule (rain, >25 °C, <10 °C). Ask again. |
| Lab 20 "simulation mode" warning | The local model folder is missing from the repo root. |
| Lab 20 cloud brain or Lab 21 `ask_cloud_model` / `image2mermaid` errors | Check the Lab 01 `.env` keys; behind a proxy add `.openai.azure.com` to `NO_PROXY` ([details](../README_Reproduce_Demo.md#proxy-set-check-unset)). |
| Port already in use | Add `--server.port 8502`. |

Further reading: [LangGraph](https://langchain-ai.github.io/langgraph/) · [ReAct pattern](https://arxiv.org/abs/2210.03629) ·
[agentskills.io](https://agentskills.io). Previous: `README_MCP.md`. Next: `README_Multimodal.md` (Lab 23).
