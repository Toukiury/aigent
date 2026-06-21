"""大模型 API 客户端（OpenAI 兼容接口）"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from openai import OpenAI


def get_client() -> OpenAI:
    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "未设置 API Key。请在环境变量中配置 LLM_API_KEY，或复制 .env.example 为 .env 后填写。"
        )
    base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
    return OpenAI(api_key=api_key, base_url=base_url)


def get_model() -> str:
    return os.getenv("LLM_MODEL", "deepseek-chat")


def get_model_display_name() -> str:
    from .config import get_active_model_info

    info = get_active_model_info()
    return f"{info['name']} ({info['model']})"


def _loads_json(text: str) -> dict[str, Any]:
    """解析 JSON，兼容模型返回的多行字符串（未转义换行）"""
    try:
        return json.loads(text, strict=False)
    except json.JSONDecodeError:
        # 去掉可能影响解析的 BOM 与首尾空白
        cleaned = text.strip().lstrip("\ufeff")
        return json.loads(cleaned, strict=False)


def extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
    try:
        return _loads_json(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return _loads_json(match.group())
            except json.JSONDecodeError as e:
                raise ValueError(f"无法解析模型返回的 JSON：{e}") from e
        raise ValueError(f"无法解析模型返回的 JSON：{text[:200]}...")


def chat_completion(system: str, user: str, temperature: float = 0.3) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model=get_model(),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content or ""
