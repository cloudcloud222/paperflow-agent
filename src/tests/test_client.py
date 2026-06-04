from src.llm.client import DeepSeekClient

client = DeepSeekClient()
result = client.chat("请只回答：客户端封装成功")
print(result)