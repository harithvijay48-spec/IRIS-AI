import os

import httpx
from dotenv import load_dotenv

load_dotenv()


class ProviderError(Exception):
    pass


def parse_spec(spec: str):
    provider, _, model = spec.partition(":")
    if provider not in ("gemini", "ollama") or not model:
        raise ProviderError(f"Bad model setting '{spec}'. Use gemini:<model> or ollama:<model>'.")
    return provider, model


async def call_gemini(model, system, prompt, search=False, json_mode=False):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ProviderError("GEMINI_API_KEY is not set")

    generation = {}
    # Gemini 3.8 Flash does not support the legacy temperature sampling parameter.
    if not model.startswith("gemini-3."):
        generation["temperature"] = 0.3
    if model.startswith("gemini-3."):
        generation["thinkingConfig"] = {"thinkingLevel": os.getenv("GEMINI_THINKING_LEVEL", "low")}
    if json_mode:
        generation["responseMimeType"] = "application/json"

    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": generation,
    }
    if search:
        body["tools"] = [{"google_search": {}}]

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            r = await client.post(url, json=body, headers={"x-goog-api-key": key, "Content-Type": "application/json"})
    except httpx.TimeoutException as e:
        raise ProviderError(f"Gemini timed out ({e.__class__.__name__})")
    except httpx.HTTPError as e:
        raise ProviderError(f"Gemini unreachable ({e.__class__.__name__})")

    if r.status_code != 200:
        try:
            err = r.json().get("error", {}).get("message", r.text[:240])
        except ValueError:
            err = r.text[:240]
        raise ProviderError(f"Gemini {r.status_code}: {err}")

    payload = r.json()
    candidates = payload.get("candidates") or []
    if not candidates:
        raise ProviderError(f"Gemini returned no candidate: {payload.get('promptFeedback', {})}")

    candidate = candidates[0]
    text = "".join(p.get("text", "") for p in candidate.get("content", {}).get("parts", [])).strip()
    if not text:
        raise ProviderError(f"Gemini returned no text (reason: {candidate.get('finishReason', 'unknown')})")

    sources = []
    for chunk in candidate.get("groundingMetadata", {}).get("groundingChunks", []):
        web = chunk.get("web")
        if web:
            sources.append({"title": web.get("title", ""), "url": web.get("uri", "")})
    return text, sources


async def call_ollama(model, system, prompt, json_mode=False):
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    body = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "options": {"temperature": 0.3},
    }
    if json_mode:
        body["format"] = "json"

    try:
        async with httpx.AsyncClient(timeout=180) as client:
            r = await client.post(f"{host}/api/chat", json=body, headers={"Content-Type": "application/json"})
    except httpx.TimeoutException as e:
        raise ProviderError(f"Ollama timed out ({e.__class__.__name__})")
    except httpx.HTTPError as e:
        raise ProviderError(f"Ollama unreachable ({e.__class__.__name__})")

    if r.status_code != 200:
        try:
            err = r.json().get("error", r.text[:240])
        except ValueError:
            err = r.text[:240]
        raise ProviderError(f"Ollama {r.status_code}: {err}")

    payload = r.json()
    text = payload.get("message", {}).get("content", "").strip()
    if not text:
        raise ProviderError("Ollama returned an empty response")
    return text, []


async def _call(spec, system, prompt, search, json_mode):
    provider, model = parse_spec(spec)
    if provider == "gemini":
        return await call_gemini(model, system, prompt, search, json_mode)
    return await call_ollama(model, system, prompt, json_mode)


async def ask(spec, fallback, system, prompt, search=False, json_mode=False):
    try:
        text, sources = await _call(spec, system, prompt, search, json_mode)
        return text, sources, spec
    except ProviderError as first_error:
        if not fallback or fallback == spec:
            raise
        try:
            text, sources = await _call(fallback, system, prompt, search, json_mode)
            return text, sources, fallback
        except ProviderError as fallback_error:
            raise ProviderError(f"{first_error}; fallback failed: {fallback_error}") from fallback_error
