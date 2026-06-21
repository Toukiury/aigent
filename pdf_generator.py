"""求解过程 PDF 报告生成"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from agent.models import OptimizationResult

# 注册中文字体（ReportLab 内置 CID 字体，无需额外字体文件）
pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="STSong-Light",
            fontSize=20,
            leading=28,
            spaceAfter=12,
        ),
        "heading": ParagraphStyle(
            "Heading",
            parent=base["Heading2"],
            fontName="STSong-Light",
            fontSize=14,
            leading=20,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.HexColor("#1a56db"),
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontName="STSong-Light",
            fontSize=10,
            leading=16,
            spaceAfter=6,
        ),
        "mono": ParagraphStyle(
            "Mono",
            parent=base["Code"],
            fontName="STSong-Light",
            fontSize=9,
            leading=14,
            leftIndent=12,
            backColor=colors.HexColor("#f3f4f6"),
            spaceAfter=8,
        ),
    }


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    safe = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )
    return Paragraph(safe, style)


def _tool_label(tool: str) -> str:
    labels = {
        "analyze_question": "工具：问题诊断 (analyze_question)",
        "rewrite_question": "工具：问题重写 (rewrite_question)",
        "evaluate_quality": "工具：质量评估 (evaluate_quality)",
        "generate_system_prompt": "工具：生成 System Prompt (generate_system_prompt)",
        "suggest_clarifications": "工具：追问建议 (suggest_clarifications)",
        "compare_answers": "工具：优化前后对比 (compare_answers)",
    }
    return labels.get(tool, tool)


SECTION_NUMS = "一二三四五六七八九十"


def _section_title(n: int, title: str) -> str:
    idx = n - 1
    prefix = SECTION_NUMS[idx] if 0 <= idx < len(SECTION_NUMS) else str(n)
    return f"{prefix}、{title}"


def _format_step_output(tool: str, output: dict[str, Any]) -> str:
    if tool == "analyze_question":
        lines = [
            f"意图：{output.get('intent', '')}",
            f"领域：{output.get('domain', '')}",
            f"缺失信息：{', '.join(output.get('missing_info', []))}",
            f"歧义点：{', '.join(output.get('ambiguities', []))}",
        ]
        return "\n".join(lines)
    if tool == "rewrite_question":
        lines = [output.get("optimized_question", "")]
        notes = output.get("optimization_notes", [])
        if notes:
            lines.append("优化说明：")
            lines.extend(f"  - {n}" for n in notes)
        return "\n".join(lines)
    if tool == "evaluate_quality":
        return (
            f"清晰度 {output.get('clarity_score')}/10 | "
            f"完整性 {output.get('completeness_score')}/10 | "
            f"可执行性 {output.get('actionability_score')}/10 | "
            f"综合 {output.get('overall_score')}/10\n"
            f"评价：{output.get('feedback', '')}"
        )
    if tool == "generate_system_prompt":
        return (
            f"System Prompt：{output.get('system_prompt', '')}\n"
            f"设计理由：{output.get('rationale', '')}"
        )
    if tool == "suggest_clarifications":
        qs = output.get("clarifying_questions", [])
        return "追问建议：\n" + "\n".join(f"  - {q}" for q in qs)
    if tool == "compare_answers":
        return (
            f"原始问题回答：{output.get('original_answer', '')}\n"
            f"优化后回答：{output.get('optimized_answer', '')}\n"
            f"对比结论：{output.get('comparison_summary', '')}"
        )
    return str(output)


def generate_pdf(result: OptimizationResult, filename: str | None = None) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if not filename:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"question_optimization_report_{ts}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    s = _styles()
    story: list = []

    story.append(_p("通用问题优化智能体 — 求解过程报告", s["title"]))
    story.append(
        _p(
            f"生成时间：{result.finished_at or datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
            f"求解开始：{result.started_at} | 求解结束：{result.finished_at}<br/>"
            f"使用模型：{result.model_info.get('name', '')} ({result.model_info.get('model', '')})<br/>"
            f"优化模板：{result.template}",
            s["body"],
        )
    )
    story.append(Spacer(1, 0.3 * cm))

    story.append(_p("一、原始问题", s["heading"]))
    story.append(_p(result.original_question, s["mono"]))
    if result.user_context:
        story.append(_p("用户补充背景", s["heading"]))
        story.append(_p(result.user_context, s["mono"]))

    story.append(_p("二、智能体求解过程（工具调用记录）", s["heading"]))
    for step in result.steps:
        tool = step.get("tool", "")
        story.append(_p(f"步骤 {step.get('step', '')} — {_tool_label(tool)}", s["body"]))
        story.append(_p(f"时间：{step.get('timestamp', '')}", s["body"]))
        inp = step.get("input", {})
        if tool == "analyze_question":
            story.append(_p(f"输入：{inp.get('question', '')}", s["body"]))
        elif tool == "rewrite_question":
            story.append(_p("输入：基于诊断结果与选定模板进行重写", s["body"]))
        elif tool == "evaluate_quality":
            story.append(_p("输入：对优化后问题进行质量评估", s["body"]))
        elif tool == "suggest_clarifications":
            story.append(_p("输入：基于诊断结果生成追问建议", s["body"]))
        elif tool == "generate_system_prompt":
            story.append(_p("输入：为优化后问题生成 System Prompt", s["body"]))
        elif tool == "compare_answers":
            story.append(_p("输入：对比原始问题与优化后问题的回答质量", s["body"]))
        out_text = _format_step_output(tool, step.get("output", {}))
        story.append(_p(f"输出：<br/>{out_text}", s["mono"]))
        story.append(Spacer(1, 0.2 * cm))

    story.append(_p("三、最终优化结果", s["heading"]))
    story.append(_p(result.optimized_question, s["mono"]))

    if result.system_prompt:
        story.append(_p("四、推荐 System Prompt", s["heading"]))
        story.append(_p(result.system_prompt, s["mono"]))
        story.append(_p(f"设计理由：{result.system_prompt_rationale}", s["body"]))

    section = 5
    if result.clarifying_questions:
        story.append(_p(_section_title(section, "建议追问"), s["heading"]))
        for i, q in enumerate(result.clarifying_questions, 1):
            story.append(_p(f"{i}. {q}", s["body"]))
        section += 1

    if result.optimization_notes:
        story.append(_p(_section_title(section, "优化说明汇总"), s["heading"]))
        section += 1
        for i, note in enumerate(result.optimization_notes, 1):
            story.append(_p(f"{i}. {note}", s["body"]))

    if result.assumptions:
        story.append(_p(_section_title(section, "合理假设"), s["heading"]))
        section += 1
        for i, item in enumerate(result.assumptions, 1):
            story.append(_p(f"{i}. {item}", s["body"]))

    ev = result.evaluation
    story.append(_p(_section_title(section, "质量评估"), s["heading"]))
    section += 1
    score_data = [
        ["维度", "得分"],
        ["清晰度", f"{ev.get('clarity_score', '-')}/10"],
        ["完整性", f"{ev.get('completeness_score', '-')}/10"],
        ["可执行性", f"{ev.get('actionability_score', '-')}/10"],
        ["综合评分", f"{ev.get('overall_score', '-')}/10"],
    ]
    table = Table(score_data, colWidths=[6 * cm, 4 * cm])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a56db")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.2 * cm))
    story.append(_p(f"评价：{ev.get('feedback', '')}", s["body"]))

    if result.comparison:
        story.append(_p(_section_title(section, "优化前后回答对比"), s["heading"]))
        cmp = result.comparison
        story.append(_p(f"原始问题回答：{cmp.get('original_answer', '')}", s["body"]))
        story.append(_p(f"优化后问题回答：{cmp.get('optimized_answer', '')}", s["body"]))
        story.append(_p(f"对比结论：{cmp.get('comparison_summary', '')}", s["body"]))
        section += 1

    story.append(_p(_section_title(section, "技术说明"), s["heading"]))
    story.append(
        _p(
            "本报告由「通用问题优化智能体」自动生成。"
            f"使用模型：{result.model_info.get('name', '')} ({result.model_info.get('model', '')})。"
            "智能体基于公开大模型 API，通过提示词工程与 6 个轻量工具调用"
            "（analyze_question → suggest_clarifications → rewrite_question → "
            "evaluate_quality → generate_system_prompt → compare_answers）"
            "完成问题优化求解，并记录完整过程。",
            s["body"],
        )
    )

    doc.build(story)
    return filepath
