# app/utils/mri_validator.py
"""
MRI Validator — Lie Detection Module
======================================
Analyses an uploaded MRI/scan file and cross-checks it against the
patient's self-reported symptoms to detect inconsistencies.

Three detection checks (explain in viva):
  1. Image validity   — Is this a real image, and is it large enough to be a scan?
  2. Symptom mismatch — Patient uploaded MRI but reported zero symptoms?
  3. Format check     — Is the file a recognisable image format at all?

Why this is not 'true' AI lie detection:
  We are not reading the MRI clinically. We are checking logical consistency:
  "If you are healthy enough to have no symptoms, why do you have an MRI?"
  This is a behavioural flag, not a medical diagnosis.
"""

from PIL import Image
import io


# ── Minimum size to be considered a real scan (pixels) ────────────────
MIN_WIDTH  = 200
MIN_HEIGHT = 200

# ── Allowed image modes for medical scans ─────────────────────────────
VALID_MODES = {"L", "RGB", "RGBA", "1", "P"}   # greyscale + colour


def validate_mri_upload(file_bytes: bytes, form_data: dict) -> dict:
    """
    Validate an uploaded MRI file and check consistency with form answers.

    Args:
        file_bytes: raw bytes of the uploaded file
        form_data:  dict of patient form answers (from patient.py)

    Returns:
        {
            "is_valid_image": bool,
            "consistency":    "consistent" | "inconsistent" | "no_mri",
            "honesty_flag":   "trusted" | "review_needed",
            "notes":          str   (human-readable explanation)
        }
    """
    result = {
        "is_valid_image": False,
        "consistency":    "no_mri",
        "honesty_flag":   "trusted",
        "notes":          "",
    }

    # ── Check 1: Can we open this as an image at all? ──────────────────
    try:
        img = Image.open(io.BytesIO(file_bytes))
        img.verify()                    # Checks file integrity
        img = Image.open(io.BytesIO(file_bytes))  # Re-open after verify()
        width, height = img.size
        mode = img.mode
    except Exception:
        result["is_valid_image"] = False
        result["honesty_flag"]   = "review_needed"
        result["consistency"]    = "inconsistent"
        result["notes"] = (
            "The uploaded file could not be read as a valid image. "
            "It may be corrupted or in an unsupported format. "
            "Manual review recommended."
        )
        return result

    # ── Check 2: Is the image large enough to be a real scan? ──────────
    if width < MIN_WIDTH or height < MIN_HEIGHT:
        result["is_valid_image"] = False
        result["honesty_flag"]   = "review_needed"
        result["consistency"]    = "inconsistent"
        result["notes"] = (
            f"Uploaded image is too small ({width}×{height}px). "
            f"A real MRI scan is typically much larger (minimum {MIN_WIDTH}×{MIN_HEIGHT}px). "
            "This may not be a genuine medical scan."
        )
        return result

    # ── Image is structurally valid ────────────────────────────────────
    result["is_valid_image"] = True

    # ── Check 3: Symptom consistency check (lie detection logic) ───────
    symptom_fields = [
        "fever", "cough", "chest_pain", "shortness_of_breath",
        "fatigue", "headache", "joint_pain", "skin_rash",
        "nausea", "weight_loss",
    ]
    reported_symptoms_count = sum(
        1 for f in symptom_fields if form_data.get(f, False)
    )

    lifestyle_risks = (
        form_data.get("smoker", False) or
        form_data.get("alcohol_use", False) or
        form_data.get("blood_pressure") == "high" or
        form_data.get("blood_sugar") == "high" or
        form_data.get("family_history_heart", False) or
        form_data.get("family_history_diabetes", False)
    )

    # ── Scenario A: Zero symptoms + MRI uploaded = suspicious ──────────
    if reported_symptoms_count == 0 and not lifestyle_risks:
        result["consistency"]  = "inconsistent"
        result["honesty_flag"] = "review_needed"
        result["notes"] = (
            "Patient uploaded an MRI scan but reported zero symptoms and no lifestyle risk factors. "
            "Completely healthy individuals rarely have MRI scans. "
            "This inconsistency has been flagged for manual medical review."
        )
        return result

    # ── Scenario B: Very few symptoms but MRI uploaded ──────────────────
    if reported_symptoms_count <= 1 and not lifestyle_risks:
        result["consistency"]  = "inconsistent"
        result["honesty_flag"] = "review_needed"
        result["notes"] = (
            "Patient reported minimal symptoms (1 or fewer) but uploaded an MRI. "
            "This may be inconsistent. A healthcare professional should review "
            "both the scan and the questionnaire responses."
        )
        return result

    # ── Scenario C: Consistent — symptoms match MRI upload ─────────────
    result["consistency"]  = "consistent"
    result["honesty_flag"] = "trusted"
    result["notes"] = (
        f"Patient reported {reported_symptoms_count} symptom(s) and uploaded a valid "
        f"scan ({width}×{height}px). This is consistent — the MRI upload "
        "aligns with the reported health complaints."
    )
    return result
