from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.case import Case
from app.models.user import User
from app.schemas.result import ResultRead

router = APIRouter(prefix="/api/cases", tags=["results"])


def _get_case_or_404(case_id: int, user_id: int, db: Session) -> Case:
    case = db.query(Case).filter(Case.id == case_id, Case.user_id == user_id).first()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found.",
        )
    return case


def _empty_result_response(case: Case) -> ResultRead:
    return ResultRead(
        case_id=case.id,
        status=case.status,
        total_tumor_volume=None,
        edema_volume=None,
        enhancing_volume=None,
        non_enhancing_volume=None,
        mask_url=None,
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

    if case.result is None:
        return _empty_result_response(case)

    return ResultRead(
        case_id=case.id,
        status=case.status,
        total_tumor_volume=case.result.total_tumor_volume,
        edema_volume=case.result.edema_volume,
        enhancing_volume=case.result.enhancing_volume,
        non_enhancing_volume=case.result.non_enhancing_volume,
        mask_url=case.result.mask_url,
        slices=case.result.slices_urls,
        overlays=case.result.overlays_urls,
    )
