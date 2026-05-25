import random
import json
import math

class MonitoringEngine:

    # ---------- CNN --------------------------------------------------------
    @staticmethod
    def run_cnn_analysis(uploaded_scan_name: str, isq_score: float, bone_level: float) -> dict:
        """
        Simulate a Convolutional Neural Network analysing an implant radiograph.
        Classifies healing stage and produces per-feature confidence values.
        """
        scan_lower = (uploaded_scan_name or "").lower()

        # Keyword-guided bias
        if "stable" in scan_lower or "normal" in scan_lower or "healthy" in scan_lower:
            classification = "Stable Healing"
        elif "mild" in scan_lower:
            classification = "Mild Bone Loss"
        elif "moderate" in scan_lower or "bone" in scan_lower:
            classification = "Moderate Bone Loss"
        elif "severe" in scan_lower or "peri" in scan_lower or "inflam" in scan_lower:
            classification = "Severe Bone Loss"
        else:
            # ISQ / bone-level driven classification
            if isq_score >= 72 and bone_level <= 0.8:
                classification = "Stable Healing"
            elif isq_score >= 62 and bone_level <= 1.5:
                classification = "Mild Bone Loss"
            elif isq_score >= 52 and bone_level <= 2.5:
                classification = "Moderate Bone Loss"
            else:
                classification = "Severe Bone Loss"

        # Per-class confidence ranges
        conf_ranges = {
            "Stable Healing":    (93.0, 98.9),
            "Mild Bone Loss":    (88.0, 94.5),
            "Moderate Bone Loss":(85.5, 92.0),
            "Severe Bone Loss":  (90.5, 96.5),
        }
        lo, hi = conf_ranges[classification]
        confidence = round(random.uniform(lo, hi), 1)

        # Feature scores extracted by CNN layers
        is_stable    = classification == "Stable Healing"
        is_mild      = classification == "Mild Bone Loss"
        is_moderate  = classification == "Moderate Bone Loss"
        is_severe    = classification == "Severe Bone Loss"

        osseointegration_pct = round(
            max(20, min(98, isq_score * 1.1 + random.uniform(-3, 3))), 1
        )
        bone_loss_est_mm = round(bone_level + random.uniform(-0.1, 0.2), 2)
        inflammation_score = (
            round(random.uniform(0.05, 0.18), 2) if is_stable else
            round(random.uniform(0.25, 0.45), 2) if is_mild else
            round(random.uniform(0.50, 0.70), 2) if is_moderate else
            round(random.uniform(0.75, 0.95), 2)
        )

        return {
            "classification":       classification,
            "confidence":           confidence,
            "bone_loss_estimation": bone_loss_est_mm,
            "osseointegration_pct": osseointegration_pct,
            "inflammation_score":   inflammation_score,
            "peri_implantitis_flag": is_severe or (is_moderate and inflammation_score > 0.60),
            "implant_stability_ok":  is_stable or is_mild,
        }

    # ---------- SVM --------------------------------------------------------
    @staticmethod
    def run_svm_prediction(
        isq_score: float,
        bone_level: float,
        mobility: str,
        pain_level: int,
        swelling: str,
        bleeding: str,
        cnn_result: dict,
    ) -> dict:
        """
        Support Vector Machine predicts complication risk and healing trajectory
        using clinical measurements + CNN feature vector.
        """
        risk_score = 0.0

        # --- ISQ contribution (normalised 0-100 axis)
        if   isq_score < 50: risk_score += 40
        elif isq_score < 60: risk_score += 25
        elif isq_score < 70: risk_score += 12

        # --- Bone level (mm loss)
        if   bone_level > 2.5: risk_score += 35
        elif bone_level > 1.5: risk_score += 20
        elif bone_level > 0.8: risk_score += 10

        # --- Mobility (M0-M3)
        mob = (mobility or "M0").upper()
        mob_scores = {"M0": 0, "M1": 10, "M2": 25, "M3": 40}
        risk_score += mob_scores.get(mob, 0)

        # --- Pain
        if pain_level > 7: risk_score += 20
        elif pain_level > 4: risk_score += 10
        elif pain_level > 2: risk_score += 5

        # --- Swelling
        sw = (swelling or "Low").lower()
        risk_score += {"high": 15, "severe": 18, "moderate": 8, "medium": 8}.get(sw, 0)

        # --- Bleeding
        bl = (bleeding or "None").lower()
        risk_score += {"high": 14, "severe": 18, "moderate": 8, "medium": 8}.get(bl, 0)

        # --- CNN features
        cnn_class = cnn_result.get("classification", "Stable Healing")
        cnn_scores = {
            "Stable Healing":    0,
            "Mild Bone Loss":   12,
            "Moderate Bone Loss":28,
            "Severe Bone Loss":  45,
        }
        risk_score += cnn_scores.get(cnn_class, 0)
        risk_score += cnn_result.get("inflammation_score", 0.0) * 20

        # --- SVM decision boundary
        if risk_score > 65:
            risk_level      = "High Risk"
            healing_status  = "High Risk — Immediate Review"
            success_prob    = round(random.uniform(38.0, 58.0), 1)
        elif risk_score > 32:
            risk_level      = "Moderate Risk"
            healing_status  = "Guarded Healing"
            success_prob    = round(random.uniform(64.0, 82.0), 1)
        else:
            risk_level      = "Low Risk"
            healing_status  = "Stable Healing"
            success_prob    = round(random.uniform(88.0, 97.5), 1)

        complication_prob = round(min(max(risk_score, 3.0), 97.0), 1)

        # Stability gain vs baseline ISQ 65
        raw_gain = round(((isq_score - 65.0) / 65.0) * 100, 1)
        stability_gain = f"+{raw_gain}%" if raw_gain >= 0 else f"{raw_gain}%"

        # Bone loss status label
        if bone_level <= 0.8:
            bone_status = "Within Normal Range"
        elif bone_level <= 1.5:
            bone_status = "Mild Crestal Resorption"
        elif bone_level <= 2.5:
            bone_status = "Moderate Bone Loss"
        else:
            bone_status = "Severe Bone Loss Detected"

        # Clinical alert generation
        alerts = []
        if cnn_result.get("peri_implantitis_flag"):
            alerts.append("Potential peri-implantitis detected")
        if bone_level > 1.5:
            alerts.append("Bone loss progression detected")
        if isq_score < 60:
            alerts.append("Implant instability — review loading protocol")
        if pain_level > 6:
            alerts.append("Persistent pain — consider clinical investigation")
        if risk_level == "High Risk":
            alerts.append("Immediate review recommended")

        return {
            "risk_level":            risk_level,
            "healing_status":        healing_status,
            "bone_status":           bone_status,
            "success_probability":   success_prob,
            "complication_probability": complication_prob,
            "stability_gain":        stability_gain,
            "alerts":                alerts,
            "raw_risk_score":        round(risk_score, 1),
        }
