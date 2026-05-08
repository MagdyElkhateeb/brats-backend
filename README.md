# BraTS Backend

FastAPI backend for a BraTS brain tumor segmentation mobile app. This service is an integration layer between a React Native frontend and an external AI model endpoint. It stores users, patients, cases, uploaded MRI sequences, task status, and normalized model results.

The backend does not implement the AI model and does not fake predictions. If the model endpoint is unavailable, the inference task marks the case as `FAILED` and stores the error message.

## Stack

- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Celery
- Redis
- Pydantic
- JWT authentication
- Local file storage for development

## Folder Structure

```text
app/
  main.py
  core/
    config.py
    security.py
    dependencies.py
  db/
    session.py
    base.py
  models/
  schemas/
  api/routes/
  services/
  tasks/
alembic/
tests/
docker-compose.yml
requirements.txt
.env.example
```

## Setup

Create a virtual environment, install dependencies, and copy the example environment file:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Start PostgreSQL and Redis:

```bash
docker compose up -d
```

Run database migrations:

```bash
alembic upgrade head
```

Run the FastAPI app:

```bash
uvicorn app.main:app --reload
```

Run the Celery worker in a second terminal:

```bash
celery -A app.tasks.celery_app.celery_app worker --loglevel=info --pool=solo
```

`--pool=solo` is useful on Windows during development. On Linux/macOS, the default Celery pool is usually fine.

## Swagger and Postman Flow

Swagger UI is available at:

```text
http://127.0.0.1:8000/docs
```

Recommended test flow:

1. Register a user with `POST /api/auth/register`.
2. Login with `POST /api/auth/login`.
3. Use the returned bearer token for authenticated requests.
4. Create a patient with `POST /api/patients`.
5. Create a case with `POST /api/cases`.
6. Upload exactly four `.nii.gz` files to `POST /api/cases/{case_id}/upload` using multipart fields `t1`, `t1ce`, `t2`, and `flair`.
7. Poll `GET /api/cases/{case_id}/status`.
8. Fetch `GET /api/cases/{case_id}/results`.

## Frontend Integration Flow

The React Native app should:

1. Authenticate and store the JWT access token.
2. Create or select a patient.
3. Create a case for that patient.
4. Upload all four MRI sequences in one multipart request.
5. Poll case status until it becomes `COMPLETED` or `FAILED`.
6. Display normalized result fields from `/api/cases/{case_id}/results`.

Users can only access their own patients and cases.

## Model Integration Flow

The Celery task `process_case_inference(case_id)`:

1. Loads the case and uploaded `CaseFile` records.
2. Ensures all four sequence files exist.
3. Creates `storage/cases/{case_id}/results/`.
4. Calls the external endpoint from `app/services/model_client.py`.
5. Normalizes the response in `app/services/result_normalizer.py`.
6. Saves `CaseResult` and marks the case `COMPLETED`, or marks it `FAILED` with an error message.

External model endpoint:

```text
POST http://16.171.169.120:8000/predict/
Content-Type: multipart/form-data
Fields: t1, t1ce, t2, flair
```

## Expected Model Responses

JSON response:

```json
{
  "status": "completed",
  "mask_url": "/outputs/case_1/mask.nii.gz",
  "slices": ["/outputs/case_1/slices/slice_001.png"],
  "overlays": ["/outputs/case_1/overlays/overlay_001.png"],
  "volumes": {
    "total_tumor_volume": 12.5,
    "edema_volume": 5.2,
    "enhancing_volume": 3.1,
    "non_enhancing_volume": 4.2,
    "unit": "cm3"
  }
}
```

Binary response:

- The raw file is saved under `storage/cases/{case_id}/results/`.
- `Content-Disposition` filename is used if present.
- Otherwise the backend uses `model_output.nii.gz`, `model_output.zip`, or `model_output.bin`.
- The saved file URL is returned as `mask_url`.
- `slices`, `overlays`, and volume values remain empty or `null`.

Unavailable or error response:

- The case status becomes `FAILED`.
- The error message is stored on the case.
- No fake prediction data is created.

## Tests

```bash
pytest
```
