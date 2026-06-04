import json
from pathlib import Path


class CostTracker:
    def __init__(self):
        self.records = {}

    def record(self, component: str, model: str, input_text: str, output_text: str, elapsed_seconds: float):
        self.records[component] = {
            "model": model,
            "input_chars": len(input_text) if input_text else 0,
            "output_chars": len(output_text) if output_text else 0,
            "elapsed_seconds": round(elapsed_seconds, 2)
        }

    def to_dict(self) -> dict:
        return self.records

    def save_json(self, output_path: str):
        path = Path(output_path)
        path.write_text(
            json.dumps(self.records, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )