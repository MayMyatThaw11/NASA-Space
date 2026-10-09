# FloodLens API
PowerShell: cd backend; py -m venv .venv; .\\.venv\\Scripts\\Activate.ps1; py -m pip install -r requirements.txt; Copy-Item .env.example .env; uvicorn main:app --reload --port 8000
POST /api/explanation accepts structured analysis results only. POST /api/tts returns audio/wav only when credentials and a working model request are available. Audio is cached by language, text, model, and voice under backend/audio-cache/.

GET /api/local-updates?region=Tanintharyi reads backend/local_updates.json. The feed is intentionally empty until verified reports are added. Each incident must include the fields documented in that JSON file; coordinates must remain null unless the location is verified. The frontend displays township-level and neighborhood-specific reports separately and never treats an empty feed as evidence of no danger.

GET /api/year-data?year=2024&region=Rakhine reads backend/year_data.json. Only source-backed year windows belong in this file. Years without loaded source-backed observations return `available: false` and the frontend shows Analysis pending.
