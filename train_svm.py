import os
import pickle
import random
import json
import numpy as np
from sklearn.svm import SVC, SVR
from sklearn.preprocessing import StandardScaler

def generate_synthetic_dataset(num_records=1000):
    np.random.seed(42)
    random.seed(42)
    
    dataset = []
    
    # Range of features
    # Bone Height: 6mm -> 16mm
    # Bone Width: 3mm -> 9mm
    # Bone Density: 300 HU -> 1500 HU
    # Bite Force: 200N -> 900N
    
    bone_heights = np.random.uniform(6.0, 16.0, num_records)
    bone_widths = np.random.uniform(3.0, 9.0, num_records)
    bone_densities = np.random.uniform(300.0, 1500.0, num_records)
    bite_forces = np.random.uniform(200.0, 900.0, num_records)
    
    for i in range(num_records):
        bh = round(float(bone_heights[i]), 2)
        bw = round(float(bone_widths[i]), 2)
        bd = round(float(bone_densities[i]), 1)
        bf = round(float(bite_forces[i]), 1)
        
        # Clinical logic mapping
        if bh >= 11.5 and bw >= 5.5:
            implant_type = "Endosteal Root Form"
            # Dynamic clinically logical diameter selection
            if bw >= 6.5:
                implant_diameter = 5.0
            elif bw >= 5.0:
                implant_diameter = 4.5
            else:
                implant_diameter = 4.0
                
            # Dynamic length selection
            if bh >= 13.5:
                implant_length = 13.0
            elif bh >= 11.5:
                implant_length = 11.5
            else:
                implant_length = 10.0
                
            base_success = 93.0
            base_stability = 80.0
            risk_level = "Low"
            
        elif bh >= 9.5 and bw >= 4.0:
            implant_type = "Tapered Platform"
            if bw >= 5.0:
                implant_diameter = 4.0
            else:
                implant_diameter = 3.5
                
            if bh >= 11.0:
                implant_length = 11.5
            elif bh >= 9.5:
                implant_length = 10.0
            else:
                implant_length = 8.0
                
            base_success = 85.0
            base_stability = 70.0
            risk_level = "Moderate"
            
        else:
            implant_type = "Short Implant"
            implant_diameter = 3.5
            implant_length = 8.0
            base_success = 72.0
            base_stability = 58.0
            risk_level = "High"
            
        # Factoring in Bone Density (HU) & Bite Force (N)
        # Low density (D4 bone < 400 HU) decreases stability and success
        density_mod = 0.0
        if bd < 400:
            density_mod = -12.0
            risk_level = "High"
        elif bd < 700:
            density_mod = -5.0
        elif bd > 1200:
            density_mod = 4.0
            
        # High bite force (> 750N) increases risk of fatigue/failure
        bite_mod = 0.0
        if bf > 750:
            bite_mod = -8.0
            if risk_level == "Low":
                risk_level = "Moderate"
            elif risk_level == "Moderate":
                risk_level = "High"
        elif bf < 400:
            bite_mod = 3.0
            
        success_probability = round(base_success + density_mod + bite_mod + random.uniform(-2, 2), 1)
        stability_score = round(base_stability + (density_mod * 1.2) + (bite_mod * 0.8) + random.uniform(-3, 3), 1)
        
        # Clamp success and stability to realistic bounds
        success_probability = max(55.0, min(99.0, success_probability))
        stability_score = max(40.0, min(95.0, stability_score))
        
        # Match closest clinical tooth+implant visualization mockup
        if implant_length <= 9.0:
            implant_image = "tooth_implant_small.png"
        elif implant_diameter <= 3.7:
            implant_image = "narrow_platform_tooth.png"
        elif implant_diameter >= 4.8:
            implant_image = "tooth_implant_large.png"
        elif implant_length >= 12.0:
            implant_image = "tapered_implant_tooth.png"
        else:
            implant_image = "tooth_implant_medium.png"
                
        dataset.append({
            "bone_height": bh,
            "bone_width": bw,
            "bone_density": bd,
            "bite_force": bf,
            "implant_type": implant_type,
            "implant_diameter": float(implant_diameter),
            "implant_length": float(implant_length),
            "success_probability": float(success_probability),
            "stability_score": float(stability_score),
            "risk_level": risk_level,
            "implant_image": implant_image
        })
        
    return dataset

def train_and_save_models():
    print("Generating synthetic clinical dataset...")
    dataset = generate_synthetic_dataset(1000)
    
    # Save dataset to JSON file as required
    os.makedirs("app/models/svm", exist_ok=True)
    with open("app/models/svm/implant_dataset.json", "w") as f:
        json.dump(dataset, f, indent=2)
        
    # Extract features and targets
    X = np.array([[r["bone_height"], r["bone_width"], r["bone_density"], r["bite_force"]] for r in dataset])
    
    y_type = [r["implant_type"] for r in dataset]
    y_diam = [str(r["implant_diameter"]) for r in dataset]
    y_length = [str(r["implant_length"]) for r in dataset]
    y_success = [r["success_probability"] for r in dataset]
    y_stability = [r["stability_score"] for r in dataset]
    y_risk = [r["risk_level"] for r in dataset]
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    print("Training SVM Classifiers and Regressors...")
    
    # SVM Classifiers (RBF Kernel)
    model_type = SVC(kernel='rbf', C=10.0, gamma='scale')
    model_type.fit(X_scaled, y_type)
    
    model_diam = SVC(kernel='rbf', C=10.0, gamma='scale')
    model_diam.fit(X_scaled, y_diam)
    
    model_length = SVC(kernel='rbf', C=10.0, gamma='scale')
    model_length.fit(X_scaled, y_length)
    
    model_risk = SVC(kernel='rbf', C=10.0, gamma='scale')
    model_risk.fit(X_scaled, y_risk)
    
    # SVM Regressors (RBF Kernel)
    model_success = SVR(kernel='rbf', C=50.0, epsilon=0.1)
    model_success.fit(X_scaled, y_success)
    
    model_stability = SVR(kernel='rbf', C=50.0, epsilon=0.1)
    model_stability.fit(X_scaled, y_stability)
    
    # Save models dict
    models_payload = {
        "scaler": scaler,
        "model_type": model_type,
        "model_diam": model_diam,
        "model_length": model_length,
        "model_success": model_success,
        "model_stability": model_stability,
        "model_risk": model_risk
    }
    
    with open("app/models/svm/svm_models.pkl", "wb") as f:
        pickle.dump(models_payload, f)
        
    print("All Support Vector Machine (SVM) models trained and serialized successfully!")

if __name__ == "__main__":
    train_and_save_models()
