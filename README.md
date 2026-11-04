# IRIS --- Fact Intelligence

IRIS is a multi-agent fact-verification prototype. It accepts a question
or claim, runs a team of specialist agents, and streams their progress
and results through a local web interface.

The Stage 1 architecture uses a **FastAPI backend**. Provider
credentials stay in the backend environment and are not placed in
browser code.

## What is included

-   Researcher, Skeptic, Fact-checker, Devil's Advocate, and Judge
    workflow
-   FastAPI backend with a streaming `POST /api/check` endpoint
-   Meta Model API provider configured as the default
-   Existing Gemini and Ollama provider support
-   Offline Demo mode
-   Health endpoint at `/api/health`

> Meta API access is required for the default Live configuration. Gemini
> or Ollama can be configured instead. A successful automated test with
> mocked responses does not prove that a real API key or model account
> is active.

## Requirements

-   Python installed and available from PowerShell as `python`
-   A Meta Model API key for the default configuration
-   Internet access for installing dependencies and calling hosted model
    APIs
-   Optional: a Gemini API key or a local Ollama installation

## Windows setup (PowerShell)

### 1. Extract the project

Extract the downloaded `IRIS-AI-stage1.zip`. The project folder should
contain an `iris` folder with `index.html` and `backend`.

### 2. Open the backend folder

In PowerShell, change directory to the `backend` folder inside the
extracted project. For example, if the project is in Downloads:

``` powershell
cd "$HOME\Downloads\IRIS-AI-stage1\IRIS-AI-main\iris\backend"
```

If your extracted folder has a different name or location, adjust the
path. You can also open the `backend` folder in File Explorer, click the
address bar, type `powershell`, and press Enter.

### 3. Create your private environment file

``` powershell
Copy-Item .env.example .env
notepad .env
```

In Notepad, replace the placeholder value with your own Meta Model API
key:

``` dotenv
MODEL_API_KEY=your_actual_meta_api_key
```

Save the file and close Notepad.

**Never share your API key in chat, screenshots, source code, or a
public repository.** Keep the real key in `backend/.env`. The `.env`
file should remain private and should not be committed.

### 4. Install Python dependencies

Use `python`, not `py`, if the Python launcher command is unavailable:

``` powershell
python -m pip install -r requirements.txt
```

If pip needs an update, you can run:

``` powershell
python -m pip install --upgrade pip
```

### 5. Start the backend

``` powershell
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Keep this PowerShell window open while using IRIS. The backend is
running while the server process remains active.

### 6. Open IRIS

Open this address in your browser:

<http://127.0.0.1:8000>

Use **Live** mode to send a question to the backend. Use **Demo** mode
for the offline demonstration.

Do not double-click `index.html` when testing Live mode. Live mode
expects the backend to be running at the address above.

### 7. Check backend status

Open:

<http://127.0.0.1:8000/api/health>

The health response reports whether provider keys are configured. It
does not reveal the keys themselves. A configured key does not guarantee
that the provider will accept it; make a real Live request to verify API
access.

## Provider configuration

The backend reads configuration from `backend/.env`.

### Meta Model API (default)

``` dotenv
MODEL_API_KEY=your_actual_meta_api_key
DEFAULT_MODEL=meta:muse-spark-1.3
```

The implementation also checks `META_API_KEY` if `MODEL_API_KEY` is not
set. Keep credentials on the backend only.

### Gemini (optional)

``` dotenv
GEMINI_API_KEY=your_gemini_api_key
```

To use Gemini for a particular agent, set its seat variable. For
example:

``` dotenv
SEAT_FACTCHECKER=gemini:gemini-2.5-flash
```

### Ollama (optional)

Make sure Ollama is installed and running locally, then configure:

``` dotenv
OLLAMA_HOST=http://localhost:11434
SEAT_RESEARCHER=ollama:llama3.2
```

The Ollama model named in the configuration must already be available
locally.

### Per-agent model selection

The following variables can override the default model for individual
agents:

``` dotenv
SEAT_RESEARCHER=
SEAT_SKEPTIC=
SEAT_FACTCHECKER=
SEAT_ADVOCATE=
SEAT_JUDGE=
SEAT_BASELINE=
```

Use a provider/model specification such as `meta:muse-spark-1.3`,
`gemini:gemini-2.5-flash`, or `ollama:llama3.2`.

An optional fallback can be configured with:

``` dotenv
FALLBACK=
```

For example, `FALLBACK=gemini:gemini-2.5-flash` uses Gemini if the
selected provider fails, provided the Gemini key is configured.

Restart the backend after changing `.env`.

## API endpoints

  -----------------------------------------------------------------------
  Method                  Endpoint                Purpose
  ----------------------- ----------------------- -----------------------
  `GET`                   `/`                     Serves the IRIS web
                                                  interface

  `GET`                   `/api/health`           Reports backend and
                                                  provider configuration
                                                  status

  `POST`                  `/api/check`            Accepts a question and
                                                  streams agent events
                                                  using Server-Sent
                                                  Events
  -----------------------------------------------------------------------

Example request body:

``` json
{
  "question": "Is this claim accurate?"
}
```

The question must contain at least 3 non-whitespace characters and be no
longer than 1,000 characters.

## Troubleshooting

### `python` is not recognized

Python may not be installed or may not be on PATH. Install Python and
enable the option to add it to PATH, then reopen PowerShell. If
`python --version` works, use `python -m ...` commands as shown above.

### `No module named pip`

Try:

``` powershell
python -m ensurepip --upgrade
python -m pip install -r requirements.txt
```

### `No module named uvicorn` or another dependency

Make sure PowerShell is in the `backend` directory, then run:

``` powershell
python -m pip install -r requirements.txt
```

### Meta API returns HTTP 401

Check that the key is valid for the Meta Model API, that it was copied
without extra spaces, and that it is in `backend/.env` under
`MODEL_API_KEY`. Muse Code login credentials and Meta Model API
credentials are not interchangeable.

Do not paste the key into an error report. Share only the error message
with secrets removed.

### Meta API returns HTTP 429

The API may have reached a rate or usage limit. Check the account's API
access and usage limits, then retry later.

### The browser cannot connect to IRIS

Confirm that the Uvicorn server is still running in PowerShell and that
the browser is using:

<http://127.0.0.1:8000>

### Live mode fails but Demo mode works

Demo mode runs locally without a live provider request. Live mode
requires the backend to be running and at least one configured provider
to be accessible.

## Current limitations

-   The Meta Chat Completions integration currently returns text
    completions; it does not provide the same Google Search grounding
    metadata available through the Gemini fact-checker path.
-   A provider response is not automatically proof that a claim is true.
    Source retrieval, structured evidence exchange, and evidence-aware
    judging are planned for subsequent development stages.
-   The displayed confidence is an AI assessment, not a calibrated
    statistical probability.
-   The Stage 1 automated tests use mocked provider responses. Test with
    your own API credentials to verify real provider access.

## Security notes

-   Never put API keys in `index.html`, `app.js`, `style.css`, or any
    other browser-delivered file.
-   Keep `backend/.env` private.
-   Do not commit `.env` or share it in ZIP files.
-   If a key is accidentally exposed, revoke or rotate it in the
    provider dashboard.
-   The local server is bound to `127.0.0.1`, so it is intended for use
    on your own computer.

## Development status

This README describes the Stage 1 backend-connected project. Later work
on agent intelligence, evidence-backed verdicts, the redesigned
interface, and further provider integrations should be treated as
separate stages and reviewed before implementation.
