"""
cloud_model.py - the cloud model used by the agent labs (Labs 14, 15, 21).

Your Microsoft Foundry deployment (Azure OpenAI v1 API), set up exactly as in Lab 01:
    AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT   (in .env)

Two helpers, both return a dict with "success" so they can be used as skills or MCP tools:
    ask_cloud_model(question)          -> {"success", "response", "model"}
    image_to_mermaid(image_path, ...)  -> {"success", "mermaid_code", "image_path", "model"}

Behind a corporate proxy with a private Foundry resource, add .openai.azure.com to NO_PROXY in your terminal
(README_Reproduce_Demo.md -> "Proxy: set, check, unset").
"""
import base64
import mimetypes
import os
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

INSTRUCTIONS = ("You are a concise technical assistant for engineering students. "
                "Answer in at most 150 words; say so when you are not sure.")
MERMAID_INSTRUCTIONS = ("Convert the diagram in the image to Mermaid code. Output only the Mermaid code, "
                        "no explanation and no code fences.")


def _client():
    from openai import OpenAI
    key, endpoint = os.environ.get("AZURE_OPENAI_API_KEY"), os.environ.get("AZURE_OPENAI_ENDPOINT")
    if not key or not endpoint:
        raise RuntimeError("Set AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY and AZURE_OPENAI_DEPLOYMENT in .env (see Lab 01)")
    return OpenAI(api_key=key, base_url=endpoint.rstrip("/") + "/openai/v1/")


def deployment():
    return os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-6.1-sol")


def ask_cloud_model(question: str, instructions: str = INSTRUCTIONS) -> dict:
    """Answer a question with the Foundry deployment (Responses API, low reasoning effort)."""
    try:
        resp = _client().responses.create(model=deployment(), instructions=instructions, input=question,
                                          reasoning={"effort": "low"})
        return {"success": True, "response": resp.output_text.strip(), "model": deployment(), "query": question}
    except Exception as e:
        return {"success": False, "error": f"{type(e).__name__}: {e}"}


def image_to_mermaid(image_path: str, diagram_type: str = "") -> dict:
    """Turn a diagram image (PNG/JPG/...) into Mermaid code with the deployment's vision input."""
    path = Path(image_path.strip().strip('"'))
    if not path.is_file():
        return {"success": False, "error": f"Image file not found: {image_path}"}
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    data_url = f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()
    hint = f" Use a Mermaid {diagram_type}." if diagram_type else ""
    try:
        resp = _client().responses.create(
            model=deployment(), instructions=MERMAID_INSTRUCTIONS, reasoning={"effort": "low"},
            input=[{"role": "user", "content": [
                {"type": "input_text", "text": "Convert this diagram to Mermaid." + hint},
                {"type": "input_image", "image_url": data_url}]}])
        code = re.sub(r"^```(?:mermaid)?\s*|\s*```$", "", resp.output_text.strip())
        return {"success": True, "mermaid_code": code, "image_path": str(path), "model": deployment()}
    except Exception as e:
        return {"success": False, "error": f"{type(e).__name__}: {e}"}


if __name__ == "__main__":
    print(ask_cloud_model("What is MLD in Wi-Fi 7? One sentence."))
