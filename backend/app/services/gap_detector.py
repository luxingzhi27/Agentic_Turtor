from __future__ import annotations

from datetime import datetime, timezone

from app.models import ConceptStats, Gap, GapsResponse, LearningEvent


class GapDetector:
    def detect(self, concept_index: dict[str, ConceptStats], events: list[LearningEvent]) -> GapsResponse:
        gaps: list[Gap] = []
        for concept, stats in concept_index.items():
            gaps.extend(self._detect_for_concept(concept, stats))
        gaps.sort(key=lambda gap: gap.severity, reverse=True)
        return GapsResponse(gaps=gaps[:5])

    def _detect_for_concept(self, concept: str, stats: ConceptStats) -> list[Gap]:
        gaps: list[Gap] = []
        evidence = self._evidence(stats)
        score = stats.average_score
        confidence = stats.average_confidence
        repeated_errors = len(stats.common_errors)
        days_since = self._days_since(stats.last_seen)

        weak_severity = 0.0
        weak_notes: list[str] = []
        if score is not None and score < 0.65:
            weak_severity += 0.35
            weak_notes.append(f"Average score {score:.2f} is below 0.65.")
        if confidence is not None and confidence < 0.55:
            weak_severity += 0.25
            weak_notes.append(f"Average confidence {confidence:.2f} is below 0.55.")
        if repeated_errors:
            weak_severity += min(0.3, repeated_errors * 0.12)
            weak_notes.append(f"Repeated errors: {', '.join(stats.common_errors[:3])}.")
        if weak_severity >= 0.3:
            gaps.append(
                Gap(
                    concept=concept,
                    gap_type="weak",
                    severity=min(1.0, weak_severity),
                    evidence=evidence,
                    calculation_notes=weak_notes,
                )
            )

        avoided_severity = 0.0
        avoided_notes: list[str] = []
        if stats.events <= 1:
            avoided_severity += 0.35
            avoided_notes.append("Only one recorded learning event for this concept.")
        if days_since is not None and days_since > 10 and (score is None or score < 0.75):
            avoided_severity += 0.35
            avoided_notes.append(f"No recent practice for {days_since} days after imperfect performance.")
        if stats.common_errors and stats.events <= 2:
            avoided_severity += 0.2
            avoided_notes.append("Errors appeared but follow-up practice is sparse.")
        if avoided_severity >= 0.45:
            gaps.append(
                Gap(
                    concept=concept,
                    gap_type="avoided",
                    severity=min(1.0, avoided_severity),
                    evidence=evidence,
                    calculation_notes=avoided_notes,
                )
            )

        decaying_severity = 0.0
        decaying_notes: list[str] = []
        if days_since is not None and days_since > 21:
            decaying_severity += 0.45
            decaying_notes.append(f"Last seen {days_since} days ago.")
        if score is not None and score >= 0.7 and days_since is not None and days_since > 14:
            decaying_severity += 0.25
            decaying_notes.append("Past performance was solid but review is stale.")
        if confidence is not None and confidence < 0.6 and days_since is not None and days_since > 14:
            decaying_severity += 0.15
            decaying_notes.append("Confidence is not strong enough to ignore the stale interval.")
        if decaying_severity >= 0.45:
            gaps.append(
                Gap(
                    concept=concept,
                    gap_type="decaying",
                    severity=min(1.0, decaying_severity),
                    evidence=evidence,
                    calculation_notes=decaying_notes,
                )
            )
        return gaps

    def _days_since(self, last_seen: datetime | None) -> int | None:
        if last_seen is None:
            return None
        now = datetime.now(timezone.utc)
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        return max(0, (now - last_seen).days)

    def _evidence(self, stats: ConceptStats) -> list[str]:
        evidence = stats.summaries[:3]
        if stats.common_errors:
            evidence.append(f"Common errors: {', '.join(stats.common_errors[:3])}")
        return evidence[:4]

