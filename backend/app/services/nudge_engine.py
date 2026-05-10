from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field, ValidationError

from app.adapters.llm import LLMClient, LLMResponseError
from app.models import Gap, Nudge, NudgesResponse


ACTION_VERBS = [
    "write",
    "draw",
    "mark",
    "test",
    "compare",
    "predict",
    "redo",
    "explain",
    "list",
    "trace",
    "sketch",
    "try",
    "start",
    "attempt",
    "apply",
    "写",
    "标",
    "圈",
    "试",
    "完成",
    "判断",
    "提交",
    "画",
    "列",
    "做",
    "看",
    "读",
    "核对",
]

FORBIDDEN_PATTERNS = [
    r"\bthe answer is\b",
    r"\bsolution\b",
    r"\btherefore,?\s+the result\b",
    r"\bstep-by-step solution\b",
]


class PracticeDraft(BaseModel):
    nudge: str
    exercise_title: str | None = None
    practice_prompt: str | None = None
    practice_materials: list[str] = Field(default_factory=list)
    practice_steps: list[str] = Field(default_factory=list)
    submission_checklist: list[str] = Field(default_factory=list)
    encouragement: str


PRACTICE_SYSTEM_PROMPT = """You generate concrete next-step practice for an action-oriented tutor.
Return only JSON with keys: nudge, exercise_title, practice_prompt, practice_materials, practice_steps, submission_checklist, encouragement.

Rules:
- Write nudge, exercise_title, practice_prompt, practice_steps, submission_checklist, and encouragement in Simplified Chinese.
- Keep technical concept names in their original form when helpful.
- Do not solve the exercise.
- Do not provide the final answer.
- The advice must tell the student what to do immediately, starting from a first step.
- Decide whether a concrete example task is useful. If the trace shows a practice gap, confusion, weak skill, or avoided concept, include an example task that fits the concept and starts with "题目：".
- If a question is not the best next action, leave exercise_title and practice_prompt null, and give concrete practice_steps such as reading a specific snippet, annotating evidence, rewriting a rule, or testing one case.
- When you include an example task, practice_prompt must contain an actual task statement with concrete data, code skeleton, input/output shape, table, list, graph, tree, or scenario details.
- Never write generic phrases like "do a practice about the concept" unless you also provide the exact first action or a concrete example.
- practice_materials should contain only materials the student can use immediately. It can be empty when the action is not material-based.
- practice_steps must be 3 to 5 short imperative steps.
- submission_checklist is optional; include 2 to 4 items only when a concrete exercise or written artifact is expected.
- Be warm, direct, and practical.
- Keep the nudge at most two sentences."""


