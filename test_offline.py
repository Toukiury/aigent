"""离线测试：不调用 API，验证 PDF 生成"""

from agent.models import OptimizationResult
from pdf_generator import generate_pdf

mock_result = OptimizationResult(
    original_question="帮我写个爬虫",
    optimized_question=(
        "【Context】Python 初学者，用于课程作业，采集公开新闻网站数据。\n"
        "【Objective】编写爬虫抓取新闻首页标题与链接。\n"
        "【约束】遵守 robots.txt，请求间隔≥1秒，输出 CSV。\n"
        "【Response】提供完整代码与简要说明。"
    ),
    optimization_notes=["补充技术栈", "明确采集目标", "增加合规约束"],
    assumptions=["目标为公开新闻站", "使用 requests + BeautifulSoup"],
    analysis={
        "intent": "获取网页数据采集代码",
        "domain": "编程",
        "missing_info": ["目标网站", "技术栈", "输出格式"],
        "ambiguities": ["爬虫范围不明确"],
    },
    evaluation={
        "clarity_score": 9,
        "completeness_score": 9,
        "actionability_score": 9,
        "overall_score": 9,
        "passed": True,
        "feedback": "质量达标",
    },
    steps=[
        {"step": 1, "tool": "analyze_question", "timestamp": "2025-06-21 10:00:00",
         "input": {"question": "帮我写个爬虫"}, "output": {"intent": "采集代码", "domain": "编程",
         "missing_info": ["技术栈"], "ambiguities": ["范围不明"]}},
        {"step": 2, "tool": "suggest_clarifications", "timestamp": "2025-06-21 10:00:02",
         "input": {}, "output": {"clarifying_questions": ["目标网站是？", "用什么语言？"]}},
        {"step": 3, "tool": "rewrite_question", "timestamp": "2025-06-21 10:00:05",
         "input": {}, "output": {"optimized_question": "（见最终结果）", "optimization_notes": ["补充约束"]}},
        {"step": 4, "tool": "evaluate_quality", "timestamp": "2025-06-21 10:00:10",
         "input": {}, "output": {"overall_score": 9, "passed": True, "feedback": "达标",
         "clarity_score": 9, "completeness_score": 9, "actionability_score": 9}},
        {"step": 5, "tool": "generate_system_prompt", "timestamp": "2025-06-21 10:00:12",
         "input": {}, "output": {"system_prompt": "你是 Python 爬虫专家...", "rationale": "明确角色"}},
        {"step": 6, "tool": "compare_answers", "timestamp": "2025-06-21 10:00:15",
         "input": {}, "output": {
             "original_answer": "可以用 Python 写爬虫...",
             "optimized_answer": "以下是针对新闻首页的完整代码...",
             "comparison_summary": "优化后回答更具体、更可执行",
         }},
    ],
    started_at="2025-06-21 10:00:00",
    finished_at="2025-06-21 10:00:15",
    template="CO-STAR",
    user_context="Python 初学者，课程作业",
    model_info={"name": "DeepSeek Chat", "model": "deepseek-chat"},
    system_prompt="你是 Python 爬虫专家，注重代码规范与合规。",
    system_prompt_rationale="明确专家角色与合规要求",
    clarifying_questions=["目标网站是什么？", "需要采集哪些字段？"],
    comparison={
        "original_answer": "可以用 Python 的 requests 库...",
        "optimized_answer": "以下是完整可运行代码...",
        "comparison_summary": "优化后提供了具体技术栈、约束和输出格式",
    },
)

if __name__ == "__main__":
    path = generate_pdf(mock_result, "test_report.pdf")
    print(f"PDF 生成成功: {path}")
