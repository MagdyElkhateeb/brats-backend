# AI Model Integration Contract

This document describes the backend integration contract for the AI model team.

## Current Model Endpoint

```text
https://hamstring-filter-gab.ngrok-free.dev/predict/
```

The backend sends a POST request to the AI model endpoint from the Celery task after the frontend upload has already completed.

## Request From Backend To AI Model

Request type:

```http
POST /predict/
Content-Type: multipart/form-data
```

Required file fields:

- `t1`
- `t1ce`
- `t2`
- `flair`

All files are `.nii.gz` MRI volumes.

## Expected AI Response

Successful response:

- HTTP `200 OK`
- `Content-Type: application/gzip`
- Body: binary `.nii.gz` segmentation mask

The returned `.nii.gz` file contains only the 3D segmentation mask.

The AI endpoint does not return:

- JSON
- slices
- overlays
- tumor volume values

## Backend Handling

The backend saves the returned file as:

```text
storage/cases/{case_id}/results/segmentation_mask.nii.gz
```

After saving the mask, the backend creates or updates the `CaseResult` record with:

- `mask_url` pointing to the saved `.nii.gz` mask
- `slices_urls = []`
- `overlays_urls = []`
- `total_tumor_volume = null`
- `edema_volume = null`
- `enhancing_volume = null`
- `non_enhancing_volume = null`

The backend then marks the case as `COMPLETED`.

## Error Handling

If the AI model endpoint returns an error or is unavailable, the backend marks the case as `FAILED` and stores an `error_message` on the case.

Known error meanings:

- HTTP `422`: one or more required MRI files may be missing.
- HTTP `500`: MRI files may be invalid or dimension-mismatched.
- Timeout or connection failure: the model service is unavailable or timed out.

## Endpoint URL Changes

If the AI model endpoint URL changes:

1. Update `MODEL_ENDPOINT_URL` in `.env`.
2. Restart FastAPI.
3. Restart the Celery worker.

## Future Optional Improvements

- Return JSON from the AI endpoint.
- Include tumor volumes.
- Upload the mask to cloud storage.
- Return a downloadable URL.
- Generate overlays or slices later if needed.
