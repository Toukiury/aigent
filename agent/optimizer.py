"""问题优化智能体：支持一次性运行与流式逐步输出"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generator

from .config import get_active_model_info
from .models import OptimizationResult, StreamState
from .tools import (
    analyze_question,
    compare_answers,
    evaluate_quality,
    generate_system_prompt,
    rewrite_question,
    suggest_clarifications,
)


def _append_step(state: StreamState, step_num: int, log: dict[str, Any]) -> None:
    state.steps.append({"step": step_num, **log})


def _copy_state(state: StreamState) -> StreamState:
    return StreamState(
        steps=list(state.steps),
        status=state.status,
        current_tool=state.current_tool,
        optimized_question=state.optimized_question,
        optimization_notes=list(state.optimization_notes),
        assumptions=list(state.assumptions),
        analysis=dict(state.analysis),
        evaluation=dict(state.evaluation),
        system_prompt=state.system_prompt,
        system_prompt_rationale=state.system_prompt_rationale,
        clarifying_questions=list(state.clarifying_questions),
        comparison=dict(state.comparison),
        done=state.done,
        result=state.result,
    )


class QuestionOptimizer:
    """通用问题优化智能体"""

    def __init__(self, max_rounds: int = 2, pass_threshold: int = 8):
        self.max_rounds = max_rounds
        self.pass_threshold = pass_threshold

    def run(
        self,
        question: str,
        template: str = "CO-STAR",
        user_context: str = "",
        enable_compare: bool = True,
    ) -> OptimizationResult:
        final: OptimizationResult | None = None
        for state in self.run_stream(question, template, user_context, enable_compare):
            if state.done and state.result:
                final = state.result
        if final is None:
            raise RuntimeError("优化流程未正常完成")
        return final

    def run_stream(
        self,
        question: str,
        template: str = "CO-STAR",
        user_context: str = "",
        enable_compare: bool = True,
    ) -> Generator[StreamState, None, None]:
        question = question.strip()
        if not question:
            raise ValueError("问题不能为空")

        started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        state = StreamState()
        step_num = 0

        def emit(tool: str, status: str) -> Generator[StreamState, None, None]:
            state.current_tool = tool
            state.status = status
            yield _copy_state(state)

        yield from emit("analyze_question", "正在调用工具：问题诊断 (analyze_question)...")
        analysis, log1 = analyze_question(question, user_context=user_context)
        step_num += 1
        _append_step(state, step_num, log1)
        state.analysis = analysis
        yield _copy_state(state)

        yield from emit("suggest_clarifications", "正在调用工具：追问建议 (suggest_clarifications)...")
        clarify_result, log_clarify = suggest_clarifications(question, analysis)
        step_num += 1
        _append_step(state, step_num, log_clarify)
        state.clarifying_questions = clarify_result.get("clarifying_questions", [])
        yield _copy_state(state)

        yield from emit("rewrite_question", "正在调用工具：问题重写 (rewrite_question)...")
        rewrite_result, log2 = rewrite_question(
            question, analysis, template=template, user_context=user_context
        )
        step_num += 1
        _append_step(state, step_num, log2)
        optimized = rewrite_result.get("optimized_question", "")
        notes = list(rewrite_result.get("optimization_notes", []))
        assumptions = list(rewrite_result.get("assumptions", []))
        state.optimized_question = optimized
        state.optimization_notes = notes
        state.assumptions = assumptions
        yield _copy_state(state)

        yield from emit("evaluate_quality", "正在调用工具：质量评估 (evaluate_quality)...")
        evaluation, log3 = evaluate_quality(question, optimized, user_context=user_context)
        step_num += 1
        _append_step(state, step_num, log3)
        state.evaluation = evaluation
        yield _copy_state(state)

        round_num = 1
        while (
            not evaluation.get("passed", False)
            and evaluation.get("overall_score", 0) < self.pass_threshold
            and round_num < self.max_rounds
        ):
            round_num += 1
            yield from emit(
                "rewrite_question",
                f"质量未达标，第 {round_num + 1} 轮迭代重写 (rewrite_question)...",
            )
            feedback = evaluation.get("feedback", "")
            rewrite_result, log_rewrite = rewrite_question(
                question,
                analysis,
                template=template,
                user_context=user_context,
                feedback=feedback,
                previous=optimized,
            )
            step_num += 1
            _append_step(state, step_num, log_rewrite)
            optimized = rewrite_result.get("optimized_question", optimized)
            notes.extend(rewrite_result.get("optimization_notes", []))
            assumptions.extend(rewrite_result.get("assumptions", []))
            state.optimized_question = optimized
            state.optimization_notes = notes
            state.assumptions = assumptions
            yield _copy_state(state)

            yield from emit("evaluate_quality", f"第 {round_num + 1} 轮质量评估 (evaluate_quality)...")
            evaluation, log_eval = evaluate_quality(
                question, optimized, user_context=user_context
            )
            step_num += 1
            _append_step(state, step_num, log_eval)
            state.evaluation = evaluation
            yield _copy_state(state)

        yield from emit(
            "generate_system_prompt",
            "正在调用工具：生成 System Prompt (generate_system_prompt)...",
        )
        sys_result, log_sys = generate_system_prompt(optimized)
        step_num += 1
        _append_step(state, step_num, log_sys)
        state.system_prompt = sys_result.get("system_prompt", "")
        state.system_prompt_rationale = sys_result.get("rationale", "")
        yield _copy_state(state)

        comparison: dict[str, Any] = {}
        if enable_compare:
            yield from emit("compare_answers", "正在调用工具：优化前后对比 (compare_answers)...")
            comparison, log_cmp = compare_answers(
                question, optimized, user_context=user_context
            )
            step_num += 1
            _append_step(state, step_num, log_cmp)
            state.comparison = comparison
            yield _copy_state(state)

        finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = OptimizationResult(
            original_question=question,
            optimized_question=optimized,
            optimization_notes=notes,
            assumptions=assumptions,
            analysis=analysis,
            evaluation=evaluation,
            steps=state.steps,
            started_at=started_at,
            finished_at=finished_at,
            template=template,
            user_context=user_context.strip(),
            model_info=get_active_model_info(),
            system_prompt=state.system_prompt,
            system_prompt_rationale=state.system_prompt_rationale,
            clarifying_questions=state.clarifying_questions,
            comparison=comparison,
        )
        state.done = True
        state.status = f"全部完成！共执行 {len(state.steps)} 个工具调用。"
        state.current_tool = ""
        state.result = result
        yield _copy_state(state)
