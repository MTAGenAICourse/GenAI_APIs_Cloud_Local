# Lab 23: The Multimodal Agent (Capstone)

One Streamlit app that runs the "analyze, understand, create" cycle on your laptop: the local Phi-3.5-vision
model inspects an image or video frames in several steps, checks its own answers, and writes a prompt you can
feed to Stable Diffusion. It ties together Part 1 (See, Create) and the agent patterns of Labs 11–22.

Run from the repo root (`GenAI_APIs_Cloud_Local`):

```bash
streamlit run Agents_MCP_Skills/Agents_lab23_multimodal_agent.py
```

---

## Setup

1. Finish the Part 1 setup in the repo root `README.md` (venv, `pip install -r requirements.txt`; it includes
   `opencv-python`). Lab 23 needs no extra packages.
2. Download the vision model into the repo root, as in Lab 04:

   ```bash
   hf download OpenVINO/Phi-3.5-vision-instruct-int4-ov --local-dir Phi-3.5-vision-instruct-int4-ov
   ```

3. Optional, to turn the generated prompt into an image: the Stable Diffusion model from Lab 09
   (`stable-diffusion-v1-5-int8-ov`).

Sample inputs are in `Data/`: `Robot.jpg` and `all_animals.mp4`. Bring a few of your own images too:
a landscape, a street scene, a portrait, a document with text, an artwork.

---

## Key ideas

### Vision-language model (VLM)

```text
image --> vision encoder --+
                           +--> language model --> text answer
text question -------------+
```

Phi-3.5-vision turns the image into tokens the language model can attend to, together with your question.
It runs locally with OpenVINO GenAI (`VLMPipeline`), INT4-quantized to fit in laptop memory.

### What makes it an agent

| Capability | In Lab 23 |
| --- | --- |
| Plan | A predefined list of analysis steps (the workflow) |
| Execute | One VLM call per step |
| Check | Each answer is tested for quality; weak answers are retried up to 2 times |
| Remember | Results and a step log are kept in the agent object |
| Act | The last step writes an image-generation prompt |

### Analyze, understand, create

```text
ANALYZE (what do I see?) --> UNDERSTAND (what does it mean?) --> CREATE (a prompt for a new image)
```

Example: a beach sunset. Analyze: sun, clouds, ocean, warm colors. Understand: an evening scene, calm mood,
natural photography. Create: "A serene evening beach, warm sunset colors, golden hour light, highly detailed".

### How it is built

Lab 23 runs its workflow as a plain Python loop; it does not import LangGraph (its intro text says so). The retry idea is the same one Lab 12 implements as a LangGraph graph;
compare the two in the exercises.

---

## Using the app

Sidebar:

1. **Select demonstration mode:** one of 🖼️ Image Analysis, 🎬 Video Analysis, 🎨 Image Generation, 🔄 Full Agentic Pipeline.
2. **VLM Model Path:** `./Phi-3.5-vision-instruct-int4-ov` (relative to the folder you started Streamlit from).
3. **Inference Device:** GPU (default), CPU or NPU.
4. **🚀 Load Model**, then wait for **✅ Model Ready**.

After loading, the app sets `stop_token_ids = {32007}` so Phi-3.5 stops at `<|end|>`; without it the model keeps writing.

### Mode 1: Image Analysis

1. **Image Source:** 📁 Upload File (jpg, jpeg, png, bmp), 📷 Camera Capture, or 🌐 Sample Image
   (a synthetic color gradient, only useful to test the pipeline).
2. **Analysis Workflow:**

   | Workflow | Steps | Prompts |
   | --- | --- | --- |
   | educational | 3 | visual features you detect; relationships between objects; a prompt to recreate the scene |
   | comprehensive | 5 | detailed description; list of objects; context and story; quality (lighting, composition, clarity); creative prompt |
   | quick | 2 | brief description; image-generation prompt |

3. **🚀 Run Analysis.** Each step shows its prompt, result and processing time.
4. **🎨 Generated Creative Prompt** shows the result of the creative-prompt step.

### Mode 2: Video Analysis

1. Upload a video (mp4, avi, mov, mkv). Try `Data/all_animals.mp4`.
2. **Frame Interval** (10–100, default 30): analyze every Nth frame. At 30 fps, 30 means one frame per second.
3. **Maximum Frames** (1–10, default 5) and **Analysis Prompt**.
4. **🎬 Analyze Video.** Results show the frame number and its time in the video.

