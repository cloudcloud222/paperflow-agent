from src.llm.client import DeepSeekClient
from src.utils.prompt_loader import load_prompt


class TaskPlanner:
    def __init__(self):
        self.client = DeepSeekClient(component_name="planner")
        self.system_prompt = load_prompt("planner.txt")
    
    def get_model_name(self) -> str:
         return self.client.model_name

    def plan(self, user_goal: str) -> str:
        return self.client.chat(
            user_message=user_goal,
            system_message=self.system_prompt
        )

    def plan_stream(self, user_goal: str) -> str:
        return self.client.chat_stream(
            user_message=user_goal,
            system_message=self.system_prompt
        )