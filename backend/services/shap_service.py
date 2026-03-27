"""SHAP helper utilities."""

from __future__ import annotations


def explain_action_message(risk_level: str, top_feature: str | None) -> str:
    if risk_level == "high":
        if top_feature:
            return f"High risk detected. Primary contributor: {top_feature}. Urgent referral recommended."
        return "High risk detected. Urgent referral recommended."
    if risk_level == "mid":
        return "Moderate risk detected. Repeat vitals and consult provider soon."
    return "Low risk currently. Continue routine monitoring and follow-up."