```text
frames: 0    30   60   90   120  ...
        ^    ^    ^    ^    ^
        analyzed (each frame on its own)
```

Each frame is analyzed independently; the model does not see earlier frames. Any story across frames is
something you read from the list of answers. The upload is saved as `temp_video_<time>.mp4` in the current folder
and is not deleted.

### Mode 3: Image Generation

This mode teaches prompt structure only. The **🎨 Generate Image** button shows a "not configured" warning; its
message points to files that are not in this repo. Use the prompt formula here, then generate the image with:

- Lab 09: `python GenAI_APIs_lab09_image_gen.py ./stable-diffusion-v1-5-int8-ov "<your prompt>"` (about 66 s on CPU)
- Lab 10: `streamlit run GenAI_APIs_lab10_image_generation_app.py`
- Lab 16: the `generate_image` MCP tool, called by the Lab 17/18 agent

| Part | Example |
| --- | --- |
| Subject | A friendly robot |
| Action | teaching students |
| Setting | in a futuristic classroom |
| Style | digital art |
| Lighting | soft ambient lighting |
| Quality | highly detailed |

Formula: `[Subject] + [Action] + [Setting] + [Style] + [Lighting] + [Quality]`.
"cat in library" is too vague; "A curious cat exploring a magical library, watercolor style, soft ambient lighting,
highly detailed" gives the model something to work with.

### Mode 4: Full Agentic Pipeline

Upload an image and press **▶️ Run Full Pipeline**. The progress bar runs four steps:

1. Preprocess (progress update only; the image is converted inside step 2)
2. Analysis with the **educational** workflow (always this one in this mode)
3. Creative prompt
4. Workflow summary

Results appear in three tabs: **📝 Analysis**, **🎨 Generated Prompt**, **📈 Workflow Summary**.
The summary tab shows the step log, including any retries. The page lists a fifth step, "Create - Generate new image
(if available)"; it is not implemented, so take the prompt to Lab 09.

---

## The code

### Workflow with self-check

```python
@dataclass
class AnalysisStep:
    step_number: int
    task_type: TaskType          # DESCRIBE, DETECT_OBJECTS, ANALYZE_SCENE, EXTRACT_TEXT, QUALITY_CHECK, CREATIVE_PROMPT
    prompt: str
    result: str = ""
    confidence: str = ""
    timestamp: str = ""
    processing_time: float = 0.0
    retry_count: int = 0
```

```python
max_retries = 2
for step in selected_workflow:
    retry_count = 0
    step_successful = False
    while not step_successful and retry_count <= max_retries:
        result, proc_time = self.analyze_with_vlm(image_tensor, step.prompt)   # max_new_tokens=200
        if self._is_low_quality_result(result):
            retry_count += 1
            if retry_count <= max_retries:
                continue                     # ask again
        step_successful = True               # good answer, or out of retries: keep it
        step.result, step.processing_time, step.retry_count = result, proc_time, retry_count
        results.append(step)
```

`_is_low_quality_result()` flags answers under 10 characters or containing phrases such as "i cannot", "sorry",
"error", "unable to", "unclear", "not visible", "no image". It is the same list as Lab 12, with the same weakness:
an honest "the label is not visible" is retried.

Each retry is written to the step log ("🔄 Retry 1/2", "⚠️ Quality Check", "⚠️ Max Retries"). In Image Analysis
mode the log and `retry_count` are not shown; use Full Pipeline mode to see them in **📈 Workflow Summary**.

### Image to tensor

The image is resized to at most 1024 px on its long side and passed as a `[1, height, width, 3]` uint8 `ov.Tensor`.
Video frames go through OpenCV (`cv2.VideoCapture`), are converted from BGR to RGB, and follow the same path.

---

## Demo script (30 minutes)

| Part | Time | What to do | Point to make |
| --- | --- | --- | --- |
| 1 | 3 min | Load the model on GPU while you explain the VLM diagram | INT4 + OpenVINO = a VLM on a laptop |
| 2 | 8 min | Image Analysis, `educational`, a rich scene | Steps go from seeing to understanding to creating |
| 3 | 5 min | Same image, `comprehensive` | More steps, more detail, more time; compare the step times |
| 4 | 5 min | Video Analysis on `Data/all_animals.mp4`, interval 30, 5 frames | Frame sampling; each frame is a separate question |
| 5 | 5 min | Full Pipeline, then open **📈 Workflow Summary** | The step log; look for retries |
| 6 | 4 min | Copy the generated prompt and run Lab 09 with it | Closing the loop: analyze, understand, create |

