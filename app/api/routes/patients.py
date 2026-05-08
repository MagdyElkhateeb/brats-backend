from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.patient import Patient
from app.models.user import User
from app.schemas.patient import PatientCreate, PatientRead, PatientUpdate

router = APIRouter(prefix="/api/patients", tags=["patients"])


def _get_patient_or_404(patient_id: int, user_id: int, db: Session) -> Patient:
    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id, Patient.user_id == user_id)
        .first()
    )
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )
    return patient


def _patient_code_exists(code: str, user_id: int, db: Session, exclude_id: int | None = None) -> bool:
    query = db.query(Patient).filter(Patient.patient_code == code, Patient.user_id == user_id)
    if exclude_id is not None:
        query = query.filter(Patient.id != exclude_id)
    return query.first() is not None


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
def create_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Patient:
    if _patient_code_exists(payload.patient_code, current_user.id, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient code already exists for this user.",
        )

    patient = Patient(user_id=current_user.id, **payload.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("", response_model=list[PatientRead])
def list_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Patient]:
    return (
        db.query(Patient)
        .filter(Patient.user_id == current_user.id)
        .order_by(Patient.created_at.desc())
        .all()
    )


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Patient:
    return _get_patient_or_404(patient_id, current_user.id, db)


@router.put("/{patient_id}", response_model=PatientRead)
def update_patient(
    patient_id: int,
    payload: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Patient:
    patient = _get_patient_or_404(patient_id, current_user.id, db)
    updates = payload.model_dump(exclude_unset=True)

    new_code = updates.get("patient_code")
    if new_code and _patient_code_exists(new_code, current_user.id, db, exclude_id=patient.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient code already exists for this user.",
        )

    for field, value in updates.items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)
    return patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    patient = _get_patient_or_404(patient_id, current_user.id, db)
    db.delete(patient)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
