"""轻量工具：分析、重写、评估、System Prompt、对比演示"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from .llm_client import chat_completion, extract_json
from .prompts import (
    ANALYZE_PROMPT,
    CLARIFY_PROMPT,
    COMPARE_ANSWER_PROMPT,
    EVALUATE_PROMPT,
    REWRITE_PROMPT,
    REWRITE_WITH_FEEDBACK_PROMPT,
    SYSTEM_PROMPT,
    SYSTEM_PROMPT_GEN,
    template_hint,
)

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "analyze_question",
            "description": "分析用户问题的意图、缺失信息与歧义点",
            "parameters": {
                "type": "object",
                "properties": {"question": {"type": "string"}},
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rewrite_question",
            "description": "根据诊断结果将问题重写为结构化高质量 Prompt",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "analysis": {"type": "object"},
                    "template": {"type": "string"},
                },
                "required": ["question", "analysis"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "evaluate_quality",
            "description": "评估优化后问题的清晰度、完整性与可执行性",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "optimized": {"type": "string"},
                },
                "required": ["question", "optimized"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_system_prompt",
            "description": "为优化后问题生成推荐的 System Prompt",
            "parameters": {
                "type": "object",
                "properties": {"optimized": {"type": "string"}},
                "required": ["optimized"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_clarifications",
            "description": "生成追问建议，帮助用户补充缺失信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "analysis": {"type": "object"},
                },
                "required": ["question", "analysis"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_answers",
            "description": "对比原始问题与优化后问题的回答质量差异",
            "parameters": {
                "type": "object",
                "properties": {
                    "original": {"type": "string"},
                    "optimized": {"type": "string"},
                },
                "required": ["original", "optimized"],
            },
        },
    },
]


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _context_block(user_context: str | None, required: bool = False) -> str:
    if user_context and user_context.strip():
        return (
            f"【用户补充背景（必须融入优化结果）】：{user_context.strip()}\n"
            "注意：此背景不是可选项，优化后的 Prompt 必须明确体现上述场景。"
        )
    if required:
        return "（用户未提供补充背景）"
    return "（用户未提供补充背景）"


def analyze_question(
    question: str, user_context: str | None = None
) -> tuple[dict[str, Any], dict[str, Any]]:
    prompt = ANALYZE_PROMPT.format(
        question=question,
        user_context_block=_context_block(user_context),
    )
    raw = chat_completion(SYSTEM_PROMPT, prompt)
    result = extract_json(raw)
    log = {
        "tool": "analyze_question",
        "timestamp": _timestamp(),
        "input": {"question": question, "user_context": user_context},
        "output": result,
    }
    return result, log


def rewrite_question(
    question: str,
    analysis: dict[str, Any],
    template: str = "CO-STAR",
    user_context: str | None = None,
    feedback: str | None = None,
    previous: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    analysis_text = json.dumps(analysis, ensure_ascii=False, indent=2)
    ctx = _context_block(user_context)
    hint = template_hint(template)

    if feedback and previous:
        prompt = REWRITE_WITH_FEEDBACK_PROMPT.format(
            question=question,
            user_context_block=ctx,
            optimized=previous,
            feedback=feedback,
            analysis=analysis_text,
            template_hint=hint,
        )
    else:
        prompt = REWRITE_PROMPT.format(
            question=question,
            user_context_block=ctx,
            analysis=analysis_text,
            template_hint=hint,
        )

    raw = chat_completion(SYSTEM_PROMPT, prompt)
    result = extract_json(raw)
    log = {
        "tool": "rewrite_question",
        "timestamp": _timestamp(),
        "input": {
            "question": question,
            "analysis": analysis,
            "template": template,
            "user_context": user_context,
            "feedback": feedback,
            "previous": previous,
        },
        "output": result,
    }
    return result, log


def evaluate_quality(
    question: str, optimized: str, user_context: str | None = None
) -> tuple[dict[str, Any], dict[str, Any]]:
    prompt = EVALUATE_PROMPT.format(
        question=question,
        optimized=optimized,
        user_context_block=_context_block(user_context),
    )
    raw = chat_completion(SYSTEM_PROMPT, prompt)
    result = extract_json(raw)
    log = {
        "tool": "evaluate_quality",
        "timestamp": _timestamp(),
        "input": {"question": question, "optimized": optimized, "user_context": user_context},
        "output": result,
    }
    return result, log


def generate_system_prompt(optimized: str) -> tuple[dict[str, Any], dict[str, Any]]:
    prompt = SYSTEM_PROMPT_GEN.format(optimized=optimized)
    raw = chat_completion(SYSTEM_PROMPT, prompt)
    result = extract_json(raw)
    log = {
        "tool": "generate_system_prompt",
        "timestamp": _timestamp(),
        "input": {"optimized": optimized},
        "output": result,
    }
    return result, log


def suggest_clarifications(
    question: str, analysis: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    prompt = CLARIFY_PROMPT.format(
        question=question,
        analysis=json.dumps(analysis, ensure_ascii=False, indent=2),
    )
    raw = chat_completion(SYSTEM_PROMPT, prompt)
    result = extract_json(raw)
    log = {
        "tool": "suggest_clarifications",
        "timestamp": _timestamp(),
        "input": {"question": question, "analysis": analysis},
        "output": result,
    }
    return result, log


def compare_answers(
    original: str, optimized: str, user_context: str | None = None
) -> tuple[dict[str, Any], dict[str, Any]]:
    prompt = COMPARE_ANSWER_PROMPT.format(
        original=original,
        optimized=optimized,
        user_context_block=_context_block(user_context),
    )
    raw = chat_completion(SYSTEM_PROMPT, prompt, temperature=0.7)
    result = extract_json(raw)
    log = {
        "tool": "compare_answers",
        "timestamp": _timestamp(),
        "input": {"original": original, "optimized": optimized, "user_context": user_context},
        "output": result,
    }
    return result, log
