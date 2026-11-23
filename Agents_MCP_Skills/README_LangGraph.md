# Labs 11–12: A Visual Agent, Plain Python vs LangGraph

Two Streamlit apps run the same multi-step visual inspection with the local Phi-3.5-vision model.
Lab 11 writes the agent as a plain Python loop. Lab 12 builds the same agent as a LangGraph state graph
and adds a self-check: a weak answer is retried before the agent moves on.

Run from the repo root (`GenAI_APIs_Cloud_Local`):

```bash
streamlit run Agents_MCP_Skills/Agents_lab11_visual_agent.py
streamlit run Agents_MCP_Skills/Agents_lab12_visual_agent_langgraph.py
```

---

## Setup

1. Finish the Part 1 setup in the repo root `README.md` (venv, models).
2. Install the Part 2 packages from the repo root: `pip install -r Agents_MCP_Skills/requirements.txt`
   (adds `langgraph`; only Lab 12 needs it here).
3. Download the vision model into the repo root, as in Lab 04:

   ```bash
   hf download OpenVINO/Phi-3.5-vision-instruct-int4-ov --local-dir Phi-3.5-vision-instruct-int4-ov
   ```

Both apps default to the path `./Phi-3.5-vision-instruct-int4-ov/`. That path is relative to the folder you
start Streamlit from, so start it from the repo root. A sample image is in `Data/Robot.jpg`.

Both apps set `stop_token_ids = {32007}` after loading the model. Phi-3.5 ends its turn with `<|end|>`
(token 32007), but the exported `generation_config.json` lists only `</s>`, so without this the model keeps writing.

---

## Using the apps

The two apps have the same layout.

| Step | Lab 11 | Lab 12 |
| --- | --- | --- |
| 1. Sidebar: model path and device (GPU or CPU, GPU selected by default) | same | same |
| 2. Load the model | **🚀 Initialize Agent** | **🚀 Initialize LangGraph Agent** |
| 3. Tab **📸 Live Analysis**: pick **Camera** or **Upload File** | same | same |
| 4. Pick a workflow in **Select Analysis Workflow** | same | same |
| 5. Run | **🚀 Execute Agent Workflow** | **🚀 Execute LangGraph Agent Workflow** |
| 6. Tab **📊 Results Dashboard**: past runs, **📥 Export All Results** then **Download JSON Report** | same | same |

The **🔄 Batch Processing** tab is a placeholder in both labs ("Coming soon"); it does not analyze anything.
The **🛠️ Customize Workflow** checkbox lets you type an extra prompt and pick a task type.

### Workflows

Each predefined workflow is three VLM questions about the same image.

| Workflow | Step 1 | Step 2 | Step 3 |
| --- | --- | --- | --- |
| Quality Inspection | Main object or product | Visible defects or damage | Quality score 1–10 and why |
| Safety Inspection | People and objects | Safety hazards | Is safety equipment used? |
| Inventory Count | How many distinct items | Categories | Count per category |
| Document Analysis | Document type | Extract visible text and numbers | Complete and legible? |
| Scene Understanding | What is happening | Significant objects and positions | Most prominent element |

The task types are an enum: `object_detection`, `quality_inspection`, `safety_check`, `comparison`,
`counting`, `text_extraction`. They label the steps; the model only sees the prompt text.

---

## Lab 11: the agent as a loop

`VisionAgent` resizes the image to at most 1024 px, turns it into an `ov.Tensor`, and asks each question in order:

```python
def execute_workflow(self, image, workflow, progress_callback=None):
    image_tensor = self.process_image(image)
    results = []
    for i, step in enumerate(workflow):
        if progress_callback:
            progress_callback(i, len(workflow), step.prompt)
        analyzed_step = self.analyze_step(image_tensor, step)   # one VLM call, max_new_tokens=200
        results.append(analyzed_step)                            # state = a Python list
        self.analysis_history.append(analyzed_step)
    return results
```

