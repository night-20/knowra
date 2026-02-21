import httpx
import time
from typing import List, Dict, Generator, Any
from openai import OpenAI, APIError
from src.config.settings import settings
from src.config.constants import DEFAULT_SETTINGS
from src.utils.security import get_api_key
from loguru import logger

class LLMClient:
    def __init__(self):
        self.provider = settings.get("llm", "provider", DEFAULT_SETTINGS["llm"]["provider"])
        self.base_url = settings.get("llm", "base_url", DEFAULT_SETTINGS["llm"]["base_url"])
        self.model_name = settings.get("llm", "model", DEFAULT_SETTINGS["llm"]["model"])
        self.temperature = settings.get("llm", "temperature", DEFAULT_SETTINGS["llm"]["temperature"])
        self.max_tokens = settings.get("llm", "max_tokens", DEFAULT_SETTINGS["llm"]["max_tokens"])
        
        # 统一强制 Ollama base url 带 /v1 后缀以兼容 openai 接口
        if self.provider == "ollama" and not self.base_url.endswith("/v1"):
            self.base_url = self.base_url.rstrip("/") + "/v1"
            
        # 从凭据管理器获取 key，本地 Ollama 可以任意
        api_key = get_api_key(self.provider)
        if not api_key:
            if self.provider == "ollama":
                api_key = "ollama"
            else:
                logger.warning(f"No API key found for provider {self.provider}. Requests may fail.")
                api_key = "dummy"

        http_client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(60.0, connect=10.0)
        )
        
        # 内置三次重试，OpenAI SDK 默认 exponential backoff
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.base_url,
            http_client=http_client,
            max_retries=3
        )
        
    def chat_stream(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """向模型发起对话请求，并返回流式生成器"""
        try:
            logger.info(f"Sending stream request to {self.model_name} at {self.base_url}")
            # 调用 openai SDK 的流式接口
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except APIError as e:
            logger.error(f"OpenAI API error when calling chat_stream: {e}")
            yield f"\n[AI 请求失败] API 错误: {e}"
        except Exception as e:
            logger.error(f"Unexpected error in chat_stream: {e}")
            yield f"\n[AI 请求发生意外错误] {e}"

    def chat_sync(self, messages: List[Dict[str, str]]) -> str:
        """同步非流式聊天（某些提取 Agent 用到）"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=False
            )
            if response.choices:
                return response.choices[0].message.content or ""
            return ""
        except APIError as e:
            logger.error(f"OpenAI API error when calling chat_sync: {e}")
            return f"[AI 请求失败] API 错误: {e}"
        except Exception as e:
            logger.error(f"Unexpected error in chat_sync: {e}")
            return f"[AI 请求发生意外错误] {e}"
