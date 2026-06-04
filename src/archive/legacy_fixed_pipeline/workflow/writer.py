from src.llm.client import DeepSeekClient
from src.utils.prompt_loader import load_prompt


class DraftWriter:
    def __init__(self):
        self.client = DeepSeekClient(component_name="writer")
        self.system_prompt = load_prompt("writer.txt")

    def get_model_name(self) -> str:
         return self.client.model_name

    def write_draft(self, material: str) -> str:
        return self.client.chat(
            user_message=material,
            system_message=self.system_prompt
        )

    def write_draft_stream(self, material: str) -> str:
        return self.client.chat_stream(
            user_message=material,
            system_message=self.system_prompt
        )