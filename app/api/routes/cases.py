from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.case import Case
from app.models.patient import Patient
from app.models.user import User
from app.schemas.case import CaseCreate, CaseRead, CaseStatusRead

router = APIRouter(prefix="/api/cases", tags=["cases"])


def _get_case_or_404(case_id: int, user_id: int, db: Session) -> Case:
    case = db.query(Case).filter(Case.id == case_id, Case.user_id == user_id).first()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found.",
        )
    return case


@router.post("", response_model=CaseRead, status_code=status.HTTP_201_CREATED)
def create_case(
    payload: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Case:
    patient = (
        db.query(Patient)
        .filter(Patient.id == payload.patient_id, Patient.user_id == current_user.id)
        .first()
    )
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )

    case = Case(
        user_id=current_user.id,
        patient_id=patient.id,
        title=payload.title,
        scan_date=payload.scan_date,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.get("", response_model=list[CaseRead])
def list_cases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Case]:
    return (
        db.query(Case)
        .filter(Case.user_id == current_user.id)
        .order_by(Case.created_at.desc())
        .all()
    )


@router.get("/{case_id}", response_model=CaseRead)
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Case:
    return _get_case_or_404(case_id, current_user.id, db)


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    case = _get_case_or_404(case_id, current_user.id, db)
    db.delete(case)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{case_id}/status", response_model=CaseStatusRead)
def get_case_status(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CaseStatusRead:
    case = _get_case_or_404(case_id, current_user.id, db)
    return CaseStatusRead(
        case_id=case.id,
        status=case.status,
        task_id=case.task_id,
        error_message=case.error_message,
    )
