# AI Model Integration

## Architecture

The backend uses FastAPI, PostgreSQL, Redis, and Celery.

FastAPI accepts and stores the MRI uploads locally under:

```text
storage/cases/{case_id}/input/
```

The Celery worker loads the stored files and calls the external AI model endpoint configured by `MODEL_ENDPOINT_URL`.

## Request To The AI Model

```http
POST /predict/
Content-Type: multipart/form-data
```

Required file fields:

- `t1`
- `t1ce`
- `t2`
- `flair`

All four files are `.nii.gz` MRI volumes.

## Successful AI Response

The AI model must return:

- HTTP `200 OK`
- A binary `.nii.gz` response body
- The 3D segmentation mask only

The response is not JSON. The model does not return PNG slices, overlays, or tumor volume measurements.

## Backend Handling

The backend saves the returned mask as:

```text
storage/cases/{case_id}/results/segmentation_mask.nii.gz
```

FastAPI serves local files through `/storage`, so the frontend mask path is:

```text
/storage/cases/{case_id}/results/segmentation_mask.nii.gz
```

The result record keeps:

- `mask_url`: URL path for the saved segmentation mask
- `slices_urls`: empty array
- `overlays_urls`: empty array
- Volume fields: `null`

After the mask is saved, the case status becomes `COMPLETED`.

## Errors

If the model endpoint fails, times out, or returns an invalid response, Celery marks the case as `FAILED` and stores an error message.

No fake prediction output is created.

## Ngrok

If the AI model is exposed through ngrok, configure its full prediction URL in `.env`:

```text
MODEL_ENDPOINT_URL=https://your-model-domain.ngrok-free.app/predict/
```

An ngrok URL normally changes after ngrok restarts. When the AI model URL changes:

1. Update `MODEL_ENDPOINT_URL` in `.env`.
2. Restart FastAPI.
3. Restart the Celery worker.

FastAPI and Celery must both be restarted so they load the updated environment value.

The backend may also be exposed through ngrok for frontend testing. That backend ngrok URL becomes the frontend `BASE_URL`.
