from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.schemas.patient_schema import PatientCreate, PatientResponse, PatientUpdate
from app.services.crud import CRUDService
from typing import List

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.get("/", response_model=List[PatientResponse])
async def read_patients(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    patients = await CRUDService.get_patients(db, skip=skip, limit=limit)
    return patients

@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(patient: PatientCreate, db: AsyncSession = Depends(get_db)):
    return await CRUDService.create_patient(db, patient)

@router.get("/{id}", response_model=PatientResponse)
async def read_patient(id: int, db: AsyncSession = Depends(get_db)):
    patient = await CRUDService.get_patient_by_id(db, id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@router.patch("/{id}", response_model=PatientResponse)
async def update_patient(id: int, patient: PatientUpdate, db: AsyncSession = Depends(get_db)):
    updated_patient = await CRUDService.update_patient(db, id, patient)
    if not updated_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return updated_patient

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(id: int, db: AsyncSession = Depends(get_db)):
    success = await CRUDService.delete_patient(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Patient not found")
    return None
