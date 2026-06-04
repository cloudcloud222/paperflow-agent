from src.llm.client import DeepSeekClient
from src.utils.prompt_loader import load_prompt


class ConsistencyChecker:
    def __init__(self):
        self.client = DeepSeekClient(component_name="consistency_checker")
        self.system_prompt = load_prompt("consistency_checker.txt")

    def get_model_name(self) -> str:
        return self.client.model_name

    def check_sections(
        self,
        topic: str,
        goal: str,
        outline_text: str,
        outline_review_text: str,
        introduction_text: str,
        related_work_text: str,
        methodology_text: str,
        experiment_text: str,
        conclusion_text: str
    ) -> str:
        user_message = f"""【论文主题】
{topic}

【当前目标】
{goal}

【论文总纲】
{outline_text}

【总纲审查意见】
{outline_review_text}

【引言章节】
{introduction_text}

【相关工作章节】
{related_work_text}

【方法章节】
{methodology_text}

【实验章节】
{experiment_text}

【结论章节】
{conclusion_text}
"""
        return self.client.chat(
            user_message=user_message,
            system_message=self.system_prompt
        )

    def check_sections_stream(
        self,
        topic: str,
        goal: str,
        outline_text: str,
        outline_review_text: str,
        introduction_text: str,
        related_work_text: str,
        methodology_text: str,
        experiment_text: str,
        conclusion_text: str
    ) -> str:
        user_message = f"""【论文主题】
{topic}

【当前目标】
{goal}

【论文总纲】
{outline_text}

【总纲审查意见】
{outline_review_text}

【引言章节】
{introduction_text}

【相关工作章节】
{related_work_text}

【方法章节】
{methodology_text}

【实验章节】
{experiment_text}

【结论章节】
{conclusion_text}
"""
        return self.client.chat_stream(
            user_message=user_message,
            system_message=self.system_prompt
        )