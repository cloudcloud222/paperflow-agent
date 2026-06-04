import os
from typing import Optional

import httpx
from dotenv import load_dotenv
from openai import OpenAI
from src.utils.config_loader import ConfigLoader


class DeepSeekClient:
    """Small OpenAI-compatible client wrapper used by Paper-Agent.

    The class name is kept for backward compatibility with existing workflow
    modules, but the implementation is provider-agnostic enough for DeepSeek
    and other OpenAI-compatible endpoints.
    """

    def __init__(self, component_name: str = "writer"):
        # Do not override environment variables already set in the shell. This
        # lets users temporarily switch API keys or proxies without editing .env.
        load_dotenv(override=False)

        self.component_name = component_name
        self.config_loader = ConfigLoader()

        models_config = self.config_loader.load_models_config()
        default_provider = (models_config.get("default_provider") or "deepseek").strip()
        routing = models_config.get("routing", {})
        providers = models_config.get("providers", {})

        self.provider_name = (routing.get(component_name) or default_provider).strip()
        if self.provider_name not in providers:
            raise ValueError(f"模型 Provider 不存在: {self.provider_name}")

        provider_config = providers[self.provider_name]
        self.base_url = (provider_config.get("base_url") or "").strip()
        self.api_key_env = (provider_config.get("api_key_env") or "").strip()
        self.model_name = (provider_config.get("chat_model") or "").strip()
        self.timeout = int(provider_config.get("timeout", 60) or 60)
        self.max_retries = int(provider_config.get("max_retries", 1) or 1)

        if not self.base_url:
            raise ValueError(f"Provider {self.provider_name} 缺少 base_url")
        if not self.api_key_env:
            raise ValueError(f"Provider {self.provider_name} 缺少 api_key_env")
        if not self.model_name:
            raise ValueError(f"Provider {self.provider_name} 缺少 chat_model")

        api_key = (os.getenv(self.api_key_env) or "").strip()
        if not api_key:
            raise ValueError(f"环境变量未设置或为空: {self.api_key_env}")

        proxy = self._detect_proxy()
        http_client = httpx.Client(proxy=proxy, timeout=self.timeout) if proxy else httpx.Client(timeout=self.timeout)

        self.client = OpenAI(
            api_key=api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=self.max_retries,
            http_client=http_client,
        )

    @staticmethod
    def _detect_proxy() -> Optional[str]:
        """Return the current HTTP(S) proxy, if one is configured.

        httpx/OpenAI may read proxy variables automatically in some setups, but
        explicitly passing the proxy makes behavior more predictable on Windows
        when using Clash/Mihomo.
        """
        proxy = (
            os.getenv("HTTPS_PROXY")
            or os.getenv("https_proxy")
            or os.getenv("HTTP_PROXY")
            or os.getenv("http_proxy")
            or ""
        ).strip()
        return proxy or None

    def get_model_info(self) -> dict:
        return {
            "provider": self.provider_name,
            "component": self.component_name,
            "base_url": self.base_url,
            "api_key_env": self.api_key_env,
            "model": self.model_name,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "proxy": self._detect_proxy() or "",
        }

    def chat(self, user_message: str, system_message: str = "你是一个简洁的助手。") -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            stream=False,
        )
        return response.choices[0].message.content or ""

    def chat_stream(self, user_message: str, system_message: str = "你是一个简洁的助手。") -> str:
        stream = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            stream=True,
        )

        full_text = ""
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                print(content, end="", flush=True)
                full_text += content

        print()
        return full_text
