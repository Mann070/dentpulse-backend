from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.patient import Patient
from app.models.user import User
from app.schemas.patient_schema import PatientCreate, PatientUpdate
from app.utils.security import get_password_hash

class CRUDService:
    @staticmethod
    async def get_patients(db: AsyncSession, skip: int = 0, limit: int = 100):
        result = await db.execute(select(Patient).offset(skip).limit(limit).order_by(Patient.created_at.desc()))
        return result.scalars().all()

    @staticmethod
    async def create_patient(db: AsyncSession, patient: PatientCreate):
        db_patient = Patient(**patient.dict())
        db.add(db_patient)
        await db.commit()
        await db.refresh(db_patient)
        return db_patient

    @staticmethod
    async def get_patient_by_id(db: AsyncSession, patient_id: int):
        result = await db.execute(select(Patient).filter(Patient.id == patient_id))
        return result.scalars().first()

    @staticmethod
    async def update_patient(db: AsyncSession, patient_id: int, patient_update: PatientUpdate):
        db_patient = await CRUDService.get_patient_by_id(db, patient_id)
        if not db_patient:
            return None
        
        update_data = patient_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_patient, key, value)
        
        await db.commit()
        await db.refresh(db_patient)
        return db_patient

    @staticmethod
    async def delete_patient(db: AsyncSession, patient_id: int):
        db_patient = await CRUDService.get_patient_by_id(db, patient_id)
        if not db_patient:
            return False
        await db.delete(db_patient)
        await db.commit()
        return True