Measured on 2026-11-09 (`README_Workshop_Demo.md`): three analysis steps and the generated prompt took about
29 s per image on the integrated GPU.

A typical educational run on a beach sunset photo looks like this (illustrative; your answers will differ):

```text
Step 1  Describe        "A setting sun on the horizon, warm orange and red sky fading to blue, a sandy beach ..."
Step 2  Analyze Scene   "The sun is the focal point; the horizon divides sky and sea; waves lead toward the viewer"
Step 3  Creative Prompt "A beach sunset with vibrant orange sky, golden sun reflecting on calm waves,
                         golden hour lighting, highly detailed"
```

---

## Exercises

1. **Image types.** Run `comprehensive` on a photo of a person, a landscape and a document.
   Which did the model handle best? What did it miss or invent?
2. **Loop vs graph.** Compare Lab 23's retry loop with Lab 12's graph. Fill in the table:

   | Aspect | Lab 23 (loop) | Lab 12 (LangGraph) | Which is easier to change? |
   | --- | --- | --- | --- |
   | Where the retry lives | | | |
   | How progress is reported | | | |
   | Adding a conditional step | | | |

3. **Prompt engineering.** Take a generated prompt and make three versions: a style change, a mood change, more
   quality words. Generate each with Lab 09 and compare.
4. **Your own workflow.** Add a 4-step workflow to `execute_analysis_workflow()` for a use case such as
   product photos for an online shop or classroom material. Use the existing `TaskType` values.
5. **Wire up creation.** Load `ov_genai.Text2ImagePipeline("./stable-diffusion-v1-5-int8-ov", "CPU")` and make
   **🎨 Generate Image** and pipeline step 5 actually produce an image.
6. **Design challenge.** Combine Hear (Lab 07), See (Labs 04–06), Reason (Labs 01–02), Act (Labs 12–18) and
   Create (Lab 09) into one app. Lab 16 already exposes most of these as MCP tools.

---

## Discussion questions

| Question | Points to raise |
| --- | --- |
| What makes this "agentic" rather than one model call? | Steps, a self-check with retries, state, an action at the end |
| Why not ask one big question? | Focused questions give more specific answers; each step can be checked |
| Why retry low-quality answers? | Stops a bad answer from feeding the next step; but the check is a phrase list |
| Why run locally with OpenVINO? | Privacy, no per-call cost, works offline; limited by laptop memory and speed |
| What if the model is wrong? | VLMs hallucinate objects and text; a human must review important results |
| Who owns a generated image, and how can it be misused? | Copyright, deepfakes, labeling AI content |

---

## Where Lab 23 fits

| Lab | Idea used here |
| --- | --- |
| 04–06 (Part 1) | VLM on an image, the camera, video frames |
| 09–10 (Part 1) | Stable Diffusion for the Create step |
| 11–12 | Multi-step visual workflow; self-check with retries (12) |
| 13–18 | Tools; local models as MCP tools (16) called by a cloud agent (17, 18) |
| 19–22 | Shared context and chaining between steps |

---

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `Failed to load model` | Check the folder is in the repo root and Streamlit was started from the repo root. |
| GPU or NPU error | Select CPU in **Inference Device**. |
| Slow analysis | Use GPU, the `quick` workflow, or fewer video frames. |
| Long rambling answers | The stop token fix is missing; use the lab file from this folder. |
| Many retries | Blurry or dark images give weak answers; try a clearer image or a simpler workflow. |
| Video not processed | Convert it to MP4 (H.264). |
| Out of memory | Close other apps; images are already capped at 1024 px. |
| **🎨 Generate Image** only shows a warning | Expected; generate with Lab 09 or 10. |

Further reading: [OpenVINO GenAI](https://docs.openvino.ai/) · [Phi-3.5-vision](https://huggingface.co/microsoft/Phi-3.5-vision-instruct).
Previous: `README_LangGraph.md` (Labs 11–12), `README_MCP.md` (13–18), `README_Skills.md` (19–22).
