"""数据模型"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OptimizationResult:
    original_question: str
    optimized_question: str
    optimization_notes: list[str]
    assumptions: list[str]
    analysis: dict[str, Any]
    evaluation: dict[str, Any]
    steps: list[dict[str, Any]] = field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""
    template: str = "CO-STAR"
    user_context: str = ""
    model_info: dict[str, str] = field(default_factory=dict)
    system_prompt: str = ""
    system_prompt_rationale: str = ""
    clarifying_questions: list[str] = field(default_factory=list)
    comparison: dict[str, Any] = field(default_factory=dict)

    def to_markdown(self) -> str:
        lines = [f"## 原始问题\n\n{self.original_question}\n"]
        if self.user_context:
            lines.extend([f"## 用户补充背景\n\n{self.user_context}\n"])
        lines.extend(
            [
                "## 问题诊断\n",
                f"- **意图**：{self.analysis.get('intent', '')}",
                f"- **领域**：{self.analysis.get('domain', '')}",
                f"- **缺失信息**：{', '.join(self.analysis.get('missing_info', [])) or '无'}",
                f"- **歧义点**：{', '.join(self.analysis.get('ambiguities', [])) or '无'}",
                f"- **使用模板**：{self.template}",
                "\n## 优化后问题\n",
                self.optimized_question,
                "\n## 优化说明\n",
            ]
        )
        for i, note in enumerate(self.optimization_notes, 1):
            lines.append(f"{i}. {note}")

        if self.assumptions:
            lines.append("\n## 合理假设\n")
            for i, item in enumerate(self.assumptions, 1):
                lines.append(f"{i}. {item}")

        if self.clarifying_questions:
            lines.append("\n## 建议追问\n")
            for i, q in enumerate(self.clarifying_questions, 1):
                lines.append(f"{i}. {q}")

        if self.system_prompt:
            lines.extend(
                [
                    "\n## 推荐 System Prompt\n",
                    self.system_prompt,
                    f"\n*设计理由：{self.system_prompt_rationale}*",
                ]
            )

        ev = self.evaluation
        lines.extend(
            [
                "\n## 质量评估\n",
                f"- 清晰度：{ev.get('clarity_score', '-')}/10",
                f"- 完整性：{ev.get('completeness_score', '-')}/10",
                f"- 可执行性：{ev.get('actionability_score', '-')}/10",
                f"- 综合评分：{ev.get('overall_score', '-')}/10",
                f"- 评价：{ev.get('feedback', '')}",
            ]
        )

        if self.comparison:
            lines.extend(
                [
                    "\n## 优化前后回答对比\n",
                    f"**原始问题回答：**\n{self.comparison.get('original_answer', '')}\n",
                    f"**优化后问题回答：**\n{self.comparison.get('optimized_answer', '')}\n",
                    f"**对比结论：** {self.comparison.get('comparison_summary', '')}",
                ]
            )

        if self.model_info:
            lines.append(
                f"\n---\n*使用模型：{self.model_info.get('name', '')} "
                f"({self.model_info.get('model', '')})*"
            )
        return "\n".join(lines)


@dataclass
class StreamState:
    """流式执行中间状态"""

    steps: list[dict[str, Any]] = field(default_factory=list)
    status: str = "准备开始..."
    current_tool: str = ""
    optimized_question: str = ""
    optimization_notes: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    analysis: dict[str, Any] = field(default_factory=dict)
    evaluation: dict[str, Any] = field(default_factory=dict)
    system_prompt: str = ""
    system_prompt_rationale: str = ""
    clarifying_questions: list[str] = field(default_factory=list)
    comparison: dict[str, Any] = field(default_factory=dict)
    done: bool = False
    result: OptimizationResult | None = None
