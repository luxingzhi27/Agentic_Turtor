from datetime import datetime, timedelta, timezone

from app.models import ConceptStats
from app.services.gap_detector import GapDetector


def test_detects_weak_concept() -> None:
    response = GapDetector().detect(
        {
            "recursion": ConceptStats(
                events=3,
                average_score=0.45,
                average_confidence=0.35,
                common_errors=["missing base case", "wrong stopping condition"],
                summaries=["Failed recursion because the base case was missing."],
            )
        },
        [],
    )

    assert any(gap.gap_type == "weak" and gap.concept == "recursion" for gap in response.gaps)


def test_detects_avoided_concept() -> None:
    response = GapDetector().detect(
        {
            "dynamic programming": ConceptStats(
                events=1,
                last_seen=datetime.now(timezone.utc) - timedelta(days=15),
                average_score=0.5,
                average_confidence=0.25,
                common_errors=["cannot define state"],
                summaries=["Skipped the DP practice problem."],
            )
        },
        [],
    )

    assert any(gap.gap_type == "avoided" for gap in response.gaps)


def test_detects_decaying_concept() -> None:
    response = GapDetector().detect(
        {
            "binary search": ConceptStats(
                events=2,
                last_seen=datetime.now(timezone.utc) - timedelta(days=30),
                average_score=0.88,
                average_confidence=0.8,
                common_errors=[],
                summaries=["Older quiz score was strong."],
            )
        },
        [],
    )

    assert any(gap.gap_type == "decaying" for gap in response.gaps)

