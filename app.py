"""通用问题优化智能体 — 流式 Web 应用（逐步显示工具调用结果）"""

from __future__ import annotations

import os
import traceback

import gradio as gr
from dotenv import load_dotenv

from agent.config import PROMPT_TEMPLATES, get_active_model_info
from agent.optimizer import QuestionOptimizer
from pdf_generator import generate_pdf
from ui_format import TIMELINE_CSS, render_comparison_html, render_timeline

load_dotenv()

optimizer = QuestionOptimizer(max_rounds=2, pass_threshold=8)
model_info = get_active_model_info()

CSS = (
    TIMELINE_CSS
    + """
.gradio-container { max-width: 1200px !important; margin: auto; }
#title { text-align: center; margin-bottom: 0.25rem; }
#subtitle { text-align: center; color: #6b7280; margin-bottom: 0.5rem; }
#model-badge {
    text-align: center; color: #1a56db; font-size: 0.9rem;
    background: #eff6ff; padding: 8px 14px; border-radius: 8px; margin-bottom: 1rem;
}
.final-panel { border: 2px solid #10b981; border-radius: 12px; padding: 4px; }
"""
)


def _empty_outputs():
    return (
        render_timeline_empty(),
        "",
        "",
        "*等待优化...*",
        "",
        "<p style='color:#111;font-weight:600;'>等待对比结果...</p>",
        "",
        gr.skip(),
    )


def render_timeline_empty():
    from agent.models import StreamState

    return render_timeline(StreamState(status="等待输入问题..."))


def _score_md(evaluation: dict) -> str:
    if not evaluation:
        return "*等待质量评估...*"
    return (
        f"### 质量评分\n"
        f"清晰度 **{evaluation.get('clarity_score', '-')}/10** · "
        f"完整性 **{evaluation.get('completeness_score', '-')}/10** · "
        f"可执行性 **{evaluation.get('actionability_score', '-')}/10** · "
        f"背景融入 **{evaluation.get('context_reflection_score', '-')}/10** · "
        f"综合 **{evaluation.get('overall_score', '-')}/10**\n\n"
        f"_{evaluation.get('feedback', '')}_\n\n"
        f"*背景检查：{evaluation.get('context_check', '—')}*"
    )


def _comparison_html(comparison: dict, done: bool, enabled: bool) -> str:
    if not enabled:
        return "<p style='color:#111;font-weight:600;'>已关闭「优化前后对比」</p>"
    if not comparison:
        hint = "等待对比结果..." if not done else "无对比数据"
        return f"<p style='color:#111;font-weight:600;'>{hint}</p>"
    return render_comparison_html(comparison)


def _clarify_text(questions: list) -> str:
    if not questions:
        return ""
    return "\n".join(f"{i}. {q}" for i, q in enumerate(questions, 1))


PLACEHOLDER_KEYS = {
    "your_deepseek_api_key_here",
    "your_dashscope_api_key_here",
    "your_ark_api_key_here",
    "sk-xxx",
}


def _is_valid_api_key() -> bool:
    key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
    key = key.strip()
    return bool(key) and key not in PLACEHOLDER_KEYS and not key.startswith("your_")


def _build_outputs(state, enable_compare: bool, pdf_path=None):
    """构建 Gradio 输出元组；未完成时不更新 PDF 组件"""
    timeline_html = render_timeline(state)
    optimized = state.optimized_question or ""
    system_prompt = state.system_prompt or ""
    score = _score_md(state.evaluation)
    clarify = _clarify_text(state.clarifying_questions)
    comparison = _comparison_html(state.comparison, state.done, enable_compare)
    report = state.result.to_markdown() if state.result else ""
    pdf_value = pdf_path if (state.done and pdf_path) else gr.skip()
    return (
        timeline_html,
        optimized,
        system_prompt,
        score,
        clarify,
        comparison,
        report,
        pdf_value,
    )


def optimize_question_stream(
    question: str,
    template: str,
    user_context: str,
    enable_compare: bool,
):
    """流式生成器：每完成一个工具调用就更新界面"""
    if not question or not question.strip():
        raise gr.Error("请输入需要优化的问题")

    if not _is_valid_api_key():
        raise gr.Error(
            "未配置有效的 API Key。请编辑 `.env` 文件，将 LLM_API_KEY 替换为你的真实密钥"
            "（当前仍是 .env.example 中的占位符）。"
            "DeepSeek 申请：https://platform.deepseek.com"
        )

    try:
        yield _empty_outputs()

        for state in optimizer.run_stream(
            question.strip(),
            template=template,
            user_context=user_context or "",
            enable_compare=enable_compare,
        ):
            pdf_path = None
            if state.done and state.result:
                pdf_path = generate_pdf(state.result)
            yield _build_outputs(state, enable_compare, pdf_path)

    except Exception as e:
        traceback.print_exc()
        raise gr.Error(f"优化失败：{e}") from e


template_choices = list(PROMPT_TEMPLATES.keys())

