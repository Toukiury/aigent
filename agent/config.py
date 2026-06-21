"""模型与模板配置"""

from __future__ import annotations

import os

MODEL_PRESETS = {
    "deepseek": {
        "name": "DeepSeek Chat",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "description": "默认推荐，性价比高，OpenAI 兼容",
    },
    "qwen": {
        "name": "通义千问 Qwen-Plus",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
        "description": "阿里云 DashScope，国内稳定",
    },
    "doubao": {
        "name": "豆包（火山方舟）",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model": "doubao-pro-32k",
        "description": "需在 .env 中将 LLM_MODEL 改为你的 endpoint_id",
    },
}

PROMPT_TEMPLATES = {
    "CO-STAR": {
        "label": "CO-STAR（通用推荐）",
        "sections": ["Context 背景", "Objective 目标", "Style 风格", "Tone 语气", "Audience 受众", "Response 输出格式"],
    },
    "CRISPE": {
        "label": "CRISPE（角色 + 能力）",
        "sections": ["Capacity 角色", "Role 任务", "Insight 背景", "Statement 陈述", "Personality 风格", "Experiment 输出"],
    },
    "RISEN": {
        "label": "RISEN（步骤化任务）",
        "sections": ["Role 角色", "Input 输入", "Steps 步骤", "Expectation 期望", "Narrowing 约束"],
    },
}


def get_active_model_info() -> dict[str, str]:
    preset_key = os.getenv("LLM_PRESET", "deepseek")
    preset = MODEL_PRESETS.get(preset_key, MODEL_PRESETS["deepseek"])
    return {
        "preset": preset_key,
        "name": preset["name"],
        "model": os.getenv("LLM_MODEL", preset["model"]),
        "base_url": os.getenv("LLM_BASE_URL", preset["base_url"]),
        "description": preset["description"],
    }
