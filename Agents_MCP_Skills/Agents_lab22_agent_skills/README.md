# Lab 22 - Agent Skills: package know-how for any coding agent

Labs 19-21 build **Skills as Python classes** inside your own agent (triggers, `SkillContext`, chaining).
This lab shows the other meaning of "skill" you will meet in industry: **Agent Skills**, an open format
(a folder with a `SKILL.md` file) that Claude Code, GitHub Copilot in VS Code and other agents load on demand.

```text
openvino-course-labs/
├── SKILL.md              # YAML front matter (name, description) + instructions in Markdown
└── scripts/
    └── check_setup.py    # code the agent can run instead of re-deriving it
```

How it works:

1. At start-up the agent reads only each skill's `name` and `description` (a few dozen tokens per skill).
2. When a request matches the description ("why does Lab 04 fail?"), the agent loads the full `SKILL.md`.
3. The instructions point to bundled scripts and files, which the agent reads or runs only when needed.

This *progressive disclosure* lets an agent carry many skills without filling its context window.

## Try it

Run the script yourself first (from the repo root):

```bash
python Agents_MCP_Skills/Agents_lab22_agent_skills/openvino-course-labs/scripts/check_setup.py
```

Then install the skill for your coding agent by copying the `openvino-course-labs` folder:

| Agent | Copy the folder to |
| --- | --- |
| Claude Code | `.claude/skills/` in the repo (or `~/.claude/skills/` for every project) |
| GitHub Copilot in VS Code | `.github/skills/` in the repo |

Ask the agent: *"Is my laptop ready for Lab 16?"* or *"Lab 04 rambles after its answer, why?"*
and watch it load the skill, run `check_setup.py` and answer from the instructions.

## Python Skills (Labs 19-21) vs Agent Skills (Lab 22)

| | Python Skills pattern | Agent Skills (`SKILL.md`) |
| --- | --- | --- |
| What it is | A class in your agent's code | A folder of instructions + scripts |
| Who uses it | Your own agent (Labs 19-21) | Any compatible agent (Claude Code, Copilot, ...) |
| Selected by | Triggers / confidence score / LLM router | The agent, by matching the `description` |
| State | Shared `SkillContext` | The agent's conversation |
| Best for | Internal logic of an app you build | Reusable know-how for coding agents |

## Exercise

Write a second skill, `lab-report-writer`, that turns a lab's console output into the homework table
(device, model, time, tokens/s). Keep the `description` specific: it decides when the skill loads.

Specification and more examples: [agentskills.io](https://agentskills.io) ·
[VS Code Agent Skills](https://code.visualstudio.com/docs/copilot/customization/agent-skills).