with gr.Blocks(title="通用问题优化智能体") as demo:
    gr.Markdown("# 通用问题优化智能体", elem_id="title")
    gr.Markdown(
        "输入模糊问题后，**逐步实时展示**每个工具的调用与输出，最终生成优化 Prompt 与 PDF 报告。",
        elem_id="subtitle",
    )
    gr.Markdown(
        f"**当前模型：** {model_info['name']} · `{model_info['model']}` · "
        f"{model_info['description']}",
        elem_id="model-badge",
    )

    with gr.Row():
        # ===== 左侧：输入区 =====
        with gr.Column(scale=4):
            gr.Markdown("### 📝 输入")
            question_input = gr.Textbox(
                label="模糊问题",
                placeholder="例如：帮我写个爬虫",
                lines=3,
            )
            user_context = gr.Textbox(
                label="补充背景（可选，但强烈建议填写）",
                placeholder="例如：旅游攻略（将采集马蜂窝/穷游网景点与路线）、Python 初学者、课程作业",
                lines=2,
                info="补充背景会强制融入优化结果，如填「旅游攻略」则不会生成新闻爬虫示例",
            )
            with gr.Row():
                template_input = gr.Dropdown(
                    choices=template_choices,
                    value="CO-STAR",
                    label="优化模板",
                    scale=2,
                )
                enable_compare = gr.Checkbox(
                    label="优化前后对比",
                    value=True,
                    scale=1,
                )
            gr.Examples(
                examples=[
                    ["帮我写个爬虫", "旅游攻略，采集景点名称、地址、评分", "CO-STAR", True],
                    ["帮我写个爬虫", "", "CO-STAR", True],
                    ["帮我做文献综述", "大语言模型提示词工程方向", "CO-STAR", True],
                    ["我该怎么选课", "计算机大二，偏AI方向", "CO-STAR", True],
                    ["帮我准备面试", "互联网公司后端开发岗", "CO-STAR", True],
                ],
                inputs=[question_input, user_context, template_input, enable_compare],
                label="快速示例",
            )
            submit_btn = gr.Button("🚀 开始优化", variant="primary", size="lg")
            gr.Markdown(
                "**使用方式：** 本地运行 `python app.py` → 浏览器打开 "
                "http://localhost:7860 ；部署到 Hugging Face Spaces 可获得公网链接。"
            )

        # ===== 右侧：最终结果区 =====
        with gr.Column(scale=5):
            gr.Markdown("### ✅ 最终输出")
            optimized_output = gr.Textbox(
                label="优化后的问题",
                lines=8,
                placeholder="完成「问题重写」工具后将在此显示...",
            )
            system_prompt_output = gr.Textbox(
                label="推荐 System Prompt",
                lines=3,
                placeholder="完成「System Prompt」工具后将在此显示...",
            )
            score_output = gr.Markdown(value="*等待质量评估...*")
            with gr.Accordion("建议追问", open=False):
                clarify_output = gr.Textbox(lines=3, show_label=False, placeholder="完成「追问建议」后显示...")
            with gr.Accordion("优化前后回答对比", open=True):
                comparison_output = gr.HTML(
                    value="<p style='color:#111;font-weight:600;'>等待对比结果...</p>"
                )

    # ===== 中间：工具调用时间线 =====
    gr.Markdown("---\n### 🔄 工具调用流水线（实时逐步显示）")
    timeline_output = gr.HTML(value=render_timeline_empty())

    with gr.Accordion("完整 Markdown 报告", open=False):
        report_output = gr.Markdown()

    pdf_output = gr.File(label="📄 下载求解过程 PDF（全部完成后可用）")

    submit_btn.click(
        fn=optimize_question_stream,
        inputs=[question_input, template_input, user_context, enable_compare],
        outputs=[
            timeline_output,
            optimized_output,
            system_prompt_output,
            score_output,
            clarify_output,
            comparison_output,
            report_output,
            pdf_output,
        ],
    )

    gr.Markdown(
        "---\n"
        "**工具链：** `analyze_question` → `suggest_clarifications` → "
        "`rewrite_question` → `evaluate_quality`（可迭代）→ "
        "`generate_system_prompt` → `compare_answers`"
    )


def _is_hf_space() -> bool:
    return bool(os.getenv("SPACE_ID") or os.getenv("SYSTEM") == "spaces")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "7860"))
    on_hf = _is_hf_space()

    if on_hf:
        # Hugging Face Space 容器内必须用 0.0.0.0，由平台反向代理对外提供服务
        server_name = "0.0.0.0"
    else:
        server_name = os.getenv("SERVER_NAME", "127.0.0.1")
        print(f"\n>>> 请在浏览器打开: http://127.0.0.1:{port}  或  http://localhost:{port}\n")

    demo.launch(
        server_name=server_name,
        server_port=port,
        share=not on_hf and os.getenv("GRADIO_SHARE", "false").lower() == "true",
        css=CSS,
        theme=gr.themes.Soft(),
    )
