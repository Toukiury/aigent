"""Web 界面格式化工具"""

from __future__ import annotations

import html
import json
from typing import Any

from agent.models import StreamState

TOOL_META = {
    "analyze_question": {"label": "问题诊断", "icon": "🔍", "order": 1},
    "suggest_clarifications": {"label": "追问建议", "icon": "❓", "order": 2},
    "rewrite_question": {"label": "问题重写", "icon": "✏️", "order": 3},
    "evaluate_quality": {"label": "质量评估", "icon": "📊", "order": 4},
    "generate_system_prompt": {"label": "System Prompt", "icon": "⚙️", "order": 5},
    "compare_answers": {"label": "优化前后对比", "icon": "⚖️", "order": 6},
}

# 内联样式（避免 Gradio 主题把文字洗浅）
S_TITLE = "color:#0f172a;font-weight:800;font-size:1rem;"
S_TOOL = "color:#1e293b;font-weight:700;font-size:0.75rem;background:#cbd5e1;padding:2px 8px;border-radius:4px;font-family:monospace;"
S_TIME = "color:#334155;font-weight:600;font-size:0.8rem;margin-bottom:8px;"
S_BODY = "color:#111827;font-weight:600;font-size:0.92rem;line-height:1.7;"
S_LABEL = "color:#0f172a;font-weight:800;"
S_TEXT = "color:#1e293b;font-weight:600;"
S_LIST = "color:#1e293b;font-weight:600;margin:5px 0;"
S_CODE = (
    "background:#1e293b;color:#f8fafc;padding:10px;border-radius:6px;"
    "white-space:pre-wrap;word-break:break-word;font-size:0.88rem;font-weight:500;"
)
S_CARD = (
    "border-left:4px solid #2563eb;padding:14px 16px;margin:10px 0;"
    "background:#ffffff;border-radius:0 10px 10px 0;border:1px solid #cbd5e1;"
    "border-left-width:4px;"
)
S_BADGE_DONE = "background:#166534;color:#ffffff;font-weight:700;font-size:0.75rem;padding:2px 8px;border-radius:4px;"
S_BADGE_RUN = "background:#b45309;color:#ffffff;font-weight:700;font-size:0.75rem;padding:2px 8px;border-radius:4px;"
S_STATUS_DONE = "background:#dcfce7;color:#14532d;border:2px solid #16a34a;font-weight:700;"
S_STATUS_RUN = "background:#fef3c7;color:#92400e;border:2px solid #f59e0b;font-weight:700;"


def _esc(text: str) -> str:
    return html.escape(str(text))


def render_comparison_html(comparison: dict[str, Any], compact: bool = False) -> str:
    """渲染优化前后对比（深色高对比，内联样式）"""
    if not comparison:
        return "<p style='color:#111;font-weight:700;'>等待对比结果...</p>"

    fs = "0.84rem" if compact else "0.95rem"
    weaknesses = comparison.get("original_weaknesses", [])
    strengths = comparison.get("optimized_strengths", [])
    weak_items = "".join(
        f"<li style='color:#fecaca;font-weight:600;margin:4px 0;'>{_esc(w)}</li>"
        for w in weaknesses
    ) or "<li style='color:#fecaca;font-weight:600;'>过于笼统</li>"
    strong_items = "".join(
        f"<li style='color:#bbf7d0;font-weight:600;margin:4px 0;'>{_esc(s)}</li>"
        for s in strengths
    ) or "<li style='color:#bbf7d0;font-weight:600;'>更具体可执行</li>"

    return f"""
    <div style="margin-top:6px;color:#111;">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;">
        <div style="background:#1a0a0a;border:2px solid #dc2626;border-radius:8px;padding:12px 14px;">
          <div style="color:#fca5a5;font-weight:800;font-size:{fs};margin-bottom:8px;">
            ❌ 原始模糊问题 → 大模型回答
          </div>
          <div style="color:#ffffff;font-weight:600;font-size:{fs};line-height:1.7;">
            {_esc(comparison.get('original_answer', ''))}
          </div>
        </div>
        <div style="background:#0a1f14;border:2px solid #16a34a;border-radius:8px;padding:12px 14px;">
          <div style="color:#86efac;font-weight:800;font-size:{fs};margin-bottom:8px;">
            ✅ 优化后问题 → 大模型回答
          </div>
          <div style="color:#ffffff;font-weight:600;font-size:{fs};line-height:1.7;">
            {_esc(comparison.get('optimized_answer', ''))}
          </div>
        </div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;">
        <div style="background:#2b1212;border:2px solid #ef4444;border-radius:8px;padding:10px 14px;">
          <div style="color:#f87171;font-weight:800;font-size:{fs};margin-bottom:6px;">原始回答的问题</div>
          <ul style="margin:0;padding-left:18px;">{weak_items}</ul>
        </div>
        <div style="background:#0f2e1c;border:2px solid #22c55e;border-radius:8px;padding:10px 14px;">
          <div style="color:#4ade80;font-weight:800;font-size:{fs};margin-bottom:6px;">优化后回答的优势</div>
          <ul style="margin:0;padding-left:18px;">{strong_items}</ul>
        </div>
      </div>
      <div style="background:#0f172a;border:2px solid #3b82f6;border-radius:8px;padding:12px 14px;">
        <span style="color:#93c5fd;font-weight:800;font-size:{fs};">对比结论：</span>
        <span style="color:#f1f5f9;font-weight:600;font-size:{fs};line-height:1.7;">
          {_esc(comparison.get('comparison_summary', ''))}
        </span>
      </div>
    </div>
    """


