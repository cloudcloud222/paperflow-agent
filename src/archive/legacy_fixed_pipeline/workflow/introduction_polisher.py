from src.llm.client import DeepSeekClient
from src.utils.prompt_loader import load_prompt


class IntroductionPolisher:
    def __init__(self):
        self.client = DeepSeekClient(component_name="introduction_polisher")
        self.system_prompt = load_prompt("introduction_polisher.txt")

    def get_model_name(self) -> str:
        return self.client.model_name

    def polish_introduction(
        self,
        topic: str,
        goal: str,
        introduction_text: str,
        outline_review_text: str = ""
    ) -> str:
        user_message = f"""【论文主题】
{topic}

【当前目标】
{goal}

【引言初稿】
{introduction_text}

【总纲审查意见】
{outline_review_text}
"""
        return self.client.chat(
            user_message=user_message,
            system_message=self.system_prompt
        )

    def polish_introduction_stream(
        self,
        topic: str,
        goal: str,
        introduction_text: str,
        outline_review_text: str = ""
    ) -> str:
        user_message = f"""【论文主题】
{topic}

【当前目标】
{goal}

【引言初稿】
{introduction_text}

【总纲审查意见】
{outline_review_text}
"""
        return self.client.chat_stream(
            user_message=user_message,
            system_message=self.system_prompt
        )