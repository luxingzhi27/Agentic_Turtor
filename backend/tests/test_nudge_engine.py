from app.models import Gap
from app.services.nudge_engine import NudgeEngine


import pytest


@pytest.mark.anyio
async def test_nudges_are_action_oriented_and_short() -> None:
    gaps = [
        Gap(
            concept="recursion",
            gap_type="weak",
            severity=0.8,
            evidence=["Repeated missing base-case errors."],
            calculation_notes=[],
        )
    ]

    response = await NudgeEngine().generate(gaps)

    assert response.nudges
    nudge = response.nudges[0]
    assert nudge.passed_guardrail
    assert nudge.nudge.count(".") <= 2
    assert "the answer is" not in nudge.nudge.lower()
    assert nudge.practice_prompt
    assert len(nudge.practice_steps) >= 3


@pytest.mark.anyio
async def test_nudges_do_not_force_an_exercise_for_every_gap() -> None:
    gaps = [
        Gap(
            concept="binary search boundary",
            gap_type="decaying",
            severity=0.55,
            evidence=["Previously understood the rule, but has not reviewed it recently."],
            calculation_notes=[],
        )
    ]

    response = await NudgeEngine().generate(gaps)

    nudge = response.nudges[0]
    assert nudge.practice_prompt is None
    assert nudge.exercise_title is None
    assert len(nudge.practice_steps) >= 3
