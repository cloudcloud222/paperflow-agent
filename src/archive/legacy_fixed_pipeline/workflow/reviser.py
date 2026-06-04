from src.llm.client import DeepSeekClient
from src.utils.prompt_loader import load_prompt


class DraftReviser:
    def __init__(self):
        self.client = DeepSeekClient(component_name="reviser")
        self.system_prompt = load_prompt("reviser.txt")
    
    def get_model_name(self) -> str:
            return self.client.model_name

    def revise(self, draft_text: str, review_text: str) -> str:
        user_message = f"""【原始初稿】
{draft_text}

【审阅意见】
{review_text}
"""
        return self.client.chat(
            user_message=user_message,
            system_message=self.system_prompt
        )

    def revise_stream(self, draft_text: str, review_text: str) -> str:
        user_message = f"""【原始初稿】
{draft_text}

【审阅意见】
{review_text}
"""
        return self.client.chat_stream(
            user_message=user_message,
            system_message=self.system_prompt
        )