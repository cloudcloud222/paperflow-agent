from src.llm.client import DeepSeekClient
from src.utils.prompt_loader import load_prompt


class RelatedWorkPolisher:
    def __init__(self):
        self.client = DeepSeekClient(component_name="related_work_polisher")
        self.system_prompt = load_prompt("related_work_polisher.txt")

    def get_model_name(self) -> str:
        return self.client.model_name

    def polish_related_work(
        self,
        topic: str,
        goal: str,
        related_work_text: str,
        literature_pack_text: str = "",
        outline_review_text: str = "",
        introduction_text: str = ""
    ) -> str:
        user_message = f"""【论文主题】
{topic}

【当前目标】
{goal}

【相关工作初稿】
{related_work_text}

【文献整理总文档】
{literature_pack_text}

【总纲审查意见】
{outline_review_text}

【已有引言内容】
{introduction_text}
"""
        return self.client.chat(
            user_message=user_message,
            system_message=self.system_prompt
        )

    def polish_related_work_stream(
        self,
        topic: str,
        goal: str,
        related_work_text: str,
        literature_pack_text: str = "",
        outline_review_text: str = "",
        introduction_text: str = ""
    ) -> str:
        user_message = f"""【论文主题】
{topic}

【当前目标】
{goal}

【相关工作初稿】
{related_work_text}

【文献整理总文档】
{literature_pack_text}

【总纲审查意见】
{outline_review_text}

【已有引言内容】
{introduction_text}
"""
        return self.client.chat_stream(
            user_message=user_message,
            system_message=self.system_prompt
        )