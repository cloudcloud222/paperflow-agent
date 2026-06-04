from src.llm.client import DeepSeekClient
from src.utils.prompt_loader import load_prompt


class DraftReviewer:
    def __init__(self):
        self.client = DeepSeekClient(component_name="reviewer")
        self.system_prompt = load_prompt("reviewer.txt")
    
    def get_model_name(self) -> str:
         return self.client.model_name

    def review(self, draft_text: str) -> str:
        return self.client.chat(
            user_message=draft_text,
            system_message=self.system_prompt
        )

    def review_stream(self, draft_text: str) -> str:
        return self.client.chat_stream(
            user_message=draft_text,
            system_message=self.system_prompt
        )