def _format_step_detail(tool: str, output: dict[str, Any]) -> str:
    if tool == "analyze_question":
        return (
            f"<div style='{S_BODY}'>"
            f"<span style='{S_LABEL}'>意图</span>："
            f"<span style='{S_TEXT}'>{_esc(output.get('intent', ''))}</span><br>"
            f"<span style='{S_LABEL}'>领域</span>："
            f"<span style='{S_TEXT}'>{_esc(output.get('domain', ''))}</span><br>"
            f"<span style='{S_LABEL}'>缺失信息</span>："
            f"<span style='{S_TEXT}'>{_esc(', '.join(output.get('missing_info', [])))}</span><br>"
            f"<span style='{S_LABEL}'>歧义点</span>："
            f"<span style='{S_TEXT}'>{_esc(', '.join(output.get('ambiguities', [])))}</span>"
            f"</div>"
        )
    if tool == "suggest_clarifications":
        qs = output.get("clarifying_questions", [])
        items = "".join(
            f"<li style='{S_LIST}'>{_esc(q)}</li>" for q in qs
        )
        return f"<ul style='margin:0;padding-left:20px;'>{items}</ul>"
    if tool == "rewrite_question":
        notes = output.get("optimization_notes", [])
        note_html = "".join(f"<li style='{S_LIST}'>{_esc(n)}</li>" for n in notes)
        preview = _esc(output.get("optimized_question", ""))[:300]
        suffix = "..." if len(output.get("optimized_question", "")) > 300 else ""
        return (
            f"<div style='{S_BODY}'>"
            f"<div style='{S_LABEL}margin-bottom:6px;'>优化后预览</div>"
            f"<pre style='{S_CODE}'>{preview}{suffix}</pre>"
            f"<div style='{S_LABEL}margin:8px 0 6px;'>优化说明</div>"
            f"<ul style='margin:0;padding-left:20px;'>{note_html}</ul>"
            f"</div>"
        )
    if tool == "evaluate_quality":
        ctx = output.get("context_reflection_score", "-")
        return (
            f"<div style='{S_BODY}'>"
            f"<span style='{S_LABEL}'>清晰度</span> "
            f"<span style='{S_TEXT}'>{output.get('clarity_score')}/10</span> · "
            f"<span style='{S_LABEL}'>完整性</span> "
            f"<span style='{S_TEXT}'>{output.get('completeness_score')}/10</span> · "
            f"<span style='{S_LABEL}'>可执行性</span> "
            f"<span style='{S_TEXT}'>{output.get('actionability_score')}/10</span> · "
            f"<span style='{S_LABEL}'>背景融入</span> "
            f"<span style='{S_TEXT}'>{ctx}/10</span> · "
            f"<span style='{S_LABEL}'>综合</span> "
            f"<span style='{S_TEXT}'>{output.get('overall_score')}/10</span><br>"
            f"<span style='{S_TEXT}margin-top:6px;display:inline-block;'>"
            f"{_esc(output.get('feedback', ''))}</span>"
            f"</div>"
        )
    if tool == "generate_system_prompt":
        return (
            f"<div style='{S_BODY}'>"
            f"<pre style='{S_CODE}'>{_esc(output.get('system_prompt', ''))}</pre>"
            f"<span style='{S_TEXT}'>{_esc(output.get('rationale', ''))}</span>"
            f"</div>"
        )
    if tool == "compare_answers":
        return render_comparison_html(output, compact=True)
    return f"<pre style='{S_CODE}'>{_esc(json.dumps(output, ensure_ascii=False, indent=2))}</pre>"


