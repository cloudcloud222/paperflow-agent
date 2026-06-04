from src.llm.client import DeepSeekClient
from src.utils.prompt_loader import load_prompt


class LiteratureSummarizer:
    def __init__(self):
        self.client = DeepSeekClient(component_name="literature_summarizer")
        self.system_prompt = load_prompt("literature_summarizer.txt")

    def get_model_name(self) -> str:
            return self.client.model_name

    def summarize(self, filename: str, content: str) -> str:
        user_message = f"""下面是论文文件名：{filename}

下面是论文文本内容：
{content}
"""
        return self.client.chat(
            user_message=user_message,
            system_message=self.system_prompt
        )

    def summarize_stream(self, filename: str, content: str) -> str:
        user_message = f"""下面是论文文件名：{filename}

下面是论文文本内容：
{content}
"""
        return self.client.chat_stream(
            user_message=user_message,
            system_message=self.system_prompt
        )