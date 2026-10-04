# Iris

Four agents (Researcher, Skeptic, Fact-checker, Devil's advocate) check a statement, then a judge writes the answer, confidence and open doubts.

## Open it
Double-click `index.html`. No install, no internet needed for Demo mode.

Modes (top right):
- Demo: saved Einstein run, works offline. Use this for the presentation.
- Live: pick a provider and model for each seat under "Configure models" (click "Load available models" to see what Gemini and Ollama really offer). Ollama needs `OLLAMA_ORIGINS=* ollama serve`; Gemini needs a key from Google AI Studio and internet.

## Optional Python backend
The Python backend is the server-side API version of the same pipeline. It keeps the Gemini key on the server, streams agent events over SSE, and supports Gemini or local Ollama providers.

1. Copy `backend/.env.example` to `backend/.env`.
2. Put your Gemini key in `GEMINI_API_KEY` if using Gemini.
3. Install dependencies: `pip install -r requirements.txt`.
4. Start the API from `iris/backend`: `uvicorn main:app --reload`.
5. Check `/api/health` before testing `POST /api/check`.

For a browser frontend served separately, set `CORS_ORIGINS` in `.env` to the exact frontend origin. Do not commit `.env`; it contains secrets.

The standalone frontend Live mode still supports direct Gemini/Ollama calls for the no-backend workflow. Demo mode remains fully offline.
