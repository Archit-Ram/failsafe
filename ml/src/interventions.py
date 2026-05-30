"""Rule-based intervention generator driven by SHAP attributions.

Given the top SHAP contributions for a single student, this returns a
ranked list of personalised interventions (extra classes, counselling,
study-plan tweaks). The rules are deliberately transparent so faculty
can audit *why* each suggestion was made.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Intervention:
    title: str
    detail: str
    category: str  # academic | wellbeing | engagement | family

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "detail": self.detail,
            "category": self.category,
        }


def _rule(feature: str, value: float, shap_value: float) -> Intervention | None:
    """Map a (feature, raw value, shap impact) tuple to a concrete action.

    `shap_value > 0` means the feature pushed the prediction *toward*
    at-risk; we only suggest interventions for risk-increasing features.
    """
    if shap_value <= 0:
        return None

    f = feature.lower()
    if f.startswith("absences"):
        return Intervention(
            title="Attendance recovery plan",
            detail=(
                f"Student has {int(value)} absences. Schedule a 1:1 with the class "
                "advisor, set a weekly attendance target, and enrol them in catch-up "
                "tutorials for missed lectures."
            ),
            category="engagement",
        )
    if f.startswith("failures"):
        return Intervention(
            title="Remedial coursework",
            detail=(
                f"{int(value)} prior subject failures. Pair with a peer mentor and "
                "assign 2x weekly remedial sessions focused on prerequisite topics."
            ),
            category="academic",
        )
    if f.startswith("studytime"):
        return Intervention(
            title="Structured study plan",
            detail=(
                "Low reported study time. Co-design a weekly study calendar with "
                "Pomodoro blocks and accountability check-ins via the LMS."
            ),
            category="academic",
        )
    if f.startswith("dalc") or f.startswith("walc"):
        return Intervention(
            title="Wellbeing & counselling referral",
            detail=(
                "Elevated alcohol-consumption signal. Refer to the campus "
                "counsellor for a confidential wellbeing screening and connect "
                "the student with peer support groups."
            ),
            category="wellbeing",
        )
    if f.startswith("goout"):
        return Intervention(
            title="Social-balance coaching",
            detail=(
                "High 'going out' frequency. Discuss time-management strategies "
                "and recommend academic-focused clubs to redirect engagement."
            ),
            category="wellbeing",
        )
    if f.startswith("health"):
        return Intervention(
            title="Health follow-up",
            detail=(
                "Self-reported health is poor. Coordinate with the medical wing "
                "for a check-up and adjust deadlines if a chronic issue is found."
            ),
            category="wellbeing",
        )
    if f.startswith("schoolsup_no"):
        return Intervention(
            title="Enrol in extra school support",
            detail=(
                "Student is not currently receiving school support classes. "
                "Auto-enrol them in the next available remediation cohort."
            ),
            category="academic",
        )
    if f.startswith("higher_no"):
        return Intervention(
            title="Career counselling",
            detail=(
                "Student does not plan to pursue higher education. A career "
                "counselling session can clarify long-term goals and motivation."
            ),
            category="engagement",
        )
    if f.startswith("famsup_no") or f.startswith("pstatus_a"):
        return Intervention(
            title="Family liaison meeting",
            detail=(
                "Limited family academic support detected. The faculty mentor "
                "should set up a parent/guardian touch-point this fortnight."
            ),
            category="family",
        )
    if f.startswith("internet_no"):
        return Intervention(
            title="Provide digital access",
            detail=(
                "No home internet access. Issue a campus hotspot loaner and "
                "share offline copies of the LMS materials."
            ),
            category="engagement",
        )
    if f.startswith("traveltime"):
        return Intervention(
            title="Logistics support",
            detail=(
                "Long commute time. Offer hostel allotment / hybrid attendance "
                "arrangements during exam-prep weeks."
            ),
            category="engagement",
        )
    if f.startswith("freetime"):
        return Intervention(
            title="Engagement plan",
            detail=(
                "Free-time pattern correlates with disengagement. Recommend "
                "structured project work or a research-mentorship slot."
            ),
            category="engagement",
        )
    return Intervention(
        title=f"Mentor review: {feature}",
        detail=(
            "This factor is materially raising the risk score. Flag it for "
            "discussion in the next mentor meeting."
        ),
        category="academic",
    )


def generate(
    contributions: Iterable[tuple[str, float, float]],
    top_k: int = 4,
) -> list[dict]:
    """`contributions` items: (feature_name, raw_value, shap_value)."""
    seen: set[str] = set()
    out: list[dict] = []
    ranked = sorted(contributions, key=lambda t: t[2], reverse=True)
    for feat, val, shap_val in ranked:
        rec = _rule(feat, val, shap_val)
        if rec is None:
            continue
        if rec.title in seen:
            continue
        seen.add(rec.title)
        out.append(rec.to_dict() | {"driver": feat, "impact": float(shap_val)})
        if len(out) >= top_k:
            break
    if not out:
        out.append(
            Intervention(
                title="Routine monitoring",
                detail=(
                    "No dominant risk factor identified. Continue regular "
                    "mentor check-ins and re-score after the next assessment."
                ),
                category="engagement",
            ).to_dict()
            | {"driver": "baseline", "impact": 0.0}
        )
    return out
