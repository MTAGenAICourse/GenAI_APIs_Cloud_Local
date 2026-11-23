# Agents, MCP and Skills (Labs 11–23)

Part 2 of the course labs: turn the models from Part 1 into **agents** that plan, call tools and check the result.
You build the same ideas three ways — **LangGraph** workflows, **MCP** tools, and **Skills** — and finish with a
multimodal agent that combines them.

Part 1 (Labs 01–10: cloud APIs and local OpenVINO models) is in the [repo root](../README.md).
Slides: [PAGA-3_Agents_MCP_Skills.pptx](PAGA-3_Agents_MCP_Skills.pptx) (21 slides, in lab order).
Reproduce every lab, and the instructor's live demo run sheet: [README_Workshop_Demo.md](README_Workshop_Demo.md).

## Labs

**Run every command from the repo root** (the model folders and `Data/` live there).

| Lab | File | What you learn | Run |
| --- | --- | --- | --- |
| 11 | `Agents_lab11_visual_agent.py` | A visual-inspection agent as a plain Python loop | `streamlit run Agents_MCP_Skills/Agents_lab11_visual_agent.py` |
| 12 | `Agents_lab12_visual_agent_langgraph.py` | The same agent as a LangGraph state machine: typed state, conditional edges | `streamlit run Agents_MCP_Skills/Agents_lab12_visual_agent_langgraph.py` |
| 13 | `Agents_lab13_mcp_tutorial.py` | MCP concepts step by step: JSON-schema tools, routing, execution | `streamlit run Agents_MCP_Skills/Agents_lab13_mcp_tutorial.py` |
| 14 | `Agents_lab14_mcp_skills_server.py` | A real MCP server (low-level `Server` API, stdio) with 5 tools, two of them on your cloud model | started by Lab 15 |
| 15 | `Agents_lab15_mcp_skills_client.py` | An MCP client app: `tools/list`, `tools/call` | `streamlit run Agents_MCP_Skills/Agents_lab15_mcp_skills_client.py` |
| 16 | `Agents_lab16_mcp_openvino_server.py` | **New.** Local OpenVINO models as MCP tools (FastMCP): describe image, transcribe, generate image | started by Labs 17–18 · `--self-test` |
| 17 | `Agents_lab17_mcp_agent_gpt.py` | **New.** Cloud reasoning, local tools: GPT agent loop over the Lab 16 server | `python Agents_MCP_Skills/Agents_lab17_mcp_agent_gpt.py` |
| 18 | `Agents_lab18_mcp_agent_claude.py` | **New.** The same loop on Claude Opus 5.5 — compare the two APIs | `python Agents_MCP_Skills/Agents_lab18_mcp_agent_claude.py` |
| 19 | `Agents_lab19_skills_tutorial.py` | The Skills pattern: triggers, `SkillContext`, chaining | `streamlit run Agents_MCP_Skills/Agents_lab19_skills_tutorial.py` |
| 20 | `Agents_lab20_skills_langgraph.py` | Skills + LangGraph with a real LLM router (local Qwen3 or your Foundry deployment) | `streamlit run Agents_MCP_Skills/Agents_lab20_skills_langgraph.py` |
| 21 | `Agents_lab21_skills_demo.py` | A skills-routing demo app: local tools plus your cloud model | `streamlit run Agents_MCP_Skills/Agents_lab21_skills_demo.py` |
| 22 | `Agents_lab22_agent_skills/` | **New.** Agent Skills (`SKILL.md`), the open format Claude Code and Copilot load | see [its README](Agents_lab22_agent_skills/README.md) |
| 23 | `Agents_lab23_multimodal_agent.py` | Capstone: the multimodal agent | `streamlit run Agents_MCP_Skills/Agents_lab23_multimodal_agent.py` |

`cloud_model.py` is a helper module used by Labs 14, 15 and 21. It calls your Microsoft Foundry deployment
(Azure OpenAI v1 API, Responses API, reasoning effort `low`) with the same `.env` keys as Lab 01:
`ask_cloud_model(question)` answers a question, `image_to_mermaid(image_path, diagram_type)` turns a diagram
image into Mermaid code. Try it alone: `python Agents_MCP_Skills/cloud_model.py`.

Topic guides: [LangGraph](README_LangGraph.md) (11–12) · [MCP](README_MCP.md) (13–18) ·
[Skills](README_Skills.md) (19–22) · [Multimodal agent](README_Multimodal.md) (23).

## Setup

Do the Part 1 setup first ([README](../README.md#setup)), then:

```bash
pip install -r Agents_MCP_Skills/requirements.txt
hf download OpenVINO/Qwen3-1.7B-int4-ov --local-dir Qwen3-1.7B-int4-ov     # Lab 20 local brain
```

`requirements.txt` pins `mcp>=1.20,<2`: mcp 2.x renamed `FastMCP` and changed the low-level server API, so
Labs 14–18 break on 2.x.

| Lab | Needs |
| --- | --- |
| 11, 12, 23 | `Phi-3.5-vision-instruct-int4-ov` |
| 16 (and 17, 18) | `Phi-3.5-vision-instruct-int4-ov`, `whisper-base`, `stable-diffusion-v1-5-int8-ov` (each loaded on first use) |
| 17 | the Lab 01 `.env` keys (`AZURE_OPENAI_*`) |
| 14, 15, 21 | the Lab 01 `.env` keys for `ask_cloud_model` and `image2mermaid`; the other tools need nothing |
| 18 | `ANTHROPIC_API_KEY` (Lab 02) |
| 20 | `Qwen3-1.7B-int4-ov`, or the Lab 01 `.env` keys for the cloud brain |
| 13, 19 | nothing extra (simulated or built-in tools) |

Check everything at once: `python Agents_MCP_Skills/Agents_lab22_agent_skills/openvino-course-labs/scripts/check_setup.py`

## Three ways to give an agent abilities

| | LangGraph (11–12, 20) | MCP tools (13–18) | Skills (19–22) |
| --- | --- | --- | --- |
| What it is | A graph of steps with typed state | A standard protocol for tools | Packaged know-how: Python classes (19–21) or `SKILL.md` folders (22) |
| Who decides the next step | Your edges and conditions | The model, from tool schemas | Triggers / router (19–21), the agent (22) |
| State | Shared typed state | None — each call stands alone | `SkillContext` (19–21) |
| Best for | Multi-step workflows you control | Connecting any agent to external systems | Reusable logic and instructions |

Real agents combine them: LangGraph orchestrates, Skills hold the logic, MCP connects to the outside world.

## Tips

- **Cloud reasoning, local data.** In Labs 17–18 the image never leaves the laptop: the cloud model only sees
  the tool's short text answer. That is a cost and privacy decision you should be able to justify in your project.
- **Device.** Labs default to CPU; `LAB_DEVICE=GPU` for Lab 16, the sidebar device choice in the Streamlit labs.
- **Proxy.** Labs 14, 15, 17, 20 and 21 call your Foundry deployment. Against a private Foundry resource behind a
  corporate proxy they need `.openai.azure.com` in `NO_PROXY` — see [Proxy: set, check, unset](../README_Reproduce_Demo.md#proxy-set-check-unset).
- **mcp 2.x.** If Labs 14–18 fail on import (`FastMCP` or `mcp.server` not found), check `pip show mcp`: the labs
  need 1.x. Reinstall with `pip install "mcp>=1.20,<2"`.
