from types import SimpleNamespace

from app.api.routes.results import get_case_results
from app.models.case import CaseStatus
from app.models.case_file import SequenceType


class QueryStub:
    def __init__(self, *, first_result=None, all_results=None):
        self.first_result = first_result
        self.all_results = all_results

    def filter(self, *args):
        return self

    def first(self):
        return self.first_result

    def all(self):
        return self.all_results


class SessionStub:
    def __init__(self, case, case_files):
        self.queries = [
            QueryStub(first_result=case),
            QueryStub(all_results=case_files),
        ]

    def query(self, model):
        return self.queries.pop(0)


def test_get_case_results_includes_modality_urls():
    result = SimpleNamespace(
        total_tumor_volume=None,
        edema_volume=None,
        enhancing_volume=None,
        non_enhancing_volume=None,
        mask_url="/storage/cases/3/results/segmentation_mask.nii.gz",
        slices_urls=["/storage/legacy/slice.png"],
        overlays_urls=["/storage/legacy/overlay.png"],
    )
    case = SimpleNamespace(id=3, status=CaseStatus.COMPLETED, result=result)
    case_files = [
        SimpleNamespace(
            sequence_type=SequenceType.T1,
            file_path="storage/cases/3/input/t1.nii.gz",
        ),
        SimpleNamespace(
            sequence_type=SequenceType.T1CE,
            file_path="storage/cases/3/input/t1ce.nii.gz",
        ),
        SimpleNamespace(
            sequence_type=SequenceType.T2,
            file_path="/storage/cases/3/input/t2.nii.gz",
        ),
    ]

    response = get_case_results(
        case_id=3,
        db=SessionStub(case, case_files),
        current_user=SimpleNamespace(id=10),
    )

    assert response.model_dump(mode="json") == {
        "case_id": 3,
        "status": "COMPLETED",
        "total_tumor_volume": None,
        "edema_volume": None,
        "enhancing_volume": None,
        "non_enhancing_volume": None,
        "mask_url": "/storage/cases/3/results/segmentation_mask.nii.gz",
        "modalities": {
            "t1": "/storage/cases/3/input/t1.nii.gz",
            "t1ce": "/storage/cases/3/input/t1ce.nii.gz",
            "t2": "/storage/cases/3/input/t2.nii.gz",
            "flair": None,
        },
        "slices": [],
        "overlays": [],
    }
