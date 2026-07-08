# EthioGig Surveillance System — Developer Reference

Face-based **test proctoring** microservice. Stores a reference photo per candidate/freelancer and verifies periodic webcam snapshots during tests.

**Path:** `c:\toptal\Surveillance System\`  
**Port:** `8003`  
**Frontend env:** `REACT_APP_SURVEILLANCE_URL`  
**API prefix:** `/api/`

---

## Running

```bash
cd "c:\toptal\Surveillance System"
docker compose up -d    # runs migrate on startup
```

Postgres for `Profile` records + media storage. Uses `face_recognition` + OpenCV (CPU-heavy).

Swagger: `http://127.0.0.1:8003/api/docs/`

---

## Authentication

`core.authentication.CustomJWTAuthentication` — Bearer JWT decoded with **`SECRET_KEY`** (same as main backend).

**Identity:** `freelancer_id` is extracted from the verified JWT payload (`request.auth['user_id']`). Do **not** pass it in the request body — the backend ignores it and reads from the token.

---

## Endpoints (`core/urls.py`)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/fetch-and-store-profile-picture/` | Upload/create reference face image |
| POST | `/api/verify-snapshot/` | Compare live screenshot to reference |
| PATCH | `/api/update-test-profile-picture/` | Update reference (profile change) |

### `verify-snapshot` request

```
multipart/form-data:
  screenshot: image/jpeg
Authorization: Bearer <candidate_token>
```

### Response actions

| `action` | Meaning |
|---|---|
| `continue` | Face matched — test proceeds |
| `pause` | No face / mismatch / bad reference — user should reposition |
| `terminate` | Multiple faces — serious violation |

HTTP 404 with `{ "error": "Freelancer profile not found." }` when no reference exists — frontend pre-test check uploads reference first.

---

## Data Model

**`Profile`** (`core/models.py`)

- `user_id` — UUID string (candidate resume id or freelancer id)
- `profile_picture` — reference image file

Face encodings cached in Django cache (`profile_face_encodings_{user_id}`).

---

## Frontend Integration

### Reference upload

1. **KYC liveness** — `LivelinessTest.js` uploads stage-1 frontal snapshot after face match.
2. **Pre-test check** — `CandidateCameraCheckPage` calls `uploadReferencePhoto()` before verify loop.
3. **Logged-in freelancers** — `CameraCheckPage` uploads profile picture from main API.

### During test

`CameraContext.js`:

- `startCamera()` → preview + 10s interval → POST `verify-snapshot`
- Waits for `<video>` ready before polling
- Pre-test: 3× `continue` required before **Start Test** button

---

## Project Layout

```
app/
├── surveillance/      # settings, urls
└── core/
    ├── views.py       # FetchAndStoreProfilePictureView, VerifySnapshotView
    ├── models.py      # Profile
    ├── authentication.py
    └── tests/         # test_snapshot_match.py, etc.
```

---

## Common Gotchas

- **404 on verify** usually means missing `Profile` — not a missing URL route.
- **Tolerance 0.5** in `compare_faces` — stricter matching; poor lighting causes `pause`.
- **Container must be running** during tests — otherwise frontend skips/retries or pauses.
- **CORS** — `localhost:3000` only in dev settings.

---

## Release readiness

- [x] Reference photo + verify snapshot APIs used by vetting
- [x] Frontend reports holds to main backend (`proctoring-violation`); camera errors ≠ hold UI copy
- [x] Pre-test: inline snapshot warnings; hold enforced on status/hub before camera check
- [ ] Tune face match tolerance if false pauses are common

**No service changes in 2026-06-02 vetting batch** — integration updates live in main backend + React `CameraContext.js`.

**Checklist:** `c:\toptal\Django Project\RELEASE_READINESS.md`

---

## Related

| Component | File |
|---|---|
| Camera state | `React App/.../CameraContext.js` |
| Pre-test gate | `CandidateCameraCheckPage.js` |
| KYC reference | `LivelinessTest.js` |
