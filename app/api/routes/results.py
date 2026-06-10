from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.case import Case
from app.models.case_file import CaseFile, SequenceType
from app.models.user import User
from app.schemas.result import ResultModalities, ResultRead
from app.services.storage_service import path_to_storage_url

router = APIRouter(prefix="/api/cases", tags=["results"])

MODALITY_KEY_BY_SEQUENCE = {
    SequenceType.T1: "t1",
    SequenceType.T1CE: "t1ce",
    SequenceType.T2: "t2",
    SequenceType.FLAIR: "flair",
}


def _get_case_or_404(case_id: int, user_id: int, db: Session) -> Case:
    case = db.query(Case).filter(Case.id == case_id, Case.user_id == user_id).first()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found.",
        )
    return case


def _frontend_file_url(file_path: str) -> str:
    normalized_path = file_path.replace("\\", "/")
    if normalized_path.startswith(("/storage/", "http://", "https://")):
        return normalized_path
    return path_to_storage_url(file_path)


def _build_modalities(case_files: list[CaseFile]) -> ResultModalities:
    modalities: dict[str, str | None] = {
        "t1": None,
        "t1ce": None,
        "t2": None,
        "flair": None,
    }
    for case_file in case_files:
        key = MODALITY_KEY_BY_SEQUENCE.get(case_file.sequence_type)
        if key is not None:
            modalities[key] = _frontend_file_url(case_file.file_path)
    return ResultModalities(**modalities)


def _empty_result_response(case: Case, modalities: ResultModalities) -> ResultRead:
    return ResultRead(
        case_id=case.id,
        status=case.status,
        total_tumor_volume=None,
        edema_volume=None,
        enhancing_volume=None,
        non_enhancing_volume=None,
        mask_url=None,
        modalities=modalities,
        slices=[],
        overlays=[],
    )


@router.get("/{case_id}/results", response_model=ResultRead)
def get_case_results(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResultRead:
    case = _get_case_or_404(case_id, current_user.id, db)
    case_files = db.query(CaseFile).filter(CaseFile.case_id == case.id).all()
    modalities = _build_modalities(case_files)

    if case.result is None:
        return _empty_result_response(case, modalities)

    return ResultRead(
        case_id=case.id,
        status=case.status,
        total_tumor_volume=case.result.total_tumor_volume,
        edema_volume=case.result.edema_volume,
        enhancing_volume=case.result.enhancing_volume,
        non_enhancing_volume=case.result.non_enhancing_volume,
        mask_url=case.result.mask_url,
        modalities=modalities,
        slices=[],
        overlays=[],
    )
