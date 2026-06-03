import os
import json
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

GEMINI_AVAILABLE = False
genai_client = None

try:
    from google import genai
    if GEMINI_API_KEY:
        genai_client = genai.Client(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
except ImportError:
    try:
        import google.generativeai as genai_legacy
        if GEMINI_API_KEY:
            genai_legacy.configure(api_key=GEMINI_API_KEY)
            GEMINI_AVAILABLE = True
            genai_client = "legacy"
    except ImportError:
        print("[WARN] google-genai not installed. Using rule-based suggestions.")


def get_ai_suggestions(
    predicted_disease: str,
    risk_level: str,
    form_data: dict | None = None
) -> dict:
    if not GEMINI_AVAILABLE:
        from app.utils.suggestion_engine import get_suggestions
        result = get_suggestions(predicted_disease)
        result["source"] = "rules"
        return result

    try:
        return _call_gemini(predicted_disease, risk_level, form_data or {})
    except Exception as e:
        print(f"[WARN] Gemini call failed: {e}. Falling back to rules.")
        from app.utils.suggestion_engine import get_suggestions
        result = get_suggestions(predicted_disease)
        result["source"] = "rules"
        return result


def _call_gemini(disease: str, risk: str, data: dict) -> dict:
    context_parts = []
    if data.get("smoker"):         context_parts.append("patient is a smoker")
    if data.get("alcohol_use"):    context_parts.append("consumes alcohol")
    if data.get("blood_pressure") == "high": context_parts.append("has high BP")
    if data.get("blood_sugar") == "high":    context_parts.append("has high blood sugar")
    if data.get("exercise_frequency") == "never": context_parts.append("does not exercise")
    if data.get("diet_quality") == "poor":   context_parts.append("has a poor diet")
    if data.get("family_history_heart"):     context_parts.append("family history of heart disease")
    if data.get("family_history_diabetes"):  context_parts.append("family history of diabetes")

    context_str = (", ".join(context_parts) + ".") if context_parts else "no specific risk context."

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

    text = ""
    if genai_client == "legacy":
        import google.generativeai as genai_legacy
        model    = genai_legacy.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        text     = response.text.strip()
    else:
        response = genai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        text = response.text.strip()

    text = text.replace("```json", "").replace("```", "").strip()

    parsed = json.loads(text)
    parsed["source"] = "gemini"
    return parsed


def get_insurance_ai_explanation(
    annual_premium: int,
    risk_factors: list,
    predicted_disease: str
) -> str:
    if not GEMINI_AVAILABLE:
        return _template_explanation(annual_premium, risk_factors, predicted_disease)

    try:
        factors_str = ", ".join(risk_factors[:4]) if risk_factors else "no specific risk factors"
        prompt = f"""An Indian health insurance system has calculated an annual premium of 
Rs.{annual_premium:,} for a patient with: {factors_str}.
Predicted health condition: {predicted_disease}.

Write 2 sentences (max 60 words total) explaining WHY this premium was calculated, 
in simple language an Indian patient can understand. No markdown, no bullet points."""

        if genai_client == "legacy":
            import google.generativeai as genai_legacy
            model    = genai_legacy.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return response.text.strip()
        else:
            response = genai_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            return response.text.strip()

    except Exception:
        return _template_explanation(annual_premium, risk_factors, predicted_disease)


def _template_explanation(premium: int, factors: list, disease: str) -> str:
    top = factors[0] if factors else "general health"
    return (
        f"Your estimated annual premium of Rs.{premium:,} is calculated based on "
        f"your health assessment showing {disease}. The primary factor is {top.lower()}."
    )
