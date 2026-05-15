# app/models/insurance_rules.py
"""
Insurance Plan Rules
=====================
Pure rule-based engine — no ML needed.
Maps risk_level → insurance plan details.

Easy to explain in viva:
  "Low risk → basic plan, Medium → standard, High → premium.
   The plan details are defined as a dictionary.
   This is a classic rule-based expert system."
"""

# ── All available plans ────────────────────────────────────────────────
INSURANCE_PLANS = {
    "basic": {
        "plan_name":  "BasicCare Shield",
        "plan_type":  "basic",
        "monthly_cost": "₹499",
        "coverage": [
            "OPD consultations up to ₹5,000/year",
            "Hospitalisation up to ₹1 Lakh",
            "Annual preventive health checkup",
            "Ambulance cover up to ₹2,000",
        ],
        "reason": (
            "Your health assessment shows a low risk profile. "
            "A basic plan covers routine needs and preventive care "
            "without overpaying for coverage you may not need."
        ),
    },

    "standard": {
        "plan_name":  "MedPlus Standard",
        "plan_type":  "standard",
        "monthly_cost": "₹1,199",
        "coverage": [
            "OPD + specialist consultations",
            "Hospitalisation up to ₹3 Lakh",
            "Diagnostic tests (blood work, scans) covered",
            "Cashless at 500+ hospitals nationwide",
            "Ambulance cover up to ₹5,000",
            "Pre & post hospitalisation (30/60 days)",
        ],
        "reason": (
            "Your assessment shows a moderate risk profile. "
            "The standard plan gives you diagnostic coverage and specialist access "
            "to monitor and manage your health proactively."
        ),
    },

    "premium": {
        "plan_name":  "SecureHealth Premium",
        "plan_type":  "premium",
        "monthly_cost": "₹2,499",
        "coverage": [
            "Unlimited OPD visits",
            "Hospitalisation up to ₹10 Lakh",
            "Critical illness cover (Heart, Cancer, Kidney failure)",
            "Cashless at 1,000+ hospitals nationwide",
            "Ambulance + ICU coverage",
            "Mental health consultations",
            "International emergency cover",
        ],
        "reason": (
            "Your assessment shows a high risk profile. "
            "The premium plan provides comprehensive protection including critical illness cover, "
            "which is essential given your predicted condition and risk factors."
        ),
    },
}

# ── Risk level → plan key mapping ─────────────────────────────────────
_RISK_TO_PLAN = {
    "low":    "basic",
    "medium": "standard",
    "high":   "premium",
}


def suggest_insurance(risk_level: str) -> dict:
    """
    Returns the recommended insurance plan dict based on risk level.

    Args:
        risk_level: one of 'low', 'medium', 'high'

    Returns:
        Full plan dict from INSURANCE_PLANS
    """
    plan_key = _RISK_TO_PLAN.get(risk_level, "basic")
    return INSURANCE_PLANS[plan_key]
