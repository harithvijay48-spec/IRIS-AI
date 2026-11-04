# IRIS — Fact Intelligence

IRIS runs a five-seat verification workflow: Researcher, Skeptic, Fact-checker, Devil's Advocate, and Judge. The browser interface communicates with the FastAPI backend; model credentials stay on the server.

## Requirements

- Python 3.10+
- A Meta Model API key for the default configuration
- Optional: Gemini API key or a local Ollama installation if you want to use those providers as fallbacks or per-seat overrides

## Run IRIS locally

1. Open a terminal in the `iris/backend` folder.
2. Create your local environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

3. Open `backend/.env` and replace `MODEL_API_KEY` with your Meta Model API key. Do not share this key or commit `.env`.
4. Install dependencies:

   ```powershell
   py -m pip install -r requirements.txt
   ```

5. Start the backend:

   ```powershell
   py -m uvicorn main:app --host 127.0.0.1 --port 8000
   ```

6. Open **http://127.0.0.1:8000** in your browser. Use Demo mode for the offline Einstein example or Live mode to run the backend-powered verification pipeline.
7. Check **http://127.0.0.1:8000/api/health** to see which providers are configured.

Do not double-click `index.html` for Live mode. The standalone file can still show the offline demo, but Live mode requires the backend URL above.

## Provider configuration

The default model is `meta:muse-spark-1.3`. The Meta Model API key is read from `MODEL_API_KEY` (or `META_API_KEY`) in the backend environment and sent as a Bearer token by the server. You can change the model or override individual seats with `DEFAULT_MODEL` and `SEAT_*` variables.

Gemini remains available with `GEMINI_API_KEY` and a seat setting such as `SEAT_FACTCHECKER=gemini:gemini-2.5-flash`. Ollama remains available through `OLLAMA_HOST` and a seat setting such as `SEAT_RESEARCHER=ollama:llama3.2`. Set `FALLBACK` to a configured provider spec if you want a fallback, for example `FALLBACK=gemini:gemini-2.5-flash`.

## API

- `GET /api/health` — backend and provider configuration status (never returns API keys).
- `POST /api/check` — accepts `{"question":"..."}` and streams agent events using Server-Sent Events.

## Important provider limitation

The Meta Chat Completions integration currently uses text chat completions. It does not itself provide the Google Search grounding metadata used by the existing Gemini fact-checker path, so Meta-only runs may not return external source links. Evidence retrieval and evidence-aware judging are a later intelligence stage; do not interpret an uncited Meta response as independently verified.

## Security

- Keep `backend/.env` private and out of version control.
- Never paste provider keys into the browser or source files.
- Use a separate API key for this project and rotate it if it is exposed.
