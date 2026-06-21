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


def _esc(text: str) -> str:
    return html.escape(str(text))


def render_comparison_html(comparison: dict[str, Any], compact: bool = False) -> str:
    """渲染优化前后对比（深色高对比，内联样式避免被 Gradio 主题覆盖）"""
    if not comparison:
        return "<p style='color:#111;font-weight:600;'>等待对比结果...</p>"

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
            f"<b>意图</b>：{_esc(output.get('intent', ''))}<br>"
            f"<b>领域</b>：{_esc(output.get('domain', ''))}<br>"
            f"<b>缺失信息</b>：{_esc(', '.join(output.get('missing_info', [])))}<br>"
            f"<b>歧义点</b>：{_esc(', '.join(output.get('ambiguities', [])))}"
        )
    if tool == "suggest_clarifications":
        qs = output.get("clarifying_questions", [])
        items = "".join(f"<li>{_esc(q)}</li>" for q in qs)
        return f"<ul>{items}</ul>"
    if tool == "rewrite_question":
        notes = output.get("optimization_notes", [])
        note_html = "".join(f"<li>{_esc(n)}</li>" for n in notes)
        preview = _esc(output.get("optimized_question", ""))[:300]
        suffix = "..." if len(output.get("optimized_question", "")) > 300 else ""
        return (
            f"<b>优化后预览</b>：<pre class='code-block'>{preview}{suffix}</pre>"
            f"<b>优化说明</b>：<ul>{note_html}</ul>"
        )
    if tool == "evaluate_quality":
        return (
            f"清晰度 <b>{output.get('clarity_score')}</b>/10 · "
            f"完整性 <b>{output.get('completeness_score')}</b>/10 · "
            f"可执行性 <b>{output.get('actionability_score')}</b>/10 · "
            f"综合 <b>{output.get('overall_score')}</b>/10<br>"
            f"<i>{_esc(output.get('feedback', ''))}</i>"
        )
    if tool == "generate_system_prompt":
        return (
            f"<pre class='code-block'>{_esc(output.get('system_prompt', ''))}</pre>"
            f"<i>{_esc(output.get('rationale', ''))}</i>"
        )
    if tool == "compare_answers":
        return render_comparison_html(output, compact=True)
    return f"<pre>{_esc(json.dumps(output, ensure_ascii=False, indent=2))}</pre>"


def render_timeline(state: StreamState) -> str:
    """渲染工具调用时间线 HTML"""
    completed_tools = {s.get("tool") for s in state.steps}
    running_tool = state.current_tool

    cards: list[str] = []
    for step in state.steps:
        tool = step.get("tool", "")
        meta = TOOL_META.get(tool, {"label": tool, "icon": "🔧", "order": 0})
        detail = _format_step_detail(tool, step.get("output", {}))
        card_cls = "step-card step-done"
        if tool == "compare_answers":
            card_cls = "step-card step-done step-compare"
        cards.append(
            f"""
            <div class="{card_cls}">
              <div class="step-header">
                <span class="step-badge done">✓ 完成</span>
                <span class="step-title">{meta['icon']} 步骤 {step.get('step')} — {meta['label']}</span>
                <span class="step-tool">{_esc(tool)}</span>
              </div>
              <div class="step-time">{_esc(step.get('timestamp', ''))}</div>
              <div class="step-body step-body-compare">{detail}</div>
            </div>
            """
        )

    if running_tool and not state.done:
        meta = TOOL_META.get(running_tool, {"label": running_tool, "icon": "⏳", "order": 0})
        cards.append(
            f"""
            <div class="step-card step-running">
              <div class="step-header">
                <span class="step-badge running">⟳ 执行中</span>
                <span class="step-title">{meta['icon']} {meta['label']}</span>
                <span class="step-tool">{_esc(running_tool)}</span>
              </div>
              <div class="step-body pulse">正在调用大模型，请稍候...</div>
            </div>
            """
        )

    progress = len(state.steps)
    total_hint = "6+" if not state.done else str(len(state.steps))
    status_cls = "status-done" if state.done else "status-running"
    status_icon = "✅" if state.done else "🔄"

    return f"""
    <div class="timeline-wrap">
      <div class="status-bar {status_cls}">
        {status_icon} {_esc(state.status)}
        <span class="progress-tag">已完成 {progress} 步</span>
      </div>
      <div class="timeline">
        {''.join(cards) if cards else '<p class="empty-hint">点击「开始优化」后，将在此逐步显示每个工具的调用结果</p>'}
      </div>
    </div>
    """


TIMELINE_CSS = """
.timeline-wrap { font-family: system-ui, sans-serif; }
.status-bar {
  padding: 12px 16px; border-radius: 10px; margin-bottom: 16px;
  font-weight: 600; display: flex; justify-content: space-between; align-items: center;
}
.status-running { background: #fffbeb; color: #b45309; border: 1px solid #fcd34d; }
.status-done { background: #ecfdf5; color: #047857; border: 1px solid #6ee7b7; }
.progress-tag { font-size: 0.85rem; font-weight: 500; opacity: 0.85; }
.step-card {
  border-left: 4px solid #d1d5db; padding: 14px 16px; margin: 10px 0;
  background: #f9fafb; border-radius: 0 10px 10px 0;
  animation: fadeIn 0.4s ease;
}
.step-done { border-left-color: #10b981; background: #f0fdf4; }
.step-compare {
  border-left-color: #3b82f6 !important;
  background: #e2e8f0 !important;
}
.step-body-compare { color: #111 !important; }
.step-compare .step-title { color: #0f172a !important; }
.step-compare .step-time { color: #334155 !important; font-weight: 600; }
.step-compare .step-tool { color: #1e293b !important; background: #cbd5e1 !important; }
.step-running { border-left-color: #f59e0b; background: #fffbeb; }
.step-header { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 6px; }
.step-title { font-weight: 700; font-size: 1rem; color: #111827; }
.step-tool { font-size: 0.75rem; color: #6b7280; background: #e5e7eb; padding: 2px 8px; border-radius: 4px; font-family: monospace; }
.step-badge { font-size: 0.75rem; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
.step-badge.done { background: #d1fae5; color: #065f46; }
.step-badge.running { background: #fef3c7; color: #92400e; }
.step-time { font-size: 0.8rem; color: #9ca3af; margin-bottom: 8px; }
.step-body { font-size: 0.9rem; color: #374151; line-height: 1.6; }
.code-block {
  background: #1f2937; color: #e5e7eb; padding: 10px; border-radius: 6px;
  white-space: pre-wrap; word-break: break-word; font-size: 0.82rem;
}
.pulse { animation: pulse 1.5s infinite; color: #b45309; }
.empty-hint { color: #374151; text-align: center; padding: 40px 0; font-weight: 600; }

@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }
"""
