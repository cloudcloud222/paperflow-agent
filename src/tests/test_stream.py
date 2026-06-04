from src.llm.client import DeepSeekClient

client = DeepSeekClient()

result = client.chat_stream("请用100字左右介绍一下什么是论文写作辅助agent平台。")

print("\n\n=== 最终完整结果 ===")
print(result)