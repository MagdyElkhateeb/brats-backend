from pathlib import Path

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.case import Case, CaseStatus
from app.models.case_file import CaseFile, SequenceType
from app.models.case_result import CaseResult
from app.services.model_client import ModelClientError, call_model_endpoint
from app.services.result_normalizer import normalize_binary_result
from app.services.storage_service import ensure_results_dir
from app.tasks.celery_app import celery_app


@celery_app.task(name="process_case_inference")
def process_case_inference(case_id: int) -> None:
    db = SessionLocal()
    try:
        case = db.get(Case, case_id)
        if case is None:
            return

        file_map = _load_required_case_files(case_id, db)
        missing_sequences = [
            sequence.value
            for sequence in SequenceType
            if sequence not in file_map or not Path(file_map[sequence]).exists()
        ]
        if missing_sequences:
            _mark_failed(
                case,
                db,
                f"Missing required sequence files: {', '.join(missing_sequences)}.",
            )
            return

        output_dir = ensure_results_dir(case.id)

        try:
            model_response = call_model_endpoint(
                file_map[SequenceType.T1],
                file_map[SequenceType.T1CE],
                file_map[SequenceType.T2],
                file_map[SequenceType.FLAIR],
                output_dir,
            )
        except ModelClientError as exc:
            _mark_failed(case, db, str(exc))
            return

        if model_response.response_type == "binary" and model_response.file_path:
            normalized = normalize_binary_result(model_response.file_path)
        else:
            _mark_failed(case, db, "Model service returned an unsupported response.")
            return

        _save_case_result(case, normalized, db)
        case.status = CaseStatus.COMPLETED
        case.error_message = None
        db.commit()
    except Exception as exc:
        db.rollback()
        case = db.get(Case, case_id)
        if case is not None:
            _mark_failed(case, db, f"Inference processing failed: {exc}")
    finally:
        db.close()


def _load_required_case_files(case_id: int, db: Session) -> dict[SequenceType, str]:
    files = db.query(CaseFile).filter(CaseFile.case_id == case_id).all()
    return {case_file.sequence_type: case_file.file_path for case_file in files}


def _save_case_result(case: Case, normalized: dict, db: Session) -> None:
    result = case.result
    if result is None:
        result = CaseResult(case_id=case.id)
        db.add(result)

    result.mask_url = normalized["mask_url"]
    result.slices_urls = normalized["slices"]
    result.overlays_urls = normalized["overlays"]
    result.total_tumor_volume = normalized["total_tumor_volume"]
    result.edema_volume = normalized["edema_volume"]
    result.enhancing_volume = normalized["enhancing_volume"]
    result.non_enhancing_volume = normalized["non_enhancing_volume"]


def _mark_failed(case: Case, db: Session, message: str) -> None:
    case.status = CaseStatus.FAILED
    case.error_message = message
    db.commit()
