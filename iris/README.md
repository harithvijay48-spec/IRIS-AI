# Iris

Four agents (Researcher, Skeptic, Fact-checker, Devil's advocate) check a statement, then a judge writes the answer, confidence and open doubts.

## Open it
Download the repository ZIP, extract it, open the `iris` folder, and double-click **`index.html`**. The page is self-contained, so the polished UI does not depend on a local web server.

Modes:
- Demo: saved Einstein investigation, works offline and needs no API key.
- Live: enter a Gemini API key under "Model routing & API settings", use "Test Gemini connection", then run your own claim. Ollama is supported when it is running locally.

For the simplest jury demo, use **Demo mode** first. Live mode is there for showing the real Gemini-backed pipeline.

## Optional Python backend
The Python backend is the server-side API version of the same pipeline. It keeps the Gemini key on the server, streams agent events over SSE, and supports Gemini or local Ollama providers.

1. Copy `backend/.env.example` to `backend/.env`.
2. Put your Gemini key in `GEMINI_API_KEY` if using Gemini.
3. Install dependencies: `pip install -r requirements.txt`.
4. Start the API from `iris/backend`: `uvicorn main:app --reload`.
5. Check `/api/health` before testing `POST /api/check`.

For a browser frontend served separately, set `CORS_ORIGINS` in `.env` to the exact frontend origin. Do not commit `.env`; it contains secrets.

The standalone frontend Live mode still supports direct Gemini/Ollama calls for the no-backend workflow. Demo mode remains fully offline.
