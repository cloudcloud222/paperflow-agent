import json
from src.llm.client import DeepSeekClient
from src.utils.prompt_loader import load_prompt


class NodeReferenceSelector:
    def __init__(self):
        self.client = DeepSeekClient(component_name="node_reference_selector")
        self.system_prompt = load_prompt("node_reference_selector.txt")

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

    def _build_user_message(
        self,
        topic: str,
        goal: str,
        node_card: dict,
        literature_summaries: list[dict],
        outline_review_text: str = "",
        previous_context_text: str = ""
    ) -> str:
        return f"""【论文主题】
{topic}

【当前写作目标】
{goal}

【节点卡片】
{json.dumps(node_card, ensure_ascii=False, indent=2)}

【总纲审查意见】
{outline_review_text}

【已有前序上下文】
{previous_context_text}

【候选文献摘要】
{json.dumps(literature_summaries, ensure_ascii=False, indent=2)}
"""

    def select_references_raw(
        self,
        topic: str,
        goal: str,
        node_card: dict,
        literature_summaries: list[dict],
        outline_review_text: str = "",
        previous_context_text: str = ""
    ) -> str:
        user_message = self._build_user_message(
            topic=topic,
            goal=goal,
            node_card=node_card,
            literature_summaries=literature_summaries,
            outline_review_text=outline_review_text,
            previous_context_text=previous_context_text
        )
        return self.client.chat(
            user_message=user_message,
            system_message=self.system_prompt
        )

    def select_references(
        self,
        topic: str,
        goal: str,
        node_card: dict,
        literature_summaries: list[dict],
        outline_review_text: str = "",
        previous_context_text: str = ""
    ) -> dict:
        raw_text = self.select_references_raw(
            topic=topic,
            goal=goal,
            node_card=node_card,
            literature_summaries=literature_summaries,
            outline_review_text=outline_review_text,
            previous_context_text=previous_context_text
        )
        cleaned_text = self._clean_json_text(raw_text)
        return json.loads(cleaned_text)