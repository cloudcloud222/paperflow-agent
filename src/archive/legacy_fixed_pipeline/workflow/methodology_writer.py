from src.llm.client import DeepSeekClient
from src.utils.prompt_loader import load_prompt


class MethodologyWriter:
    def __init__(self):
        self.client = DeepSeekClient(component_name="methodology_writer")
        self.system_prompt = load_prompt("methodology_writer.txt")

    def get_model_name(self) -> str:
        return self.client.model_name

    def write_methodology(
        self,
        topic: str,
        goal: str,
        literature_pack_text: str,
        outline_text: str,
        outline_review_text: str,
        introduction_text: str = "",
        related_work_text: str = ""
    ) -> str:
        user_message = f"""【论文主题】
{topic}

【当前目标】
{goal}

【文献整理总文档】
{literature_pack_text}

【论文总纲】
{outline_text}

【总纲审查意见】
{outline_review_text}

【已有引言内容】
{introduction_text}

【已有相关工作内容】
{related_work_text}
"""
        return self.client.chat(
            user_message=user_message,
            system_message=self.system_prompt
        )

    def write_methodology_stream(
        self,
        topic: str,
        goal: str,
        literature_pack_text: str,
        outline_text: str,
        outline_review_text: str,
        introduction_text: str = "",
        related_work_text: str = ""
    ) -> str:
        user_message = f"""【论文主题】
{topic}

【当前目标】
{goal}

【文献整理总文档】
{literature_pack_text}

【论文总纲】
{outline_text}

【总纲审查意见】
{outline_review_text}

【已有引言内容】
{introduction_text}

【已有相关工作内容】
{related_work_text}
"""
        return self.client.chat_stream(
            user_message=user_message,
            system_message=self.system_prompt
        )