def render_timeline(state: StreamState) -> str:
    """渲染工具调用时间线 HTML"""
    running_tool = state.current_tool
    cards: list[str] = []

    for step in state.steps:
        tool = step.get("tool", "")
        meta = TOOL_META.get(tool, {"label": tool, "icon": "🔧", "order": 0})
        detail = _format_step_detail(tool, step.get("output", {}))
        border_color = "#2563eb" if tool == "compare_answers" else "#16a34a"
        card_style = S_CARD.replace("#2563eb", border_color)

        cards.append(
            f"""
            <div style="{card_style}">
              <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:6px;">
                <span style="{S_BADGE_DONE}">✓ 完成</span>
                <span style="{S_TITLE}">{meta['icon']} 步骤 {step.get('step')} — {meta['label']}</span>
                <span style="{S_TOOL}">{_esc(tool)}</span>
              </div>
              <div style="{S_TIME}">{_esc(step.get('timestamp', ''))}</div>
              <div>{detail}</div>
            </div>
            """
        )

    if running_tool and not state.done:
        meta = TOOL_META.get(running_tool, {"label": running_tool, "icon": "⏳", "order": 0})
        cards.append(
            f"""
            <div style="border-left:4px solid #f59e0b;padding:14px 16px;margin:10px 0;
                        background:#fffbeb;border-radius:0 10px 10px 0;border:1px solid #fcd34d;border-left-width:4px;">
              <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:6px;">
                <span style="{S_BADGE_RUN}">⟳ 执行中</span>
                <span style="{S_TITLE}">{meta['icon']} {meta['label']}</span>
                <span style="{S_TOOL}">{_esc(running_tool)}</span>
              </div>
              <div style="color:#92400e;font-weight:700;font-size:0.92rem;">正在调用大模型，请稍候...</div>
            </div>
            """
        )

    progress = len(state.steps)
    status_style = S_STATUS_DONE if state.done else S_STATUS_RUN
    status_icon = "✅" if state.done else "🔄"

    return f"""
    <div style="font-family:system-ui,sans-serif;">
      <div style="{status_style}padding:12px 16px;border-radius:10px;margin-bottom:16px;
                  display:flex;justify-content:space-between;align-items:center;">
        <span>{status_icon} {_esc(state.status)}</span>
        <span style="font-size:0.85rem;font-weight:700;">已完成 {progress} 步</span>
      </div>
      <div>
        {''.join(cards) if cards else '<p style="color:#111827;font-weight:700;text-align:center;padding:40px 0;">点击「开始优化」后，将在此逐步显示每个工具的调用结果</p>'}
      </div>
    </div>
    """


# 保留空 CSS 占位，Gradio launch 仍引用
TIMELINE_CSS = """
.gradio-container .timeline-wrap, .gradio-container .step-card { color: #111827 !important; }
.gradio-container .step-body, .gradio-container .step-body * { color: #111827 !important; }
.gradio-container b, .gradio-container strong { color: #0f172a !important; font-weight: 800 !important; }
.gradio-container i, .gradio-container em { color: #1e293b !important; font-style: normal !important; }
"""
