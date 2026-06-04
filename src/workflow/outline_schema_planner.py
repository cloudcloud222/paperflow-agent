import json
from src.llm.client import DeepSeekClient
from src.utils.prompt_loader import load_prompt


class OutlineSchemaPlanner:
    def __init__(self):
        self.client = DeepSeekClient(component_name="outline_schema_planner")
        self.system_prompt = load_prompt("outline_schema_planner.txt")

    def get_model_name(self) -> str:
        return self.client.model_name

    def _clean_json_text(self, text: str) -> str:
        text = text.strip()

        if text.startswith("```json"):
            text = text[len("```json"):].strip()
        elif text.startswith("```"):
            text = text[len("```"):].strip()

        if text.endswith("```"):
            text = text[:-3].strip()

        return text

    def plan_schema_raw(
        self,
        topic: str,
        goal: str,
        literature_pack_text: str,
        organized_material: str = ""
    ) -> str:
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

    def plan_schema(
        self,
        topic: str,
        goal: str,
        literature_pack_text: str,
        organized_material: str = ""
    ) -> dict:
        raw_text = self.plan_schema_raw(
            topic=topic,
            goal=goal,
            literature_pack_text=literature_pack_text,
            organized_material=organized_material
        )

        cleaned_text = self._clean_json_text(raw_text)
        return json.loads(cleaned_text)