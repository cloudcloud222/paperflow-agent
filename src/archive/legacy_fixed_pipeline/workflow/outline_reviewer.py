from src.llm.client import DeepSeekClient
from src.utils.prompt_loader import load_prompt


class OutlineReviewer:
    def __init__(self):
        self.client = DeepSeekClient(component_name="outline_reviewer")
        self.system_prompt = load_prompt("outline_reviewer.txt")

    def get_model_name(self) -> str:
        return self.client.model_name

    def review_outline(self, outline_text: str) -> str:
        return self.client.chat(
            user_message=outline_text,
            system_message=self.system_prompt
        )

    def review_outline_stream(self, outline_text: str) -> str:
        return self.client.chat_stream(
            user_message=outline_text,
            system_message=self.system_prompt
        )