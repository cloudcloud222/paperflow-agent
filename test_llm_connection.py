import os
import traceback
import httpx
from openai import OpenAI

api_key = (os.getenv("DEEPSEEK_API_KEY") or "").strip()
if not api_key:
    raise RuntimeError("DEEPSEEK_API_KEY is not set.")

base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
proxy = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")

print("Base URL:", base_url)
print("Model:", model)
print("Key length:", len(api_key))
print("HTTP_PROXY:", os.getenv("HTTP_PROXY"))
print("HTTPS_PROXY:", os.getenv("HTTPS_PROXY"))

try:
    http_client = httpx.Client(proxy=proxy, timeout=60) if proxy else httpx.Client(timeout=60)

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=60,
        max_retries=0,
        http_client=http_client,
    )

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": "请回复：连接测试成功。"}
        ],
        temperature=0.2,
        max_tokens=50,
        stream=False,
    )

    print("连接成功：")
    print(resp.choices[0].message.content)

except Exception as e:
    print("连接失败：")
    print(type(e).__name__)
    print(repr(e))
    print("\n完整堆栈：")
    traceback.print_exc()
