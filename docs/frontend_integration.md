# Frontend Integration Contract

This document describes the backend API contract for the mobile/frontend team.

## Base URLs

Local development base URL:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

For a deployed backend, replace the local base URL with the deployed API URL.

## Authentication Flow

1. Register a user.
2. Login with the user's email and password.
3. Store the returned JWT access token.
4. Send the token on all authenticated requests.

### Register

```http
POST /api/auth/register
Content-Type: application/json
```

Example request:

```json
{
  "full_name": "Dr. Example",
  "email": "doctor@example.com",
  "password": "strong-password",
  "role": "doctor"
}
```

### Login

Swagger Authorize and the login endpoint use OAuth2 password form fields:

```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded
```

Fields:

- `username`: user email
- `password`: user password

Example success response:

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

### Authorization Header

Authenticated requests must include:

```http
Authorization: Bearer jwt-token
```

### Current User

```http
GET /api/auth/me
Authorization: Bearer jwt-token
```

## Patient Endpoints

All patient endpoints require authentication.

```http
POST /api/patients
GET /api/patients
GET /api/patients/{patient_id}
PUT /api/patients/{patient_id}
DELETE /api/patients/{patient_id}
```

Users can only access their own patients.

## Case Endpoints

All case endpoints require authentication.

```http
POST /api/cases
GET /api/cases
GET /api/cases/{case_id}
DELETE /api/cases/{case_id}
GET /api/cases/{case_id}/status
GET /api/cases/{case_id}/results
POST /api/cases/{case_id}/upload
```

Users can only access their own cases. A case must belong to one of the authenticated user's patients.

## MRI Upload

```http
POST /api/cases/{case_id}/upload
Authorization: Bearer jwt-token
Content-Type: multipart/form-data
```

Required multipart file fields:

- `t1`
- `t1ce`
- `t2`
- `flair`

Upload rules:

- The request must include exactly these four file fields.
- All uploaded files must end with `.nii.gz`.
- Do not send extra MRI file fields.

Example successful response:

```json
{
  "case_id": 3,
  "status": "PROCESSING",
  "task_id": "celery-task-id",
  "message": "Upload accepted. Inference processing has started."
}
```

The upload endpoint returns HTTP `202 Accepted` after saving the input files and enqueueing the Celery task.

## Status Polling

```http
GET /api/cases/{case_id}/status
Authorization: Bearer jwt-token
```

Possible statuses:

- `CREATED`
- `PROCESSING`
- `COMPLETED`
- `FAILED`

Example processing response:

```json
{
  "case_id": 3,
  "status": "PROCESSING",
  "task_id": "celery-task-id",
  "error_message": null
}
```

Example failed status response:

```json
{
  "case_id": 3,
  "status": "FAILED",
  "task_id": "celery-task-id",
  "error_message": "Model service returned HTTP 500; MRI files may be invalid or dimension-mismatched."
}
```

## Results

```http
GET /api/cases/{case_id}/results
Authorization: Bearer jwt-token
```

Completed result response:

```json
{
  "case_id": 3,
  "status": "COMPLETED",
  "total_tumor_volume": null,
  "edema_volume": null,
  "enhancing_volume": null,
  "non_enhancing_volume": null,
  "mask_url": "/storage/cases/3/results/segmentation_mask.nii.gz",
  "slices": [],
  "overlays": []
}
```

## Important Frontend Notes

- `mask_url` points to a `.nii.gz` 3D segmentation mask file.
- `mask_url` is not a PNG image.
- `slices` and `overlays` are empty arrays for now.
- Tumor volume values are `null` for now.
- The frontend viewer should overlay the mask on `t1ce` or `flair`.
- The frontend should map mask labels to colors.
