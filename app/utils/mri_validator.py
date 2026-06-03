from PIL import Image
import io

MIN_WIDTH  = 200
MIN_HEIGHT = 200

VALID_MODES = {"L", "RGB", "RGBA", "1", "P"}

def validate_mri_upload(file_bytes: bytes, form_data: dict) -> dict:
    result = {
        "is_valid_image": False,
        "consistency":    "no_mri",
        "honesty_flag":   "trusted",
        "notes":          "",
    }

    try:
        img = Image.open(io.BytesIO(file_bytes))
        img.verify()
        img = Image.open(io.BytesIO(file_bytes))
        width, height = img.size
        mode = img.mode
    except Exception:
        result["is_valid_image"] = False
        result["honesty_flag"]   = "unverified"
        result["consistency"]    = "invalid_image"
        result["notes"] = (
            "The uploaded file could not be read as a valid image. "
            "It may be corrupted or in an unsupported format. "
            "Manual review recommended."
        )
        return result

    if width < MIN_WIDTH or height < MIN_HEIGHT:
        result["is_valid_image"] = False
        result["honesty_flag"]   = "unverified"
        result["consistency"]    = "too_small"
        result["notes"] = (
            f"Uploaded image is too small ({width}×{height}px). "
            f"A real MRI scan is typically much larger (minimum {MIN_WIDTH}×{MIN_HEIGHT}px). "
            "This may not be a genuine medical scan."
        )
        return result

    result["is_valid_image"] = True

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

    if reported_symptoms_count == 0 and not lifestyle_risks:
        result["consistency"]  = "inconsistent"
        result["honesty_flag"] = "untrusted"
        result["notes"] = (
            "Patient uploaded an MRI scan but reported zero symptoms and no lifestyle risk factors. "
            "Completely healthy individuals rarely have MRI scans. "
            "This inconsistency has been flagged for manual medical review."
        )
        return result

    if reported_symptoms_count <= 1 and not lifestyle_risks:
        result["consistency"]  = "questionable"
        result["honesty_flag"] = "untrusted"
        result["notes"] = (
            "Patient reported minimal symptoms (1 or fewer) but uploaded an MRI. "
            "This may be inconsistent. A healthcare professional should review "
            "both the scan and the questionnaire responses."
        )
        return result

    result["consistency"]  = "consistent"
    result["honesty_flag"] = "trusted"
    result["notes"] = (
        f"Patient reported {reported_symptoms_count} symptom(s) and uploaded a valid "
        f"scan ({width}×{height}px). This is consistent — the MRI upload "
        "aligns with the reported health complaints."
    )
    return result
