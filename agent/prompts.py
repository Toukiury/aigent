"""系统提示词与优化模板"""

SYSTEM_PROMPT = """你是一个通用问题优化智能体，专门将用户模糊、不完整或低效的问题，
改写为结构清晰、上下文完整、易于大模型高质量回答的 Prompt。

你的工作原则：
1. 先理解真实意图，不臆造用户未提及的需求
2. 识别缺失维度：目标、背景、约束、受众、输出格式、示例等
3. 消除歧义，将笼统表述具体化
4. 使用结构化模板组织最终 Prompt
5. 对每一步优化给出简短、可理解的理由

你配备了以下工具，请按流程使用：
- analyze_question：诊断问题意图、缺失项与歧义
- rewrite_question：基于诊断结果重写问题
- evaluate_quality：评估优化后问题的质量并给出改进建议
"""

ANALYZE_PROMPT = """请分析以下用户问题，以 JSON 格式返回诊断结果（只返回 JSON，不要其他文字）：

用户问题：{question}
{user_context_block}

【重要】若用户提供了补充背景，必须将其视为核心约束，纳入意图分析与领域判断，不得忽略。

返回格式：
{{
  "intent": "用户真实意图（一句话，需融合补充背景）",
  "domain": "问题所属领域",
  "missing_info": ["缺失的信息维度1", "缺失的信息维度2"],
  "ambiguities": ["歧义点1", "歧义点2"],
  "suggested_context": ["建议补充的背景1", "建议补充的背景2"],
  "context_integration": "如何将用户补充背景融入优化方向（一句话）"
}}
"""

def template_hint(template: str) -> str:
    from .config import PROMPT_TEMPLATES

    sections = PROMPT_TEMPLATES.get(template, PROMPT_TEMPLATES["CO-STAR"])["sections"]
    lines = [f"优化模板（{template}）："]
    for sec in sections:
        lines.append(f"【{sec}】...")
    return "\n".join(lines)


REWRITE_PROMPT = """请根据诊断结果，将用户原始问题优化为高质量 Prompt。

原始问题：{question}
{user_context_block}
诊断结果：
{analysis}

{template_hint}

要求：
1. 在保留用户原意的前提下补全关键缺失信息（可合理假设并注明）
2. 严格按上述模板分段组织「优化后问题」正文
3. 列出逐条「优化说明」
4. 【硬性要求】若用户提供了补充背景，优化后的问题必须在 Context/背景 和 Objective/目标 中明确体现该背景。
   - 例如：补充背景为「旅游攻略」→ 爬虫目标应是旅游网站/攻略平台，采集景点、路线、美食等字段，禁止套用无关示例（如新闻网站）
   - 例如：补充背景为「课程作业」→ 应体现学习目的、难度约束

以 JSON 格式返回（只返回 JSON）：
{{
  "optimized_question": "优化后的完整 Prompt 正文",
  "optimization_notes": ["优化说明1", "优化说明2"],
  "assumptions": ["合理假设1", "合理假设2"],
  "context_used": "说明如何使用了用户补充背景"
}}
"""

SYSTEM_PROMPT_GEN = """请为以下优化后的问题，生成一段适合配合使用的 System Prompt（系统提示词）。

优化后问题：
{optimized}

以 JSON 格式返回（只返回 JSON）：
{{
  "system_prompt": "推荐的 System Prompt 全文（50-150字）",
  "rationale": "为什么这样设计 System Prompt 的简要说明"
}}
"""

CLARIFY_PROMPT = """用户提出了一个模糊问题，请生成 2-4 个追问，帮助用户补充关键信息。

原始问题：{question}
诊断结果：
{analysis}

以 JSON 格式返回（只返回 JSON）：
{{
  "clarifying_questions": ["追问1", "追问2", "追问3"]
}}
"""

COMPARE_ANSWER_PROMPT = """请模拟大模型分别回答以下两个问题，用于展示「问题优化」前后的效果差异。

{user_context_block}

问题 A（原始模糊问题，仅含这句话，不含任何补充背景）：
{original}

问题 B（优化后的结构化问题）：
{optimized}

要求：
1. 对问题 A 的回答必须**故意模糊、笼统、简短**（50-80字），体现「问题不清晰导致回答质量差」
2. 对问题 B 的回答必须**具体、可执行、详细**（250-400字），包含技术栈、步骤、字段示例、注意事项
3. 若用户补充背景与问题 A 相关（如旅游攻略），问题 B 的回答必须体现该背景，与 A 形成鲜明对比
4. 列出 A 的缺点和 B 的优点，各至少 3 条
5. JSON 字符串内如需换行请用 \\n，不要插入真实换行符

以 JSON 格式返回（只返回 JSON）：
{{
  "original_answer": "对问题A的模糊简短回答",
  "optimized_answer": "对问题B的详细可执行回答",
  "original_weaknesses": ["原始回答缺点1", "缺点2", "缺点3"],
  "optimized_strengths": ["优化后回答优点1", "优点2", "优点3"],
  "comparison_summary": "2-3句总结：优化前后差异有多大"
}}
"""

EVALUATE_PROMPT = """请评估以下优化后问题的质量。

原始问题：{question}
{user_context_block}
优化后问题：{optimized}

评估时请检查：若用户提供了补充背景，优化后问题是否明确体现了该背景（未体现则完整性扣分）。

以 JSON 格式返回（只返回 JSON）：
{{
  "clarity_score": 1-10的整数,
  "completeness_score": 1-10的整数,
  "actionability_score": 1-10的整数,
  "context_reflection_score": 1-10的整数,
  "overall_score": 1-10的整数,
  "passed": true或false（overall_score>=8为true）,
  "feedback": "若未通过，给出具体改进建议；若通过，写一句肯定评价",
  "context_check": "用户补充背景是否被正确融入（是/否 + 说明）"
}}
"""

REWRITE_WITH_FEEDBACK_PROMPT = """请根据评估反馈，进一步改进优化后的问题。

原始问题：{question}
{user_context_block}
当前优化版本：
{optimized}

评估反馈：{feedback}

诊断结果：
{analysis}

{template_hint}

【硬性要求】若用户提供了补充背景，改进后必须明确体现，不得使用与背景无关的示例。

以 JSON 格式返回（只返回 JSON）：
{{
  "optimized_question": "改进后的完整 Prompt 正文",
  "optimization_notes": ["本轮改进说明1", "本轮改进说明2"],
  "assumptions": ["合理假设1"],
  "context_used": "说明如何使用了用户补充背景"
}}
"""

DEMO_EXAMPLES = [
    "帮我写个爬虫",
    "帮我做文献综述",
    "我该怎么选课",
    "帮我准备面试",
]