`make_decision()` then builds a summary dict from the results. There is no LLM call in this step; it joins
the first 100 characters of each answer.

This is fine for a fixed list of questions. It gets harder when you want branches ("if a defect was found,
ask a follow-up"), retries, or a view of where the run is.

---

## Lab 12: the same agent as a state graph

### The graph

```text
preprocess_image
       |
       v
execute_analysis_step  <-------------------------------+
       |                                               |
       v                                               |
should_continue(state)                                 |
   |  "continue" (more steps, or retry this one)       |
   +----------------> check_workflow_complete ---------+
   |
   |  "complete" (current_step == number of steps)
   v
make_decision  -->  finalize  -->  END
```

| Node | What it does |
| --- | --- |
| `preprocess_image` | Pass-through. The image is already a tensor when the graph starts. |
| `execute_analysis_step` | One VLM call. Checks the answer quality. Records the step or asks for a retry. |
| `check_workflow_complete` | Pass-through node, kept so the loop is visible in the graph. |
| `make_decision` | Builds the summary dict (no LLM call, same as Lab 11) and adds `"agent_type": "LangGraph Multi-Step Agent"`. |
| `finalize` | Adds the results to the agent's history. |

The graph is built once, in the agent constructor:

```python
workflow = StateGraph(AgentState)
workflow.add_node("preprocess_image", self.preprocess_image_node)
workflow.add_node("execute_analysis_step", self.execute_analysis_step_node)
workflow.add_node("check_workflow_complete", self.check_workflow_complete_node)
workflow.add_node("make_decision", self.make_decision_node)
workflow.add_node("finalize", self.finalize_node)

workflow.set_entry_point("preprocess_image")
workflow.add_edge("preprocess_image", "execute_analysis_step")
workflow.add_conditional_edges("execute_analysis_step", self.should_continue,
                               {"continue": "check_workflow_complete", "complete": "make_decision"})
workflow.add_edge("check_workflow_complete", "execute_analysis_step")
workflow.add_edge("make_decision", "finalize")
workflow.add_edge("finalize", END)
graph = workflow.compile()
```

### The state

```python
class AgentState(TypedDict):
    image_tensor: Any
    workflow: List[AnalysisStep]
    current_step: int
    results: Annotated[List[AnalysisStep], operator.add]   # reducer: updates are appended
    decision: Dict[str, Any]
    pipeline: Any
    error: str
    retry_count: int
```

Two rules make the graph correct:

1. **A node returns only the keys it changes.** LangGraph merges that partial dict into the state.
2. **`results` has an `operator.add` reducer.** Returning `{"results": [step]}` appends one item.
   If a node returned the whole state, every earlier result would be appended again on each pass.

### Self-check and retry

The retry logic lives in `execute_analysis_step_node`, not in the routing function:

```python
retry_count = state.get("retry_count", 0)
max_retries = 2
if self._is_low_quality_result(result) and retry_count < max_retries:
    return {"retry_count": retry_count + 1}        # not recorded, step counter unchanged -> loop runs it again

done = replace(step, result=result, timestamp=..., confidence=f"{elapsed:.2f}s")
return {"results": [done], "current_step": current_step_idx + 1, "retry_count": 0}
```

The routing function only reads the state. LangGraph does not save changes made inside a routing function,
so it must not do bookkeeping:

```python
def should_continue(self, state):
    if state.get("current_step", 0) >= len(state["workflow"]):
        return "complete"
    return "continue"
```

`_is_low_quality_result()` flags an answer that is shorter than 10 characters or contains one of these phrases:
"i cannot", "i can't", "i don't", "i am unable", "sorry", "error", "unable to", "not able to",
"cannot determine", "unclear", "not visible", "no image", "image not".

Retries print to the terminal that runs Streamlit (`🔄 RETRY: Step 2 ...`). After two retries the step is
kept anyway and a warning is printed. If a step raises an exception, the error is stored and the step counter
still advances, so a failing step cannot loop forever.

Phrase matching is crude. An honest answer such as "The serial number is not visible" is flagged and
re-asked twice. Watch for this in the Safety and Document workflows.

### Streaming

The app runs the graph once and reads the state after every node:

```python
for state in self.graph.stream(initial_state, stream_mode="values"):
    final_state = state                     # full state after each node; the last one is the result
    current = state.get("current_step", 0)
    ...update the progress bar...
```

Calling `graph.invoke()` after the stream to get the final state would run every VLM call a second time.

---

## Lab 11 vs Lab 12

| Aspect | Lab 11 (loop) | Lab 12 (LangGraph) |
| --- | --- | --- |
| State | A Python list inside the method | Typed `AgentState`, merged by LangGraph |
| Control flow | `for` loop | Nodes, edges, one conditional edge |
| Self-check | None | Low-quality answers retried up to 2 times |
| Progress | Callback before each step | Read from the state after each node |
| Adding a branch | Edit the loop | Add a node and an edge |
| Lines of agent code | Fewer | More |

Measured on the instructor laptop on 2026-11-09 (see `README_Workshop_Demo.md`): a 3-step Lab 12 workflow,
three VLM calls, took about 8 s on the integrated GPU.

For three fixed questions, the loop is shorter and easier to read. The graph pays off when the flow has
branches, retries or loops that you want to see and change in one place.

---

## Output format

One step in the exported JSON (`steps` list). The `confidence` field holds the processing time, not a probability:

```json
{
  "step_number": 1,
  "task_type": "object_detection",
  "prompt": "What is the main object or product in this image? Describe it briefly.",
  "result": "A white humanoid robot holding a cup of coffee.",
  "confidence": "1.23s",
  "timestamp": "14:30:45"
}
```

The `decision` object has `timestamp`, `total_steps`, `findings` (step, task, result) and `summary`.
The values above are an illustration; your answers and times will differ.

Note: `asdict(step)` keeps `task_type` as a Python enum, which `json.dumps` cannot serialize on its own.
The export passes `default=lambda o: getattr(o, "value", str(o))`, so the report stores `"object_detection"` etc.

---

## Exercises

None of these are implemented in the labs. Each one is a small change to Lab 12.

1. **Conditional follow-up.** In Quality Inspection, parse the 1–10 score from step 3. If it is below 7,
   route to a new node that asks "Describe the worst defect and where it is." Add the branch with
   `add_conditional_edges`.
2. **Your own node.** Add `caption: str` to `AgentState` and a node after `preprocess_image`.
   Return only the key you change, then show the caption in `make_decision`:

   ```python
   def caption_node(self, state):
       text = str(state["pipeline"].generate("Give a five-word caption.", image=state["image_tensor"],
                                             max_new_tokens=20))
       return {"caption": text}
   ```

3. **Parallel branches.** Add two nodes that both start from `preprocess_image` (for example "objects" and
   "text") and both lead to a merge node. Both branches write to `results`, so the reducer is what keeps
   their updates from overwriting each other. Measure whether it is faster on your device; one VLM pipeline
   may still run the calls one after the other.
4. **Better self-check.** Replace the phrase list with a second VLM call: "Does this answer the question? yes/no".
   Compare the number of retries on five images.

---

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `Failed to load model` | Check the folder exists in the repo root and that you started Streamlit from the repo root. |
| GPU not available | Select **CPU** in the sidebar. |
| `ModuleNotFoundError: langgraph` | `pip install langgraph` (Lab 12 only). |
| Answers run on and repeat | The stop token fix is missing; use the lab files from this folder. |
| A step is slow and repeats | It was flagged as low quality and retried; see the terminal output. |
| Out of memory | Use smaller images or close other apps; images are already capped at 1024 px. |

Further reading: [LangGraph docs](https://langchain-ai.github.io/langgraph/) ·
[OpenVINO GenAI](https://docs.openvino.ai/) · [Phi-3.5-vision](https://huggingface.co/microsoft/Phi-3.5-vision-instruct)
