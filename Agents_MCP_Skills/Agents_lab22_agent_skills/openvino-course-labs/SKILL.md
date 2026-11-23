---
name: openvino-course-labs
description: Run, check and troubleshoot the GenAI_APIs_Cloud_Local course labs (Labs 01-23 - cloud GPT/Claude, local OpenVINO text/vision/speech/image, agents, MCP and Skills). Use when a student asks how to run a lab, why a lab fails, which model a lab needs, or whether their laptop is set up.
---

# OpenVINO course labs

The repo has two parts. Every command runs from the **repo root**.

| Labs | Folder | What |
| --- | --- | --- |
| 01-02 | repo root | Cloud models: GPT on Microsoft Foundry (01), Claude Opus 5.5 (02) |
| 03-10 | repo root | Local OpenVINO GenAI: text, vision, speech, image |
| 11-23 | `Agents_MCP_Skills/` | LangGraph agents, MCP servers and clients, Skills |

## First step: check the setup

Run the bundled script and act on every `MISSING` or `WARN` line before anything else:

```bash
python Agents_MCP_Skills/Agents_lab22_agent_skills/openvino-course-labs/scripts/check_setup.py
```

## Which model each lab needs

| Model folder (repo root) | Labs | Download |
| --- | --- | --- |
| `TinyLlama-1.1B-Chat-v1.0` | 03 | `hf download OpenVINO/TinyLlama-1.1B-Chat-v1.0-int4-ov --local-dir TinyLlama-1.1B-Chat-v1.0` |
| `Phi-3.5-vision-instruct-int4-ov` | 04-06, 11, 12, 16, 23 | `hf download OpenVINO/Phi-3.5-vision-instruct-int4-ov --local-dir Phi-3.5-vision-instruct-int4-ov` |
| `whisper-base` | 07, 08, 16 | `hf download OpenVINO/whisper-base-fp16-ov --local-dir whisper-base` |
| `stable-diffusion-v1-5-int8-ov` | 09, 10, 16 | `hf download OpenVINO/stable-diffusion-v1-5-int8-ov --local-dir stable-diffusion-v1-5-int8-ov` |
| `Qwen3-1.7B-int4-ov` | 20 (local brain) | `hf download OpenVINO/Qwen3-1.7B-int4-ov --local-dir Qwen3-1.7B-int4-ov` |

Models stored somewhere else: set `LAB_MODELS_DIR` (Lab 16) or pass the path to the lab (`--model`, or the first argument for Labs 03 and 09).

## Known problems and fixes

- **Lab 01 or 17 returns `403 Public access is disabled`.** The request went through a corporate proxy to a private Foundry resource. The user adds `.openai.azure.com` to `NO_PROXY` and opens a new terminal. Never change the user's environment yourself - tell them the command.
- **Vision answer rambles past the question.** Phi-3.5-vision needs `stop_token_ids = {32007}`; every lab sets it.
- **First GPU run takes 15+ seconds.** That is model compilation. Warm up once, or use CPU for small models (Whisper).
- **`temperature` rejected (Labs 01, 02, 17, 18, 20).** Reasoning models are steered with effort, not temperature.
- **`ask_cloud_model` / `image2mermaid` fail (Labs 14, 15, 21).** They use the Foundry deployment: check the Lab 01 `.env` keys (and NO_PROXY behind a proxy).
- **Streamlit "port already in use".** Add `--server.port 8502`.

## When the user asks to run a lab

1. Look up the lab in `README.md` (Labs 01-10) or `Agents_MCP_Skills/README.md` (Labs 11-23) and use the exact command there.
2. Confirm the model folders above exist for that lab.
3. Run on CPU first; suggest `--device GPU` (or `LAB_DEVICE=GPU` for Lab 16) only after it works.
4. Report the result with its timing, and compare it with the expected output in `README_Reproduce_Demo.md` (Labs 01-10) or `Agents_MCP_Skills/README_Workshop_Demo.md` (Labs 11-23).
