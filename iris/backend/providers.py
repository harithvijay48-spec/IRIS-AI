import os

import httpx
from dotenv import load_dotenv

load_dotenv()


class ProviderError(Exception):
    """A provider failure that is safe to report to the application user."""


def parse_spec(spec: str):
    provider, _, model = spec.partition(":")
    if provider not in ("gemini", "ollama", "meta") or not model:
        raise ProviderError(
            f"Bad model setting '{spec}'. Use meta:<model>, gemini:<model> or ollama:<model>."
        )
    return provider, model


async def call_meta(model, system, prompt, json_mode=False):
    # Meta Model API uses a Bearer token. Never send this credential to the browser.
    key = os.getenv("MODEL_API_KEY") or os.getenv("META_API_KEY")
    if not key:
        raise ProviderError("MODEL_API_KEY is not set in the backend environment")

    if json_mode:
        system = system + " Return valid JSON only, without Markdown fences or surrounding commentary."

    body = {
        "model": model,
        "messages": [
            {"role": "developer", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
    }
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                "https://api.meta.ai/v1/chat/completions",
                json=body,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
            )
    except httpx.TimeoutException as exc:
        raise ProviderError("Meta Model API timed out") from exc
    except httpx.HTTPError as exc:
        raise ProviderError("Meta Model API is unreachable") from exc

    if response.status_code != 200:
        # Do not echo request headers or credentials into application errors.
        try:
            message = response.json().get("error", {}).get("message", "Request failed")
        except (ValueError, AttributeError):
            message = "Request failed"
        if response.status_code == 401:
            raise ProviderError("Meta Model API rejected the key (HTTP 401). Check MODEL_API_KEY.")
        if response.status_code == 429:
            raise ProviderError("Meta Model API rate limit reached (HTTP 429). Try again shortly.")
        raise ProviderError(f"Meta Model API returned HTTP {response.status_code}: {str(message)[:180]}")

    try:
        payload = response.json()
        text = payload["choices"][0]["message"]["content"].strip()
    except (ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
        raise ProviderError("Meta Model API returned an unexpected response format") from exc
    if not text:
        raise ProviderError("Meta Model API returned an empty response")
    return text, []


async def call_gemini(model, system, prompt, search=False, json_mode=False):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ProviderError("GEMINI_API_KEY is not set")

    generation = {}
    # Gemini 3.x models do not support the legacy temperature sampling parameter.
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
            response = await client.post(
                url, json=body,
                headers={"x-goog-api-key": key, "Content-Type": "application/json"},
            )
    except httpx.TimeoutException as exc:
        raise ProviderError("Gemini timed out") from exc
    except httpx.HTTPError as exc:
        raise ProviderError("Gemini is unreachable") from exc

    if response.status_code != 200:
        try:
            message = response.json().get("error", {}).get("message", "Request failed")
        except (ValueError, AttributeError):
            message = "Request failed"
        raise ProviderError(f"Gemini returned HTTP {response.status_code}: {str(message)[:180]}")

    payload = response.json()
    candidates = payload.get("candidates") or []
    if not candidates:
        raise ProviderError("Gemini returned no candidate")

    candidate = candidates[0]
    text = "".join(part.get("text", "") for part in candidate.get("content", {}).get("parts", [])).strip()
    if not text:
        raise ProviderError("Gemini returned no text")

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
            response = await client.post(
                f"{host}/api/chat", json=body,
                headers={"Content-Type": "application/json"},
            )
    except httpx.TimeoutException as exc:
        raise ProviderError("Ollama timed out") from exc
    except httpx.HTTPError as exc:
        raise ProviderError("Ollama is unreachable") from exc

    if response.status_code != 200:
        try:
            message = response.json().get("error", "Request failed")
        except ValueError:
            message = "Request failed"
        raise ProviderError(f"Ollama returned HTTP {response.status_code}: {str(message)[:180]}")

    text = response.json().get("message", {}).get("content", "").strip()
    if not text:
        raise ProviderError("Ollama returned an empty response")
    return text, []


async def _call(spec, system, prompt, search, json_mode):
    provider, model = parse_spec(spec)
    if provider == "meta":
        return await call_meta(model, system, prompt, json_mode)
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
