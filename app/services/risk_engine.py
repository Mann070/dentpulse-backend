class RiskEngine:
    @staticmethod
    def analyze_risk(bone_loss: float, isq_score: float, pain: int, swelling: str, bleeding: str):
        # Mock Rule-based Risk Analysis
        risk_score = 0
        
        if bone_loss > 1.5:
            risk_score += 40
        if isq_score < 60:
            risk_score += 30
        if pain > 5:
            risk_score += 20
        if swelling == "High" or bleeding == "Severe":
            risk_score += 10
            
        if risk_score > 70:
            status = "High"
            alert = "Critical: Immediate intervention required"
        elif risk_score > 30:
            status = "Moderate"
            alert = "Warning: Monitor closely, check oral hygiene"
        else:
            status = "Low"
            alert = "Stable: Healing progressing as expected"
            
        return {
            "complication_risk": f"{min(risk_score, 100)}%",
            "ai_confidence": "94.2%",
            "recommendation": alert,
            "alert_level": status
        }
