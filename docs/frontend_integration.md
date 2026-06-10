# Frontend Integration

## Base URL

Local development:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

When using ngrok, set the frontend `BASE_URL` to the backend ngrok URL. If ngrok restarts, the URL normally changes and the frontend configuration must be updated.

CORS is enabled for development.

## Authentication

The backend uses JWT bearer authentication.

1. Register with `POST /api/auth/register`.
2. Log in with `POST /api/auth/login`.
3. Store the returned `access_token`.
4. Send it on authenticated requests:

```http
Authorization: Bearer <access_token>
```

The login endpoint uses form fields:

- `username`: user email
- `password`: user password

Users can only access their own patients and cases.

## Patient And Case Metadata

Patient Name and Scan Date do not belong in the upload request.

Send Patient Name as `patient_code`:

```http
POST /api/patients
Content-Type: application/json
```

```json
{
  "patient_code": "Patient 001"
}
```

Send Scan Date as `scan_date` when creating the case:

```http
POST /api/cases
Content-Type: application/json
```

```json
{
  "patient_id": 1,
  "title": "Brain MRI",
  "scan_date": "2026-06-10"
}
```

## MRI Upload

```http
POST /api/cases/{case_id}/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

The upload endpoint receives exactly these file fields:

- `t1`
- `t1ce`
- `t2`
- `flair`

All four files must end with `.nii.gz`.

Example response:

```json
{
  "case_id": 3,
  "status": "PROCESSING",
  "task_id": "celery-task-id",
  "message": "Upload accepted. Inference processing has started."
}
```

## Status Polling

```http
GET /api/cases/{case_id}/status
Authorization: Bearer <access_token>
```

Possible statuses:

- `CREATED`
- `PROCESSING`
- `COMPLETED`
- `FAILED`

Poll until the case is `COMPLETED` or `FAILED`.

## Results And NiiVue

```http
GET /api/cases/{case_id}/results
Authorization: Bearer <access_token>
```

Expected completed response:

```json
{
  "case_id": 3,
  "status": "COMPLETED",
  "total_tumor_volume": null,
  "edema_volume": null,
  "enhancing_volume": null,
  "non_enhancing_volume": null,
  "mask_url": "/storage/cases/3/results/segmentation_mask.nii.gz",
  "modalities": {
    "t1": "/storage/cases/3/input/t1.nii.gz",
    "t1ce": "/storage/cases/3/input/t1ce.nii.gz",
    "t2": "/storage/cases/3/input/t2.nii.gz",
    "flair": "/storage/cases/3/input/flair.nii.gz"
  },
  "slices": [],
  "overlays": []
}
```

NiiVue should load:

- `BASE_URL + mask_url`
- `BASE_URL + modalities.t1`
- `BASE_URL + modalities.t1ce`
- `BASE_URL + modalities.t2`
- `BASE_URL + modalities.flair`

These paths point directly to `.nii.gz` files served by FastAPI through `/storage`.

Practical notes:

- A modality value can be `null` if its file record is missing.
- `mask_url` is a 3D segmentation mask, not a PNG.
- `slices` and `overlays` remain empty arrays for compatibility.
- Volume fields are currently `null`.
- Check for `null` before adding a file to NiiVue.

## Recommended Frontend Flow

1. Authenticate and store the JWT.
2. Create or select a patient.
3. Create a case with its `scan_date`.
4. Upload the four MRI files.
5. Poll the case status.
6. Fetch the results.
7. Load the modality and mask URLs in NiiVue.
