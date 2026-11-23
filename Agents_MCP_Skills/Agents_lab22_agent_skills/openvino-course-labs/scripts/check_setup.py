"""
Check that a laptop is ready for the GenAI_APIs_Cloud_Local labs (01-23).

Prints one line per check: OK, MISSING or WARN. Never prints secret values.
Run from anywhere:  python check_setup.py [--repo PATH]
"""
import argparse
import importlib.util
import os
import sys
from pathlib import Path

MODELS = {
    "TinyLlama-1.1B-Chat-v1.0": "Lab 03",
    "Phi-3.5-vision-instruct-int4-ov": "Labs 04-06, 11, 12, 16, 23",
    "whisper-base": "Labs 07, 08, 16",
    "stable-diffusion-v1-5-int8-ov": "Labs 09, 10, 16",
    "Qwen3-1.7B-int4-ov": "Lab 20 (local brain)",
}
PACKAGES = {"openvino_genai": "Labs 03-23", "openai": "Labs 01, 14, 15, 17, 20, 21", "anthropic": "Labs 02, 18",
            "streamlit": "UI labs", "langgraph": "Labs 12, 20", "mcp": "Labs 14-18",
            "dotenv": "cloud labs"}
ENV_KEYS = {"AZURE_OPENAI_ENDPOINT": "Labs 01, 14, 15, 17, 20, 21", "AZURE_OPENAI_API_KEY": "Labs 01, 14, 15, 17, 20, 21",
            "AZURE_OPENAI_DEPLOYMENT": "Labs 01, 14, 15, 17, 20, 21", "ANTHROPIC_API_KEY": "Labs 02, 18"}


def find_repo(start):
    for p in [start, *start.parents]:
        if (p / "GenAI_APIs_lab01_gpt_sol.py").exists():
            return p
    return None


def main():
    here = Path(__file__).resolve()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--repo", type=Path, help="repo root (default: search upward, then the current folder)")
    args = parser.parse_args()
    repo = args.repo or find_repo(here.parent) or find_repo(Path.cwd())
    if repo is None:
        print("MISSING repo: run from inside GenAI_APIs_Cloud_Local or pass --repo")
        return 1
    print(f"repo: {repo}")

    ok = sys.version_info >= (3, 10)
    print(f"{'OK     ' if ok else 'MISSING'} Python {sys.version.split()[0]} (need 3.10+)")

    for pkg, used in PACKAGES.items():
        found = importlib.util.find_spec(pkg) is not None
        print(f"{'OK     ' if found else 'MISSING'} package {pkg:15} ({used})")

    models_dir = Path(os.environ.get("LAB_MODELS_DIR", repo))
    for name, used in MODELS.items():
        found = (models_dir / name).is_dir()
        print(f"{'OK     ' if found else 'MISSING'} model {name:34} ({used})")

    if importlib.util.find_spec("openvino"):
        import openvino as ov
        print(f"OK      OpenVINO devices: {ov.Core().available_devices}")

    env = {}
    env_file = repo / ".env"
    if env_file.is_file() and importlib.util.find_spec("dotenv"):
        from dotenv import dotenv_values
        env = dotenv_values(env_file)
    for key, used in ENV_KEYS.items():
        found = bool(os.environ.get(key) or env.get(key))
        print(f"{'OK     ' if found else 'WARN   '} {key:24} set ({used})")

    no_proxy = os.environ.get("NO_PROXY", "") + "," + os.environ.get("no_proxy", "")
    if os.environ.get("HTTPS_PROXY") and ".openai.azure.com" not in no_proxy:
        print("WARN    HTTPS_PROXY is set but NO_PROXY lacks .openai.azure.com "
              "(a private Foundry resource answers 403 - see README_Reproduce_Demo.md)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
