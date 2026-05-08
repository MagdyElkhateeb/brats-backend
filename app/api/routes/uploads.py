from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.core.dependencies import get_current_user, get_db
from app.models.case import Case, CaseStatus
from app.models.case_file import CaseFile, SequenceType
from app.models.user import User
from app.services.storage_service import is_nii_gz_filename, save_upload_file
from app.tasks.inference_tasks import process_case_inference

router = APIRouter(prefix="/api/cases", tags=["uploads"])

EXPECTED_UPLOAD_FIELDS = {"t1", "t1ce", "t2", "flair"}
SEQUENCE_MAP = {
    "t1": SequenceType.T1,
    "t1ce": SequenceType.T1CE,
    "t2": SequenceType.T2,
    "flair": SequenceType.FLAIR,
}


def _get_case_or_404(case_id: int, user_id: int, db: Session) -> Case:
    case = db.query(Case).filter(Case.id == case_id, Case.user_id == user_id).first()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found.",
        )
    return case


async def _ensure_exact_upload_fields(request: Request) -> None:
    form = await request.form()
    file_fields = [
        key for key, value in form.multi_items() if isinstance(value, StarletteUploadFile)
    ]
    if set(form.keys()) != EXPECTED_UPLOAD_FIELDS or set(file_fields) != EXPECTED_UPLOAD_FIELDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload must include exactly four file fields: t1, t1ce, t2, flair.",
        )
    if len(file_fields) != len(EXPECTED_UPLOAD_FIELDS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate upload fields are not allowed.",
        )


@router.post("/{case_id}/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_case_files(
    case_id: int,
    request: Request,
    t1: UploadFile = File(...),
    t1ce: UploadFile = File(...),
    t2: UploadFile = File(...),
    flair: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    await _ensure_exact_upload_fields(request)

    case = _get_case_or_404(case_id, current_user.id, db)
    if case.status == CaseStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Case is already processing.",
        )

    uploads = {"t1": t1, "t1ce": t1ce, "t2": t2, "flair": flair}
    invalid_fields = [
        field
        for field, upload in uploads.items()
        if upload.filename is None or not is_nii_gz_filename(upload.filename)
    ]
    if invalid_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All uploaded files must end with .nii.gz.",
        )

    db.query(CaseFile).filter(CaseFile.case_id == case.id).delete(synchronize_session=False)

    for field, upload in uploads.items():
        saved_path = await save_upload_file(case.id, field, upload)
        db.add(
            CaseFile(
                case_id=case.id,
                sequence_type=SEQUENCE_MAP[field],
                file_path=str(saved_path),
                original_filename=upload.filename or f"{field}.nii.gz",
            )
        )

    case.status = CaseStatus.PROCESSING
    case.error_message = None

    try:
        task = process_case_inference.delay(case.id)
    except Exception as exc:
        case.status = CaseStatus.FAILED
        case.error_message = "Could not enqueue inference task."
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not enqueue inference task.",
        ) from exc

    case.task_id = task.id
    db.commit()

    return {
        "case_id": case.id,
        "status": case.status,
        "task_id": case.task_id,
        "message": "Upload accepted. Inference processing has started.",
    }