class NudgeEngine:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client

    async def generate(self, gaps: list[Gap]) -> NudgesResponse:
        nudges = [await self._for_gap(gap) for gap in gaps[:3]]
        return NudgesResponse(nudges=nudges)

    async def _for_gap(self, gap: Gap) -> Nudge:
        draft = await self._llm_practice(gap) if self.llm_client else None
        if draft is None:
            draft = self._fallback_practice(gap)
        prompt_guardrail = True if draft.practice_prompt is None else self._passes_guardrail(draft.practice_prompt, max_sentences=6)
        passed = self._passes_guardrail(draft.nudge) and prompt_guardrail
        if not passed:
            draft = self._fallback_practice(gap)
            prompt_guardrail = True if draft.practice_prompt is None else self._passes_guardrail(draft.practice_prompt, max_sentences=6)
            passed = self._passes_guardrail(draft.nudge) and prompt_guardrail
        priority = "high" if gap.severity >= 0.7 else "medium" if gap.severity >= 0.45 else "low"
        return Nudge(
            concept=gap.concept,
            gap_type=gap.gap_type,
            nudge=draft.nudge,
            action_type=self._action_type(gap),
            exercise_title=draft.exercise_title,
            practice_prompt=draft.practice_prompt,
            practice_materials=draft.practice_materials[:6],
            practice_steps=draft.practice_steps[:5],
            submission_checklist=draft.submission_checklist[:4],
            encouragement=draft.encouragement,
            priority=priority,
            passed_guardrail=passed,
        )

    async def _llm_practice(self, gap: Gap) -> PracticeDraft | None:
        if self.llm_client is None:
            return None
        user_prompt = json.dumps(
            {
                "concept": gap.concept,
                "gap_type": gap.gap_type,
                "severity": gap.severity,
                "evidence": gap.evidence[:4],
                "calculation_notes": gap.calculation_notes[:4],
            },
            ensure_ascii=False,
        )
        try:
            data = await self.llm_client.extract_json(PRACTICE_SYSTEM_PROMPT, user_prompt)
            draft = PracticeDraft.model_validate(data)
        except (LLMResponseError, ValidationError, ValueError):
            return None
        if not self._is_actionable(draft):
            return None
        return draft

    def _fallback_practice(self, gap: Gap) -> PracticeDraft:
        if gap.gap_type == "weak":
            exercise = self._exercise_for(gap.concept, gap.gap_type)
            nudge = (
                f"现在做一道很小的「{gap.concept}」题，只交题目要求的中间过程。"
                "重点是抓住上次容易错的位置，不需要求完整答案。"
            )
            practice_prompt = exercise["prompt"]
            practice_materials = exercise["materials"]
            practice_steps = [
                "先圈出题目里最小的输入或边界情况。",
                "在 starter code 或表格上写出第一步，不要直接完成答案。",
                "标出你最可能再次出错的位置。",
                "写下一条下次避免该错误的检查规则。",
            ]
            encouragement = "题目已经足够小了；你只要把第一处薄弱点定位出来，就已经完成了今天最有价值的一步。"
        elif gap.gap_type == "avoided":
            exercise = self._exercise_for(gap.concept, gap.gap_type)
            nudge = (
                f"用 10 分钟启动这道「{gap.concept}」题，先不要追求做完。"
                "只提交题目建模和第一步决策，让回避点变成可观察的材料。"
            )
            practice_prompt = exercise["prompt"]
            practice_materials = exercise["materials"]
            practice_steps = [
                "用一句话写出这道题要求你判断什么。",
                "只写第一个变量、状态或规则，不需要算最终答案。",
                "把你能确定的一步写在材料旁边。",
                "写出一个具体卡住你的问题。",
            ]
            encouragement = "先把题目摆上桌面就很好；一个不完整但真实的开头，比继续回避更有用。"
        else:
            exercise = {
                "title": None,
                "prompt": None,
                "materials": [
                    f"回忆对象：「{gap.concept}」",
                    "小数据：任选你最近做过的一道相关题，只看题干前两行或第一个测试样例",
                ],
                "submission": [
                    "写出你凭记忆能说出的核心规则",
                    "圈出第一个不确定的词或条件",
                ],
            }
            nudge = (
                f"先不看笔记，做一道「{gap.concept}」回忆题。"
                "用给定小数据检查规则有没有变模糊。"
            )
            practice_prompt = None
            practice_materials = exercise["materials"]
            practice_steps = [
                "合上笔记，先写你记得的规则。",
                "找一条最近相关题目的输入样例，只判断第一步该用哪条规则。",
                "打开笔记前，圈出最不确定的一步。",
                "用笔记核对那一步，并写一句修正后的规则。",
            ]
            encouragement = "这不是考试；你圈出的不确定处，就是下一次复习最省力的入口。"
        return PracticeDraft(
            nudge=nudge,
            exercise_title=exercise["title"],
            practice_prompt=practice_prompt,
            practice_materials=practice_materials,
            practice_steps=practice_steps,
            submission_checklist=exercise["submission"],
            encouragement=encouragement,
        )

    def _action_type(self, gap: Gap) -> str:
        if gap.gap_type == "weak":
            return "micro-exercise-and-mark"
        if gap.gap_type == "avoided":
            return "ten-minute-start"
        return "retrieve-and-test"

    def _exercise_for(self, concept: str, gap_type: str) -> dict[str, list[str] | str]:
        lowered = concept.lower()
        if any(token in lowered for token in ["state definition", "dynamic", "dp", "recurrence"]):
            return {
                "title": "台阶最小花费的 DP 建模题",
                "prompt": "题目：有 5 级台阶，每级花费 costs = [2, 5, 1, 4, 3]。你每次可以走 1 级或 2 级，可以从第 0 级或第 1 级开始。请只完成 DP 建模：定义 dp[i] 的含义，并写出递推关系，不要计算最终最小花费。",
                "materials": [
                    "数据：costs = [2, 5, 1, 4, 3]",
                    "限制：每次可以走 1 级或 2 级",
                    "目标：到达顶部时累计花费最小",
                    "提示：先判断 dp[i] 表示“站在第 i 级”还是“到达第 i 级之前”",
                ],
                "submission": [
                    "写出 dp[i] 的一句话定义",
                    "写出 base cases",
                    "写出 recurrence",
                    "标出你最不确定的一处建模选择",
                ],
            }
        if any(token in lowered for token in ["factorial", "base case"]):
            return {
                "title": "factorial 的 base case 补全题",
                "prompt": "题目：补全 `factorial(n)` 的停止条件。函数要能处理 n = 0、n = 1、n = 4。请先写 base case，再写递归调用；不要展开计算 4! 的最终结果。",
                "materials": [
                    "Starter code: `def factorial(n):\\n    # base case here\\n    return n * factorial(n - 1)`",
                    "测试输入：n = 0, n = 1, n = 4",
                    "目标输出形状：n = 0 和 n = 1 时不再递归；n = 4 时逐步缩小到 base case",
                ],
                "submission": [
                    "写出 base case 条件",
                    "写出递归调用那一行",
                    "说明为什么必须先检查 base case",
                ],
            }
        if any(token in lowered for token in ["tree depth", "tree", "depth"]):
            return {
                "title": "树高递归的停止条件题",
                "prompt": "题目：给定树 A(B, C(D, E))，请写出求树高 `height(node)` 的停止条件，以及对 A 的子节点做递归处理的第一步。不要算出最终树高。",
                "materials": [
                    "树结构：A 的子节点是 B 和 C；C 的子节点是 D 和 E",
                    "边界情况：空节点 None 的高度如何处理",
                    "Starter shape: `height(node) = ? if node is None else ?`",
                ],
                "submission": [
                    "写出 None 节点的返回值",
                    "写出对 A 的所有子节点要做的第一步",
                    "标出是否需要 max、sum 或 count，并说明一句原因",
                ],
            }
        if any(token in lowered for token in ["count-down", "count_down", "recursion", "stopping"]):
            return {
                "title": "count_down 的递归停止题",
                "prompt": "题目：写 `count_down(n)`，让它打印 n, n-1, ..., 1。请只针对 n = 3 和 n = 0 写出停止条件、打印语句位置、递归调用方向，不需要写完整可运行代码。",
                "materials": [
                    "目标输出形状：n = 3 时依次出现 3, 2, 1",
                    "边界输入：n = 0",
                    "Starter outline: `if ____: return; print(n); count_down(____)`",
                ],
                "submission": [
                    "填出停止条件",
                    "填出递归调用参数",
                    "说明 print 应该在递归调用前还是后",
                ],
            }
        if "binary search" in lowered or "boundary" in lowered:
            return {
                "title": "二分查找边界更新题",
                "prompt": "题目：在有序数组 nums = [1, 3, 3, 5, 8, 13] 中找第一个大于等于 5 的位置。请只写 loop condition、mid 计算方式和 left/right 更新规则，不要给最终下标。",
                "materials": [
                    "数组：nums = [1, 3, 3, 5, 8, 13]",
                    "目标：first index with value >= 5",
                    "边界提示：数组里有重复元素 3，目标 5 正好存在",
                ],
                "submission": [
                    "写出 left/right 初始值",
                    "写出 while 条件和 mid 计算",
                    "写出 nums[mid] < 5 与 nums[mid] >= 5 时的更新规则",
                ],
            }
        return {
            "title": f"{concept} 的第一步判断题",
            "prompt": f"题目：给定样例数据 records = [{{'score': 2, 'attempts': 1}}, {{'score': 4, 'attempts': 3}}, {{'score': 7, 'attempts': 2}}]。请用「{concept}」只完成第一步判断：你要从每条记录中看哪个字段、用什么条件筛选、第一条记录如何处理，不要给最终结论。",
            "materials": [
                "样例数据：records = [{'score': 2, 'attempts': 1}, {'score': 4, 'attempts': 3}, {'score': 7, 'attempts': 2}]",
                f"目标：只练习「{concept}」的第一步判断",
                "限制：只处理第一条记录，不要完成全部记录",
            ],
            "submission": [
                "写出要读取的字段名",
                "写出判断条件",
                "写出第一条记录的处理动作",
            ],
        }

    def _is_actionable(self, draft: PracticeDraft) -> bool:
        combined = " ".join(
            item
            for item in [
                draft.nudge,
                draft.exercise_title,
                draft.practice_prompt,
                *draft.practice_materials,
                *draft.practice_steps,
                *draft.submission_checklist,
            ]
            if item
        )
        if len(draft.practice_steps) < 3:
            return False
        if not any(verb in combined.lower() for verb in ACTION_VERBS):
            return False
        if draft.practice_prompt:
            return self._has_task_statement(draft.practice_prompt) or self._has_concrete_material(combined)
        return True

    def _has_concrete_material(self, text: str) -> bool:
        without_time = re.sub(r"10\s*分钟|10\s*minutes", "", text, flags=re.IGNORECASE)
        numbers = re.findall(r"\d+", without_time)
        concrete_tokens = [
            "[",
            "]",
            "{",
            "}",
            "`",
            "costs",
            "nums",
            "records",
            "starter",
            "输入",
            "数组",
            "树结构",
            "Starter code",
            "测试输入",
            "题目：",
            "数据：",
        ]
        return len(numbers) >= 2 or any(token in text for token in concrete_tokens)

    def _has_task_statement(self, text: str) -> bool:
        return bool(re.search(r"题目[:：]|给定|Starter|数组|数据|输入|records|nums|costs|tree", text, re.IGNORECASE))

    def _passes_guardrail(self, text: str, max_sentences: int = 2) -> bool:
        sentences = [sentence for sentence in re.split(r"[.!?]+", text) if sentence.strip()]
        if len(sentences) > max_sentences:
            return False
        lowered = text.lower()
        if not any(verb in lowered for verb in ACTION_VERBS):
            return False
        return not any(re.search(pattern, lowered) for pattern in FORBIDDEN_PATTERNS)
