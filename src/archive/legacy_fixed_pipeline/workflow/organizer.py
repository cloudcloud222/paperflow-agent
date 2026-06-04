from src.llm.client import DeepSeekClient
from src.utils.prompt_loader import load_prompt


class MaterialOrganizer:
    def __init__(self):
        self.client = DeepSeekClient(component_name="organizer")
        self.system_prompt = load_prompt("organizer.txt")

    def get_model_name(self) -> str:
         return self.client.model_name

    def organize(self, raw_material: str) -> str:
        return self.client.chat(
            user_message=raw_material,
            system_message=self.system_prompt
        )

    def organize_stream(self, raw_material: str) -> str:
        return self.client.chat_stream(
            user_message=raw_material,
            system_message=self.system_prompt
        )