# Reproduce and demo every lab (PAGA-2 hands-on, deck v6)

How to reproduce, or demo live, every lab in part 1 of `PAGA-2_HandsOn_v6.pptx` (slides 1–14), in slide order.

- **Students:** use [Reproduce every lab](#reproduce-every-lab). It is one table with a command and the expected result for each lab.
- **Instructor:** use the [live demo run sheet](#live-demo-run-sheet). For each lab it gives what to show, the talking points and how long it takes.

The agent labs (slides 15+) are in [OPENVINO-GENAI-SAMPLES](https://github.com/MTAGenAICourse/OPENVINO-GENAI-SAMPLES).

All timings were measured on a Windows 11 laptop with an Intel CPU, an integrated GPU and an NPU, using OpenVINO GenAI 2025.4.
Labs 03–10 were re-run from this repo on 2026-11-11. Your numbers will differ: record them in the homework table.

---

## Setup (once)

```bash
git clone https://github.com/MTAGenAICourse/GenAI_APIs_Cloud_Local.git
cd GenAI_APIs_Cloud_Local
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env          # Labs 01-02 only: fill in your keys. Never commit .env
```

Download the models. They are already converted to OpenVINO format, so you don't need PyTorch. The total is about 7 GB.

```bash
hf download OpenVINO/TinyLlama-1.1B-Chat-v1.0-int4-ov --local-dir TinyLlama-1.1B-Chat-v1.0
hf download OpenVINO/Phi-3.5-vision-instruct-int4-ov  --local-dir Phi-3.5-vision-instruct-int4-ov
hf download OpenVINO/whisper-base-fp16-ov             --local-dir whisper-base
hf download OpenVINO/stable-diffusion-v1-5-int8-ov    --local-dir stable-diffusion-v1-5-int8-ov
```

> **Already have the models in a clone of OPENVINO-GENAI-SAMPLES?** You can link them instead of downloading them again
> (Command Prompt, run inside `GenAI_APIs_Cloud_Local`):
>
> ```cmd
> for %m in (TinyLlama-1.1B-Chat-v1.0 Phi-3.5-vision-instruct-int4-ov whisper-base stable-diffusion-v1-5-int8-ov) do mklink /J %m ..\OPENVINO-GENAI-SAMPLES\%m
> ```
>
> Every lab also accepts a model path (`--model` or the first argument), so you can point it at the existing folder instead.

> If you want to export models yourself with `optimum-cli`, do it in a **separate** venv (`pip install "optimum-intel[openvino]"`).
> On 2026-11-09, exporting Whisper failed with `NormalizedConfig ... allow_new`, but the downloads above worked.

---

## Reproduce every lab

| Lab | Slide | Command | Expected | Measured |
| --- | --- | --- | --- | --- |
| 01 | 14 | `python GenAI_APIs_lab01_gpt_sol.py --effort low` | short RAG explanation, plus timing and token counts | low 3.8 s · high 4.5 s (needs Azure keys) |
| 02 | 15 | `python GenAI_APIs_lab02_claude_opus.py --effort low` | same task on Claude Opus 5.5 | ≈ 6–10 s (needs `ANTHROPIC_API_KEY`) |
| 03 | 18 | `python GenAI_APIs_lab03_text_to_text.py ./TinyLlama-1.1B-Chat-v1.0/ "Sun is yellow because" --device CPU` | streamed answer, then tokens/s | CPU 33–55 tok/s · GPU 51–57 tok/s |
| 04 | 19 | `python GenAI_APIs_lab04_vision_basics.py Data/Robot.jpg "What is the robot doing?"` | "The robot is holding a cup of coffee." | CPU 14 s · GPU 2.5 s |
| 05 | 19 | `streamlit run GenAI_APIs_lab05_camera_to_text.py` | webcam Q&A app | — |
| 06 | 19 | `python GenAI_APIs_lab06_video_analyzer_cli.py --source Data/all_animals.mp4 --interval 2` | per-frame descriptions: lion, elephant, zebra | GPU ≈ 3–5 s per frame |
| 07 | 20 | `python GenAI_APIs_lab07_speech_basics.py --record 5` (or `--wav file.wav`, 16 kHz mono) | your sentence as text | 0.4 s for 5 s of audio (CPU) |
| 08 | 20 | `streamlit run GenAI_APIs_lab08_microphone_to_text.py` | live transcription app | — |
| 09 | 20 | `python GenAI_APIs_lab09_image_gen.py ./stable-diffusion-v1-5-int8-ov "starry night over Jaffa port"` | `image.bmp`, 512×512 | ≈ 66 s on CPU |
| 10 | 20 | `streamlit run GenAI_APIs_lab10_image_generation_app.py` | image studio app; finds `./stable-diffusion-v1-5-int8-ov` automatically | — |

Slide numbers are the page numbers printed in the slide footers.

---

## Live demo run sheet

### Before class (15 minutes)

1. **Make sure Azure OpenAI bypasses the corporate proxy.** A Foundry resource with public access disabled only accepts traffic
   from its private network. If requests go through the corporate proxy (`HTTPS_PROXY`), Lab 01 fails with
   `403 Public access is disabled`. Add `.openai.azure.com` to `NO_PROXY` yourself. The labs never change proxy settings.

   Permanent, for new terminals (run once):

   ```cmd
   setx NO_PROXY "%NO_PROXY%,.openai.azure.com"
   ```

   For a terminal that is already open:

   | Shell | Command |
   | --- | --- |
   | PowerShell | `$env:NO_PROXY = "$env:NO_PROXY,.openai.azure.com"` |
   | Command Prompt | `set NO_PROXY=%NO_PROXY%,.openai.azure.com` |
   | Git Bash | `export NO_PROXY="$NO_PROXY,.openai.azure.com" no_proxy="$no_proxy,.openai.azure.com"` |

   To check (PowerShell): `$env:NO_PROXY -split ',' | Select-String openai` should print `.openai.azure.com`.
   Putting `NO_PROXY` in `.env` doesn't work, because `load_dotenv()` doesn't override a value already set in the shell.
   `setx` cuts values off at 1024 characters; if your list is longer, edit it in Windows Settings → Environment variables.
   Students on their own Azure for Students resources don't need this, because those resources allow public access.

2. **Open a new terminal** after running `setx`. Terminals that were already open keep the old `NO_PROXY`.
3. **Activate the environment** and confirm the devices:

   ```bash
   cd GenAI_APIs_Cloud_Local
   .venv\Scripts\activate
   python -c "import openvino as ov; print(ov.Core().available_devices)"
   ```

   Expected on the instructor laptop: `['CPU', 'GPU.0', 'GPU.1', 'NPU']`
4. **Check the cloud keys** (no values are printed):

   ```bash
   python -c "from dotenv import dotenv_values as d; v=d('.env'); print({k: bool(v.get(k)) for k in ['AZURE_OPENAI_ENDPOINT','AZURE_OPENAI_API_KEY','AZURE_OPENAI_DEPLOYMENT','ANTHROPIC_API_KEY']})"
   ```

   All four should be `True`. `AZURE_OPENAI_DEPLOYMENT` must name a deployment that exists on your resource.
5. **Pre-generate the Lab 09 image.** It takes 1–2.5 minutes on CPU, too long to wait for live:

   ```bash
   python GenAI_APIs_lab09_image_gen.py ./stable-diffusion-v1-5-int8-ov "starry night over Jaffa port"
   ```

   Keep the resulting `image.bmp` open in a viewer.
6. **Warm up the vision model once**, so the first live run isn't slowed by GPU compilation:

   ```bash
   python GenAI_APIs_lab04_vision_basics.py Data/Robot.jpg "What is the robot doing?" --device GPU
   ```

### Part 1: Cloud models (slides 14–15)

#### Lab 01: GPT on Microsoft Foundry (slide 14)

```bash
python GenAI_APIs_lab01_gpt_sol.py --effort low
python GenAI_APIs_lab01_gpt_sol.py --effort high
```

- **Show:** the same answer at both efforts, then the token line at the bottom.
- **Expect:** a two-sentence RAG explanation. low: 3.8 s, 66 output tokens · high: 4.5 s, 117 output tokens.
- **Talking point:** effort changes the tokens you pay for more than the answer itself.
- **Talking point:** there's no `temperature` here. Reasoning models are steered with effort and instructions.
  See [Temperature: cloud vs local](#temperature-cloud-vs-local).

#### Lab 02: Claude Opus 5.5 (slide 15)

```bash
python GenAI_APIs_lab02_claude_opus.py --effort low
python GenAI_APIs_lab02_claude_opus.py --effort high
```

- **Expect:** a note that server-side fallback isn't enabled for this workspace, then the answer.
  low: 6–10 s · high: about 12 s. The output token count includes Opus's thinking tokens.
- **Talking point:** compare latency, cost ($2/$10 vs $4/$20 per 1M tokens) and writing style with Lab 01.

### Part 2: Local models with OpenVINO (slides 18–20)

#### Lab 03: Local LLM, CPU vs GPU (slide 18)

```bash
python GenAI_APIs_lab03_text_to_text.py ./TinyLlama-1.1B-Chat-v1.0/ "Sun is yellow because" --device CPU
python GenAI_APIs_lab03_text_to_text.py ./TinyLlama-1.1B-Chat-v1.0/ "Sun is yellow because" --device GPU
```

- **Show:** the tokens streaming in, then the `tokens/s` line.
- **Expect:** CPU about 33–55 tokens/s, GPU about 51–57 tokens/s.
- **Talking point:** the answer is fluent but scientifically wrong. Ask the class to compare it with Labs 01–02.

#### Temperature: cloud vs local

Temperature controls how random the next-token choice is. Low values give safe, predictable text;
high values give more varied and more creative text, and eventually nonsense.
**Reasoning models don't expose it, but local models do**, which makes a good contrast between Labs 01–02 and Lab 03.

Tested on 2026-11-09:

| Model | `temperature` | What happens |
| --- | --- | --- |
| Claude Opus 5.5 (Lab 02) | Not available | The current `anthropic` SDK (2.6) no longer has the parameter: `TypeError: unexpected keyword argument 'temperature'`. Steer with `output_config={"effort": ...}` and the prompt. |
| GPT on Foundry (Lab 01) | Only with reasoning off | Accepted with `reasoning={"effort": "none"}`; with `low` or `high` the API returns `400 Unsupported parameter: 'temperature'`. |
| TinyLlama on OpenVINO (Lab 03) | Fully supported | Set `do_sample=True` together with `temperature` (and optionally `top_p`/`top_k`). Without `do_sample=True`, temperature has no effect. |

**Live demo (local, about 30 s on CPU).** Paste into a Python prompt, or save as `temperature_demo.py`:

```python
import openvino_genai as ov_genai

pipe = ov_genai.LLMPipeline("./TinyLlama-1.1B-Chat-v1.0", "CPU")
prompt = "Write a one-line slogan for a coffee shop."

for label, temp in [("greedy", None), ("temperature 0.2", 0.2), ("temperature 1.3", 1.3)]:
    cfg = ov_genai.GenerationConfig()
    cfg.max_new_tokens = 30
    if temp is not None:
        cfg.do_sample = True          # required, or temperature is ignored
        cfg.temperature = temp
        cfg.top_p = 0.95
    for run in range(3):
        print(f"{label:16} run {run + 1}: {pipe.generate(prompt, cfg).strip()}")
```

What we saw on CPU:

| Setting | 3 runs |
| --- | --- |
| greedy (default) | identical every time: "Where coffee meets art" |
| temperature 0.2 | different but tame: "Caffeinated Comfort", "Caffeinated Escape" |
| temperature 1.3 | creative to nonsensical: "Nibble it niri, satisfy it hastach!" |

- **Talking point:** for reproducible output, use greedy decoding (the default) **on CPU**. On GPU, greedy output
  varied slightly between runs, and setting `rng_seed` did not make repeated sampled runs identical in our test.
- **Talking point:** small models spread probability more evenly, so even temperature 0.2 varies. Larger models
  are more stable at low temperature.

#### Labs 04–06: Vision-language model (slide 19)

```bash
python GenAI_APIs_lab04_vision_basics.py Data/Robot.jpg "What is the robot doing?" --device GPU
python GenAI_APIs_lab06_video_analyzer_cli.py --source Data/all_animals.mp4 --interval 2 --device GPU
```

- **Expect (Lab 04):** "The robot is holding a cup of coffee." in about 2.5 s on GPU (14 s on CPU).
- **Expect (Lab 06):** one description per sampled frame, naming a lion, elephant and zebra, at about 3–5 s per frame on GPU.
- **Talking point:** point to the `stop_token_ids = {32007}` line on the slide. Without it the model keeps writing after its answer.
- **Lab 05 (optional):** `streamlit run GenAI_APIs_lab05_camera_to_text.py` for a live webcam demo.
  Set the model path in the sidebar and click load before taking a photo.

#### Labs 07–10: Speech and images (slide 20)

```bash
python GenAI_APIs_lab07_speech_basics.py --record 5
```

- **Show:** say a sentence, e.g. "Starry night over Jaffa port, in a dreamy anime style."
- **Expect:** the transcript in about 0.4 s on CPU. Stay on CPU here: on GPU, Whisper first spends about 15 s compiling.
- **Talking point:** Whisper-base makes small mistakes (earlier test: "Story Knight over Jeffa Port"). Bigger models fix that.
  Fed silence or a tone instead of speech, it may repeat an invented phrase; that's normal for Whisper.
- **Lab 08 (optional):** `streamlit run GenAI_APIs_lab08_microphone_to_text.py` for continuous transcription.
- **Lab 09:** show the pre-generated `image.bmp` and explain the generation command. Don't run it live.
- **Lab 10 (optional):** `streamlit run GenAI_APIs_lab10_image_generation_app.py` for the guided prompt builder.
  On CPU, use few inference steps (≈ 20) so a generation finishes during class.

---

## If something goes wrong

| Symptom | Fix |
| --- | --- |
| Lab 01: `403 Public access is disabled` | The terminal is still using the corporate proxy. Open a **new** terminal (`NO_PROXY` must contain `.openai.azure.com`). See [Before class](#before-class-15-minutes). |
| Lab 01: `404 DeploymentNotFound` | `AZURE_OPENAI_DEPLOYMENT` must name a deployment that exists on the resource. |
| Lab 02: `server_side_fallback not supported` | Expected on some workspaces. The script retries automatically without fallback. |
| First GPU run takes 15+ s | GPU compilation on first load. Warm the model up before class, or use CPU. |
| Vision answer rambles past the question | The model is missing `stop_token_ids = {32007}`. All samples in this repo set it. |
| Lab 10: "No image generation models found" | Download `stable-diffusion-v1-5-int8-ov` into the repo folder (see [Setup](#setup-once)). |
| Port already in use (Streamlit) | Add `--server.port 8502`, or close the previous app. |
