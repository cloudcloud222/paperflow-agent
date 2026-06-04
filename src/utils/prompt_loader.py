from pathlib import Path


def load_prompt(filename: str) -> str:
    prompt_path = Path("src/prompts") / filename
    return prompt_path.read_text(encoding="utf-8").strip()