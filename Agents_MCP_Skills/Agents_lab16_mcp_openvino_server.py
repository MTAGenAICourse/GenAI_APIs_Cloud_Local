"""
Lab 16 - Local models as MCP tools: an OpenVINO MCP server (FastMCP).

The Part 1 local models become tools that ANY MCP client can discover and call:
    describe_image    Phi-3.5-vision  (Lab 04)
    transcribe_audio  Whisper-base    (Lab 07)
    generate_image    Stable Diffusion (Lab 09)
    calculate         safe arithmetic
    list_data_files   what is in Data/

The models run on your laptop; the agent that calls them (Lab 17 GPT, Lab 18 Claude,
Claude Desktop, VS Code...) only sees the tool names, descriptions and JSON schemas.

You normally don't run this file yourself: an MCP client starts it as a subprocess and
talks to it over stdio. To try it on its own:
    python Agents_MCP_Skills/Agents_lab16_mcp_openvino_server.py --self-test
    mcp dev Agents_MCP_Skills/Agents_lab16_mcp_openvino_server.py      # MCP Inspector (needs Node.js)

Models are loaded lazily (first call) from the repo root, the folders you downloaded in Part 1.
Device: set LAB_DEVICE=GPU to use the integrated GPU (default CPU).
Models elsewhere? Set LAB_MODELS_DIR to the folder that holds them.

Exercise: add a summarize_text tool backed by the Lab 03 LLMPipeline (TinyLlama), then ask
the Lab 17/18 agent to "describe Data/Robot.jpg and summarize it in five words".
"""
import ast
import operator
import os
import sys
import time
import wave
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Import the heavy native libraries at start-up, before the MCP server begins reading stdin.
# On Windows, importing them later (inside a tool call) can block on the stdin pipe and hang the server.
import numpy as np            # noqa: E402
import openvino as ov         # noqa: E402
import openvino_genai as ov_genai  # noqa: E402
from PIL import Image         # noqa: E402

ROOT =Path(__file__).resolve().parent.parent      # repo root: model folders and Data/ live here
DEVICE = os.environ.get("LAB_DEVICE", "CPU")
MODELS_DIR = Path(os.environ.get("LAB_MODELS_DIR", ROOT))   # override if your models live elsewhere
MODELS = {
    "vlm": MODELS_DIR / "Phi-3.5-vision-instruct-int4-ov",
    "whisper": MODELS_DIR / "whisper-base",
    "sd": MODELS_DIR / "stable-diffusion-v1-5-int8-ov",
}

mcp = FastMCP("openvino-local-models", log_level="WARNING")   # keep stderr quiet
_pipes = {}


def log(msg):
    # stdout carries the MCP protocol; anything else must go to stderr
    print(f"[lab16] {msg}", file=sys.stderr, flush=True)


def _pipe(kind):
    """Load a pipeline on first use and keep it for later calls."""
    if kind not in _pipes:
        import openvino_genai as ov_genai
        path = MODELS[kind]
        if not path.is_dir():
            raise RuntimeError(f"Model folder not found: {path}. Download it as in the README (Part 1 setup).")
        start = time.time()
        cls = {"vlm": ov_genai.VLMPipeline, "whisper": ov_genai.WhisperPipeline,
               "sd": ov_genai.Text2ImagePipeline}[kind]
        _pipes[kind] = cls(str(path), DEVICE)
        log(f"loaded {path.name} on {DEVICE} in {time.time() - start:.1f}s")
    return _pipes[kind]


def _inside_repo(path_str):
    """Resolve a path relative to the repo root and refuse anything outside it."""
    p = Path(path_str)
    p = (p if p.is_absolute() else ROOT / p).resolve()
    if ROOT not in p.parents and p != ROOT:
        raise ValueError(f"Only files inside the course repo are allowed: {path_str}")
    if not p.is_file():
        raise FileNotFoundError(f"No such file: {path_str}. Call list_data_files to see what exists.")
    return p


@mcp.tool()
def list_data_files() -> list[str]:
    """List the sample files in the repo's Data/ folder (images, video, audio) as repo-relative paths."""
    return sorted(str(p.relative_to(ROOT)).replace("\\", "/") for p in (ROOT / "Data").iterdir() if p.is_file())


@mcp.tool()
def describe_image(image_path: str, question: str = "Describe this image in two sentences.") -> str:
    """Answer a question about a local image with the on-device vision-language model (Phi-3.5-vision).

    image_path: repo-relative path such as Data/Robot.jpg.
    question: what to ask about the image.
    """
    import numpy as np
    import openvino as ov
    from PIL import Image

    img = Image.open(_inside_repo(image_path)).convert("RGB")
    pipe = _pipe("vlm")
    cfg = pipe.get_generation_config()
    cfg.max_new_tokens = 200
    cfg.stop_token_ids = {32007}            # Phi-3.5 ends its turn with <|end|>
    tensor = ov.Tensor(np.array(img)[None])
    return str(pipe.generate(question, image=tensor, generation_config=cfg)).strip()


@mcp.tool()
def transcribe_audio(wav_path: str) -> str:
    """Transcribe a local 16 kHz mono 16-bit WAV file to text with the on-device Whisper model."""
    import numpy as np

    with wave.open(str(_inside_repo(wav_path))) as w:
        if w.getframerate() != 16000 or w.getnchannels() != 1 or w.getsampwidth() != 2:
            raise ValueError("Need a 16 kHz, mono, 16-bit WAV file")
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    return str(_pipe("whisper").generate(pcm.astype(np.float32) / 32768.0)).strip()


@mcp.tool()
def generate_image(prompt: str, steps: int = 20) -> str:
    """Generate a 512x512 image from a text prompt with on-device Stable Diffusion.

    Slow on CPU (about a minute at 20 steps). Returns the repo-relative path of the saved PNG.
    """
    from PIL import Image

    steps = max(1, min(int(steps), 50))
    result = _pipe("sd").generate(prompt, width=512, height=512, num_inference_steps=steps)
    out_dir = ROOT / "output"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"agent_image_{int(time.time())}.png"
    Image.fromarray(result.data[0]).save(out)
    return str(out.relative_to(ROOT)).replace("\\", "/")


_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.Mod: operator.mod, ast.FloorDiv: operator.floordiv,
        ast.USub: operator.neg, ast.UAdd: operator.pos}


def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("Only numbers and + - * / // % ** are allowed")


@mcp.tool()
def calculate(expression: str) -> str:
    """Evaluate an arithmetic expression exactly, e.g. "(17 + 25) * 2" or "0.15 * 240"."""
    return str(_eval(ast.parse(expression, mode="eval").body))


def self_test():
    """Call each fast tool directly, without an MCP client."""
    print("list_data_files ->", list_data_files())
    print("calculate('(17 + 25) * 2') ->", calculate("(17 + 25) * 2"))
    print("describe_image('Data/Robot.jpg') ->", describe_image("Data/Robot.jpg", "What is the robot doing?"))


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    else:
        log(f"serving over stdio (models from {MODELS_DIR}, device {DEVICE})")
        mcp.run()          # stdio transport by default
