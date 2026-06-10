# BraTS Backend

FastAPI integration backend for a BraTS MRI segmentation frontend and an external AI model service.

## Stack

- FastAPI
- PostgreSQL with SQLAlchemy and Alembic
- Redis and Celery
- JWT bearer authentication
- Local file storage under `storage/`

The backend serves stored files through `/storage`. For example:

```text
storage/cases/3/input/t1.nii.gz
```

is available at:

```text
/storage/cases/3/input/t1.nii.gz
```

CORS is enabled for development frontend access.

## Integration Documentation

- [Frontend integration](docs/frontend_integration.md)
- [AI model integration](docs/ai_model_integration.md)

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
docker compose up -d
alembic upgrade head
```

Run FastAPI:

```bash
uvicorn app.main:app --reload
```

Run Celery in another terminal:

```bash
celery -A app.tasks.celery_app.celery_app worker --loglevel=info --pool=solo
```

`--pool=solo` is useful for Windows development.

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## Application Flow

1. Register and log in to receive a JWT.
2. Create a patient with `POST /api/patients`.
3. Create a case with `POST /api/cases`.
4. Upload four `.nii.gz` MRI files with `POST /api/cases/{case_id}/upload`.
5. Celery sends the files to the external AI model endpoint.
6. The AI endpoint returns a binary `.nii.gz` segmentation mask.
7. The backend stores the mask under `storage/` and exposes it through `/storage`.
8. Poll case status and fetch `GET /api/cases/{case_id}/results`.

Users can only access their own patients and cases.

## Upload Contract

```http
POST /api/cases/{case_id}/upload
Content-Type: multipart/form-data
Authorization: Bearer <jwt>
```

Required file fields:

- `t1`
- `t1ce`
- `t2`
- `flair`

All files must end with `.nii.gz`. The upload endpoint receives files only.

If the frontend collects Patient Name and Scan Date:

- Send Patient Name as `patient_code` to `POST /api/patients`.
- Send Scan Date as `scan_date` to `POST /api/cases`.

## Results Contract

```http
GET /api/cases/{case_id}/results
Authorization: Bearer <jwt>
```

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

The frontend uses NiiVue to load the original MRI volumes and segmentation mask directly. Build each file URL with `BASE_URL + path`.

## AI Model Contract

Celery calls the endpoint configured by `MODEL_ENDPOINT_URL` using multipart fields `t1`, `t1ce`, `t2`, and `flair`.

The successful model response is binary `.nii.gz` data containing only the segmentation mask. It is not JSON and does not include slices, overlays, or volume measurements.

## Ngrok

For frontend testing, expose FastAPI with ngrok and use the backend ngrok URL as the frontend `BASE_URL`. The URL changes when ngrok restarts unless a reserved domain is configured.

If the AI model ngrok URL changes:

1. Update `MODEL_ENDPOINT_URL` in `.env`.
2. Restart FastAPI.
3. Restart the Celery worker.

## Tests

```bash
pytest
```
