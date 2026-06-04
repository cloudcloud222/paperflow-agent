import json
from src.llm.client import DeepSeekClient
from src.utils.prompt_loader import load_prompt


class NodeReviser:
    def __init__(self):
        self.client = DeepSeekClient(component_name="node_reviser")
        self.system_prompt = load_prompt("node_reviser.txt")

    def get_model_name(self) -> str:
        return self.client.model_name

    def _build_user_message(
        self,
        topic: str,
        goal: str,
        node_card: dict,
        node_text: str,
        consistency_report: str,
        literature_pack_text: str = "",
        outline_review_text: str = "",
        previous_context_text: str = ""
    ) -> str:
        return f"""【论文主题】
{topic}

【当前写作目标】
{goal}

【节点卡片】
{json.dumps(node_card, ensure_ascii=False, indent=2)}

【当前节点正文】
{node_text}

【节点一致性检查报告】
{consistency_report}

【文献整理总文档】
{literature_pack_text}

【总纲审查意见】
{outline_review_text}

【已有前序上下文】
{previous_context_text}
"""

    def revise_node(
        self,
        topic: str,
        goal: str,
        node_card: dict,
        node_text: str,
        consistency_report: str,
        literature_pack_text: str = "",
        outline_review_text: str = "",
        previous_context_text: str = ""
    ) -> str:
        user_message = self._build_user_message(
            topic=topic,
            goal=goal,
            node_card=node_card,
            node_text=node_text,
            consistency_report=consistency_report,
            literature_pack_text=literature_pack_text,
            outline_review_text=outline_review_text,
            previous_context_text=previous_context_text
        )
        return self.client.chat(
            user_message=user_message,
            system_message=self.system_prompt
        )

    def revise_node_stream(
        self,
        topic: str,
        goal: str,
        node_card: dict,
        node_text: str,
        consistency_report: str,
        literature_pack_text: str = "",
        outline_review_text: str = "",
        previous_context_text: str = ""
    ) -> str:
        user_message = self._build_user_message(
            topic=topic,
            goal=goal,
            node_card=node_card,
            node_text=node_text,
            consistency_report=consistency_report,
            literature_pack_text=literature_pack_text,
            outline_review_text=outline_review_text,
            previous_context_text=previous_context_text
        )
        return self.client.chat_stream(
            user_message=user_message,
            system_message=self.system_prompt
        )