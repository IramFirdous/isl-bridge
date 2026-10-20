# ISL Bridge

Partner challenge: **VerbX / IvishAI (PS 3)** — connect a documented set of **Indian Sign Language (ISL)** gestures with text and multilingual speech in both directions.

VerbX is used for **STT, TTS, and translation only**. It does **not** recognize sign gestures. Recognition is **MediaPipe Hands** landmarks plus a **local geometric classifier**. Unknown poses return **`UNRECOGNIZED`**. The camera and microphone stay off until the person on camera **consents**.

## What it demonstrates

| Case | Route |
| --- | --- |
| TC1 | Named ISL catalog of 10 isolated glosses |
| TC2 | Supported sign → English + Hindi speech (approve before TTS) |
| TC3 | Speech → transcript (editable) → matching ISL sign card, or unsupported phrase |
| TC4 | No consent → camera blocked; random motion → `UNRECOGNIZED`, no speech |

Languages in the demo: **English** and **Hindi**. Sign language: **Indian Sign Language (ISL)** — isolated word subset, not full ISL grammar.

## Data origin

Glosses were scoped from documented ISL teaching practice and the INCLUDE lexicon (Sridhar et al., ACM Multimedia 2020, [INCLUDE](https://doi.org/10.1145/3394171.3413528), CC BY-NC-SA 4.0, non-commercial). Live video is only processed after consent. Do not ship INCLUDE videos in a public repo unless the licence allows your use; this app does not bundle dataset videos.

## Run locally

**Backend (keys stay here)**

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Put VERBX_API_KEY in .env — never commit it
python app.py
```

**Frontend**

```powershell
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173

### VerbX

1. Register with your Ziro email at https://one.verbxeco.com  
2. Eligible teams redeem **ZIRO26** once (credits until 31 Oct 2026, 23:59 IST)  
3. Paste the API key into `backend/.env`  
4. If the dashboard shows different REST paths, set `VERBX_API_BASE`, `VERBX_TRANSLATE_PATH`, `VERBX_STT_PATH`, `VERBX_TTS_PATH`, `VERBX_AUTH_MODE`

Without a key, translation uses the catalog bilingual strings and the browser `speechSynthesis` / Speech Recognition APIs. The UI labels those as **fallback**, not as VerbX.

## Guardrails built in

- Sign language is named on every screen: Indian Sign Language (ISL)
- `UNRECOGNIZED` is a first-class state; TTS is disabled
- Consent record in SQLite before camera/mic
- Approve & speak required before translation/TTS
- API key only on the server (`.gitignore` includes `.env`)



## Tests

```powershell
cd backend
python tests\test_recognize.py
```
