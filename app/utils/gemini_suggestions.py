# app/utils/gemini_suggestions.py
"""
Gemini AI Health Suggestions
==============================
Uses Google Gemini (free tier) to generate personalized health advice.
Falls back to the rule-based engine if Gemini is unavailable.

Setup:
  pip install google-generativeai
  Add to .env: GEMINI_API_KEY=your_key_here

Get free API key: https://makersuite.google.com/app/apikey
(Completely free — no billing needed for basic use)

Explain in viva:
  "We use Google Gemini's free generative AI API to generate personalized
   health suggestions based on the patient's predicted disease and reported
   symptoms. Unlike our rule-based engine, Gemini can synthesize context-aware
   advice that adapts to the specific combination of conditions."
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Try importing Gemini — graceful fallback if not installed
try:
    import google.generativeai as genai
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
    GEMINI_AVAILABLE = bool(GEMINI_API_KEY)
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠  google-generativeai not installed. Using rule-based suggestions.")


def get_ai_suggestions(
    predicted_disease: str,
    risk_level: str,
    form_data: dict | None = None
) -> dict:
    """
    Get personalized health suggestions using Gemini AI.

    Args:
        predicted_disease: e.g. "Heart Disease"
        risk_level: "low" | "medium" | "high"
        form_data: optional dict of patient form answers for context

    Returns:
        {"precautions": [...], "improvements": [...], "source": "gemini"|"rules"}
    """
    if not GEMINI_AVAILABLE:
        from app.utils.suggestion_engine import get_suggestions
        result = get_suggestions(predicted_disease)
        result["source"] = "rules"
        return result

    try:
        return _call_gemini(predicted_disease, risk_level, form_data or {})
    except Exception as e:
        print(f"⚠  Gemini call failed: {e}. Falling back to rules.")
        from app.utils.suggestion_engine import get_suggestions
        result = get_suggestions(predicted_disease)
        result["source"] = "rules"
        return result


def _call_gemini(disease: str, risk: str, data: dict) -> dict:
    """Make actual Gemini API call with structured prompt."""

    # Build context from form data
    context_parts = []
    if data.get("smoker"):         context_parts.append("patient is a smoker")
    if data.get("alcohol_use"):    context_parts.append("consumes alcohol")
    if data.get("blood_pressure") == "high": context_parts.append("has high BP")
    if data.get("blood_sugar") == "high":    context_parts.append("has high blood sugar")
    if data.get("exercise_frequency") == "never": context_parts.append("does not exercise")
    if data.get("diet_quality") == "poor":   context_parts.append("has a poor diet")
    if data.get("family_history_heart"):     context_parts.append("family history of heart disease")
    if data.get("family_history_diabetes"):  context_parts.append("family history of diabetes")

    context_str = (", ".join(context_parts) + ".") if context_parts else "no additional context."

    prompt = f"""You are a medical assistant AI. A patient in India has been assessed.

Predicted condition: {disease}
Risk level: {risk}
Patient context: {context_str}

Generate practical, specific health advice for this Indian patient. 
Respond ONLY with a JSON object in this exact format (no markdown, no explanation):
{{
  "precautions": ["precaution 1", "precaution 2", "precaution 3", "precaution 4", "precaution 5"],
  "improvements": ["improvement 1", "improvement 2", "improvement 3", "improvement 4", "improvement 5"]
}}

Rules:
- Precautions: immediate actions to take or avoid
- Improvements: long-term lifestyle changes
- Keep each item under 80 characters
- Be specific to Indian context (mention Indian foods, hospitals, costs)
- No markdown formatting, no asterisks, no numbered lists inside strings"""

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    text = response.text.strip()

    # Clean any markdown fences
    text = text.replace("```json", "").replace("```", "").strip()

    parsed = json.loads(text)
    parsed["source"] = "gemini"
    return parsed


def get_insurance_ai_explanation(
    annual_premium: int,
    risk_factors: list,
    predicted_disease: str
) -> str:
    """
    Use Gemini to generate a plain-language explanation of the insurance price.
    Falls back to a template string.
    """
    if not GEMINI_AVAILABLE:
        return _template_explanation(annual_premium, risk_factors, predicted_disease)

    try:
        factors_str = ", ".join(risk_factors[:4]) if risk_factors else "standard health profile"
        prompt = f"""An Indian health insurance system has calculated an annual premium of 
₹{annual_premium:,} for a patient with: {factors_str}.
Predicted health condition: {predicted_disease}.

Write 2 sentences (max 60 words total) explaining WHY this premium was calculated, 
in simple language an Indian patient can understand. No markdown, no bullet points."""

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return _template_explanation(annual_premium, risk_factors, predicted_disease)


def _template_explanation(premium: int, factors: list, disease: str) -> str:
    top = factors[0] if factors else "your health profile"
    return (
        f"Your estimated annual premium of ₹{premium:,} is calculated based on "
        f"your health assessment showing {disease}. The primary factor is {top.lower()}."
    )