from app.services.result_normalizer import empty_normalized_result, normalize_binary_result


def test_empty_normalized_result_does_not_fake_outputs():
    assert empty_normalized_result() == {
        "mask_url": None,
        "slices": [],
        "overlays": [],
        "total_tumor_volume": None,
        "edema_volume": None,
        "enhancing_volume": None,
        "non_enhancing_volume": None,
    }


def test_normalize_binary_result_exposes_only_mask_url():
    normalized = normalize_binary_result(
        "storage/cases/1/results/segmentation_mask.nii.gz"
    )

    assert normalized == {
        "mask_url": "/storage/cases/1/results/segmentation_mask.nii.gz",
        "slices": [],
        "overlays": [],
        "total_tumor_volume": None,
        "edema_volume": None,
        "enhancing_volume": None,
        "non_enhancing_volume": None,
    }
