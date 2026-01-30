# API Reference

The Platform API is RESTful. Base URL: `https://api.company.com/v1`. All requests require an `Authorization: Bearer <token>` header. Tokens are obtained via the login flow or `platform auth token`.

## Endpoints

### Projects

- `GET /projects` — List projects for the current user.
- `POST /projects` — Create a project. Body: `{ "name": "string" }`.
- `GET /projects/{id}` — Get project by ID.
- `DELETE /projects/{id}` — Delete project (must be empty).

### Datasets

- `GET /projects/{projectId}/datasets` — List datasets in a project.
- `POST /projects/{projectId}/datasets` — Create dataset. Body: `{ "name": "string", "schema": {...} }`.
- `GET /datasets/{id}` — Get dataset metadata.
- `POST /datasets/{id}/upload` — Upload file (multipart). Max size 500 MB.

### Pipelines

- `GET /projects/{projectId}/pipelines` — List pipelines.
- `POST /projects/{projectId}/pipelines` — Create pipeline. Body: `{ "name": "string", "steps": [...] }`.
- `POST /pipelines/{id}/run` — Trigger a run. Returns `runId`. Poll `GET /runs/{runId}` for status.

## Rate Limits

- 100 requests per minute per token. Response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`.

## Errors

- `400` — Bad request (invalid body or params).
- `401` — Unauthorized (missing or invalid token).
- `404` — Resource not found.
- `429` — Rate limit exceeded. Retry after `Retry-After` seconds.
