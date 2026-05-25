import asyncio
from app.database.connection import AsyncSessionLocal
from app.services.crud import CRUDService
from app.schemas.patient_schema import PatientCreate

# Import models so SQLAlchemy registry knows about them for relationships
from app.models.user import User
from app.models.patient import Patient
from app.models.planning import TreatmentPlanning
from app.models.monitoring import Monitoring
from app.models.insights import Insights
from app.models.uploads import XrayUpload

async def run_demo():
    print("\n--- DentPulse AI Database Demo --- \n")
    
    # 1. Create a Patient schema object
    new_patient = PatientCreate(
        patient_id="DEMO-001",
        full_name="Alice Smith",
        age=45,
        gender="Female",
        implant_site="Tooth #14",
        implant_type="Titanium Screw",
        risk_level="Low",
        notes="Demo patient created via the newly configured SQLite DB!"
    )
    
    async with AsyncSessionLocal() as db:
        print("1. Inserting a new patient into the Database...")
        # CRUDService.create_patient uses patient.dict() which creates a real Patient model 
        # and saves it to the SQLite database
        created = await CRUDService.create_patient(db, new_patient)
        print(f"Patient Created! DB ID: {created.id}, Name: {created.full_name}\n")
        
        print("2. Querying all patients from the Database...")
        patients = await CRUDService.get_patients(db)
        print(f"Total Patients found: {len(patients)}")
        for p in patients:
            print(f"   - [{p.patient_id}] {p.full_name} | Site: {p.implant_site} | Risk: {p.risk_level} | Notes: {p.notes}")
            
    print("\nDemo complete! The real Python database is fully functional.\n")

if __name__ == "__main__":
    asyncio.run(run_demo())
