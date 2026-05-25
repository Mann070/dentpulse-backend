from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, admin, patients, planning, monitoring, insights
from app.routes import patient_auth, appointments, recovery, chatbot
from app.database.connection import engine, Base
import os

# Import all models so SQLAlchemy registers them before create_all
from app.models.user import User
from app.models.patient import Patient
from app.models.planning import TreatmentPlanning
from app.models.monitoring import Monitoring
from app.models.insights import Insights
from app.models.uploads import XrayUpload
from app.models.login_history import LoginHistory
from app.models.patient_account import PatientAccount
from app.models.appointment import Appointment
from app.models.prescription import Prescription
from app.models.chatbot_history import ChatbotHistory

app = FastAPI(
    title="DentPulse AI Clinical Backend",
    description="AI-Based Post-Implant Monitoring & Early Complication Prediction System",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    from sqlalchemy import text

    async with engine.begin() as conn:
        # Create all tables (new tables created, existing ones preserved)
        await conn.run_sync(Base.metadata.create_all)

        # Legacy ALTER TABLE migrations for existing tables
        legacy_migrations = [
            "ALTER TABLE users ADD COLUMN phone_number VARCHAR;",
            "ALTER TABLE users ADD COLUMN license_id VARCHAR;",
            "ALTER TABLE users ADD COLUMN is_approved BOOLEAN DEFAULT 0;",
            "ALTER TABLE users ADD COLUMN approval_status VARCHAR DEFAULT 'pending';",
            "ALTER TABLE users ADD COLUMN reset_password_otp VARCHAR;",
            "ALTER TABLE users ADD COLUMN reset_password_expiry TIMESTAMP;",
            "ALTER TABLE users ADD COLUMN otp_retry_count INTEGER DEFAULT 0;",
            "ALTER TABLE users ADD COLUMN reset_otp_retry_count INTEGER DEFAULT 0;",
            "ALTER TABLE treatment_planning ADD COLUMN doctor_id INTEGER;",
            "ALTER TABLE treatment_planning ADD COLUMN implant_recommendations VARCHAR;",
            "ALTER TABLE monitoring ADD COLUMN doctor_id INTEGER;",
            "ALTER TABLE monitoring ADD COLUMN uploaded_scan VARCHAR;",
            "ALTER TABLE monitoring ADD COLUMN cnn_result VARCHAR;",
            "ALTER TABLE monitoring ADD COLUMN svm_prediction VARCHAR;",
        ]
        for stmt in legacy_migrations:
            try:
                await conn.execute(text(stmt))
            except Exception:
                pass  # Column already exists — safe to ignore

        # Seed default Admin user if not present
        from app.utils.security import get_password_hash

        admin_email = "admin@dentpulse.com"
        result = await conn.execute(
            text(f"SELECT * FROM users WHERE email='{admin_email}';")
        )
        admin_exists = result.first()
        if not admin_exists:
            hashed_pwd = get_password_hash("admin123")
            await conn.execute(
                text(
                    f"INSERT INTO users (full_name, email, hashed_password, role, is_verified, is_approved, approval_status, created_at) "
                    f"VALUES ('System Admin', '{admin_email}', '{hashed_pwd}', 'admin', 1, 1, 'approved', CURRENT_TIMESTAMP);"
                )
            )
            print(
                "\n[DENTPULSE AI DB SEED] Seeded default Admin: admin@dentpulse.com / admin123\n"
            )


from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.database.connection import get_db
from app.services.crud import CRUDService


@app.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    patients_list = await CRUDService.get_patients(db)
    active_cases = len(patients_list)
    high_risk = sum(1 for p in patients_list if p.risk_level == "High")

    return [
        {"id": "1", "label": "Active Cases", "value": str(active_cases), "trend": "+2%", "type": "neutral"},
        {"id": "2", "label": "Recovery", "value": "94%", "trend": "+1%", "type": "success"},
        {"id": "3", "label": "Risk Alerts", "value": str(high_risk), "trend": "-1%", "type": "error"},
        {"id": "4", "label": "AI Accuracy", "value": "98.5%", "trend": "+0.5%", "type": "success"},
    ]


# ─── Clinical Routers ──────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(patients.router)
app.include_router(planning.router)
app.include_router(monitoring.router)
app.include_router(insights.router)

# ─── Patient & New Feature Routers ────────────────────────────────────────────
app.include_router(patient_auth.router)
app.include_router(appointments.router)
app.include_router(recovery.router)
app.include_router(chatbot.router)


@app.get("/")
async def root():
    return {
        "message": "DentPulse AI Backend v2.0 — Complete Ecosystem",
        "status": "Operational",
        "docs": "/docs",
    }
