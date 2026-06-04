from src.llm.client import DeepSeekClient
from src.utils.prompt_loader import load_prompt


class OutlinePlanner:
    def __init__(self):
        self.client = DeepSeekClient(component_name="outline_planner")
        self.system_prompt = load_prompt("outline_planner.txt")

    def get_model_name(self) -> str:
        return self.client.model_name

    def plan_outline(self, topic: str, goal: str, literature_pack_text: str, organized_material: str = "") -> str:
        user_message = f"""【论文主题】
{topic}

【当前目标】
{goal}

【文献整理结果】
{literature_pack_text}

【已有研究材料】
{organized_material}
"""
        return self.client.chat(
            user_message=user_message,
            system_message=self.system_prompt
        )

    def plan_outline_stream(self, topic: str, goal: str, literature_pack_text: str, organized_material: str = "") -> str:
        user_message = f"""【论文主题】
{topic}

【当前目标】
{goal}

【文献整理结果】
{literature_pack_text}

【已有研究材料】
{organized_material}
"""
        return self.client.chat_stream(
            user_message=user_message,
            system_message=self.system_prompt
        )