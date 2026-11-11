# GenAI_APIs_Cloud_Local

Hands-on labs for **Practical Applications of Generative AI** (The Academic College of Tel Aviv–Jaffa, 2026–2027), part 1 of the PAGA-2 session:
call state-of-the-art models **in the cloud** (GPT-6.1 Sol, Claude Opus 5.5), then run open models **locally** with OpenVINO GenAI (text, vision, speech, images).

The agent labs (LangGraph, MCP, Skills) are in [OPENVINO-GENAI-SAMPLES](https://github.com/MTAGenAICourse/OPENVINO-GENAI-SAMPLES).

## Labs

Run them in order. Each lab builds on the one before it.

| Lab | File | What you learn | Run |
| --- | --- | --- | --- |
| 01 | `GenAI_APIs_lab01_gpt_sol.py` | Cloud: GPT-6.1 Sol on Microsoft Foundry, Responses API, reasoning effort | `python GenAI_APIs_lab01_gpt_sol.py --effort low` |
| 02 | `GenAI_APIs_lab02_claude_opus.py` | Cloud: Claude Opus 5.5, Messages API — compare with Lab 01 | `python GenAI_APIs_lab02_claude_opus.py --effort low` |
| 03 | `GenAI_APIs_lab03_text_to_text.py` | Local LLM with `LLMPipeline`, token streaming | `python GenAI_APIs_lab03_text_to_text.py ./TinyLlama-1.1B-Chat-v1.0/ "Sun is yellow because"` |
| 04 | `GenAI_APIs_lab04_vision_basics.py` | Image Q&A with a vision-language model (`VLMPipeline`) | `python GenAI_APIs_lab04_vision_basics.py Data/Robot.jpg "What is the robot doing?"` |
| 05 | `GenAI_APIs_lab05_camera_to_text.py` | Webcam photo → questions (Streamlit app) | `streamlit run GenAI_APIs_lab05_camera_to_text.py` |
| 06 | `GenAI_APIs_lab06_video_analyzer_cli.py` | Describe a video / webcam every N seconds | `python GenAI_APIs_lab06_video_analyzer_cli.py --source Data/all_animals.mp4 --interval 2` |
| 07 | `GenAI_APIs_lab07_speech_basics.py` | Speech → text with Whisper (`WhisperPipeline`) | `python GenAI_APIs_lab07_speech_basics.py --record 5` |
| 08 | `GenAI_APIs_lab08_microphone_to_text.py` | Live microphone transcription (Streamlit app) | `streamlit run GenAI_APIs_lab08_microphone_to_text.py` |
| 09 | `GenAI_APIs_lab09_image_gen.py` | Text → image with Stable Diffusion (`Text2ImagePipeline`) | `python GenAI_APIs_lab09_image_gen.py ./stable-diffusion-v1-5-int8-ov "starry night over Jaffa port"` |
| 10 | `GenAI_APIs_lab10_image_generation_app.py` | Image studio: guided prompts, styles, gallery (Streamlit app) | `streamlit run GenAI_APIs_lab10_image_generation_app.py` |

`image_generation_service.py` and `text_sanitization_utilities.py` are helper modules used by Lab 10.

## Setup

```bash
git clone https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local.git
cd GenAI_APIs_Cloud_Local
python -m venv .venv && .venv\Scripts\activate      # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

### Cloud labs (01–02)

1. Activate **Azure for Students** (free credit, no credit card).
2. Create a **Microsoft Foundry** resource and deploy `gpt-6.1-sol`. Note the deployment name.
3. Get a Claude API key at [console.anthropic.com](https://console.anthropic.com) (optional — or deploy Claude in Foundry).
4. `copy .env.example .env` and fill in your values. **Never commit `.env`.**

### Local labs (03–10)

No keys needed. Download the pre-converted OpenVINO models once (≈ 7 GB total, no PyTorch required):

```bash
hf download OpenVINO/TinyLlama-1.1B-Chat-v1.0-int4-ov --local-dir TinyLlama-1.1B-Chat-v1.0
hf download OpenVINO/Phi-3.5-vision-instruct-int4-ov  --local-dir Phi-3.5-vision-instruct-int4-ov
hf download OpenVINO/whisper-base-fp16-ov             --local-dir whisper-base
hf download OpenVINO/stable-diffusion-v1-5-int8-ov    --local-dir stable-diffusion-v1-5-int8-ov
```

| Lab | Model |
| --- | --- |
| 03 | TinyLlama-1.1B-Chat-v1.0 |
| 04, 05, 06 | Phi-3.5-vision-instruct-int4-ov |
| 07, 08 | whisper-base |
| 09, 10 | stable-diffusion-v1-5-int8-ov |

## Tips

- **No proxy setup needed.** The labs never read or change proxy variables. On a home network nothing is required;
  behind a corporate proxy, keep your existing `HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY` as they are — the labs were tested that way.
- **Device.** Start on `CPU`, then try `GPU` (or `NPU`) and compare speed. The vision model is about 3× faster on an integrated GPU.
  Small models such as Whisper-base spend ~15 s compiling for the GPU, so the CPU wins there.
- **Phi-3.5-vision stop token.** The samples set `stop_token_ids = {32007}` so the model stops at `<|end|>`; without it the model rambles.
- **Reasoning models (Labs 01–02) reject `temperature` / `top_p`.** Steer them with instructions and `effort` instead.
- **Measured on a Windows 11 laptop (Intel CPU + iGPU), OpenVINO GenAI 2025.4:** Lab 03 CPU ≈ 33–55 tok/s · Lab 04 GPU ≈ 2.5 s ·
  Lab 06 GPU ≈ 5 s per frame · Lab 09 CPU ≈ 66 s per 512×512 image. Your numbers will differ — record them for the homework.

## Homework

1. Run Labs 01 + 02 with the same prompt. Compare latency, cost and style.
2. Run Labs 03–10 on your laptop. Record tokens/sec (or seconds per image) on CPU vs GPU in a short table.
3. Voice-to-image: speak a prompt, transcribe it with Lab 07, render it with Lab 09.
