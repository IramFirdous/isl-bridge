"""Server-side VerbX STT / TTS / translation client.

API keys never leave this process. Exact dashboard paths differ by account,
so base URL and paths are environment-configurable.

If the live API is missing or returns an error and VERBX_ALLOW_FALLBACK=1,
a clearly labelled local fallback is used so the demo routes still run.
Fallback is never described as VerbX sign recognition — VerbX does not do that.
"""

from __future__ import annotations

import base64
import os
from typing import Any

import httpx

from catalog import load_catalog, signs_by_id

TIMEOUT = 45.0


def configured() -> bool:
    return bool(os.getenv("VERBX_API_KEY", "").strip())


def allow_fallback() -> bool:
    return os.getenv("VERBX_ALLOW_FALLBACK", "1").strip() not in {"0", "false", "False"}


def _headers() -> dict[str, str]:
    key = os.getenv("VERBX_API_KEY", "").strip()
    mode = os.getenv("VERBX_AUTH_MODE", "Bearer").strip()
    if mode.lower() in {"x-api-key", "x_api_key"}:
        return {"X-Api-Key": key, "Accept": "application/json"}
    return {"Authorization": f"Bearer {key}", "Accept": "application/json"}


def _url(path_env: str, default_path: str) -> str:
    base = os.getenv("VERBX_API_BASE", "https://api.verbxeco.com").rstrip("/")
    path = os.getenv(path_env, default_path)
    if not path.startswith("/"):
        path = "/" + path
    return base + path


def _extract_text(payload: Any) -> str | None:
    if payload is None:
        return None
    if isinstance(payload, str):
        return payload
    if not isinstance(payload, dict):
        return None
    for key in ("text", "translation", "translated_text", "output", "result"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
        if isinstance(value, dict):
            nested = _extract_text(value)
            if nested:
                return nested
    data = payload.get("data")
    if data is not None:
        return _extract_text(data)
    return None


async def translate(text: str, source: str, target: str) -> dict:
    if configured():
        url = _url("VERBX_TRANSLATE_PATH", "/v1/translate")
        body = {"text": text, "source": source, "target": target, "from": source, "to": target}
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.post(url, json=body, headers=_headers())
            if response.status_code < 300:
                translated = _extract_text(response.json()) or response.text
                return {
                    "ok": True,
                    "provider": "verbx",
                    "source": source,
                    "target": target,
                    "input": text,
                    "text": translated,
                    "status": response.status_code,
                }
            err = response.text[:400]
            if not allow_fallback():
                return {"ok": False, "provider": "verbx", "error": err, "status": response.status_code}
        except Exception as exc:
            if not allow_fallback():
                return {"ok": False, "provider": "verbx", "error": str(exc)}

    fallback = _glossary_translate(text, target)
    return {
        "ok": True,
        "provider": "local_glossary_fallback",
        "source": source,
        "target": target,
        "input": text,
        "text": fallback,
        "note": "VerbX call skipped or failed. Catalog bilingual strings used. Not presented as live VerbX output.",
    }


async def tts(text: str, language: str) -> dict:
    if configured():
        url = _url("VERBX_TTS_PATH", "/v1/tts")
        body = {"text": text, "language": language, "lang": language, "voice": language}
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.post(url, json=body, headers=_headers())
            if response.status_code < 300:
                ctype = response.headers.get("content-type", "")
                if "audio" in ctype or "octet-stream" in ctype:
                    audio_b64 = base64.b64encode(response.content).decode("ascii")
                    return {
                        "ok": True,
                        "provider": "verbx",
                        "language": language,
                        "text": text,
                        "audio_base64": audio_b64,
                        "mime": ctype.split(";")[0] or "audio/mpeg",
                    }
                try:
                    data = response.json()
                except Exception:
                    data = {}
                audio_b64 = data.get("audio_base64") or data.get("audio") or data.get("data")
                audio_url = data.get("url") or data.get("audio_url")
                if isinstance(audio_b64, str) and audio_b64.startswith("http"):
                    audio_url = audio_b64
                    audio_b64 = None
                return {
                    "ok": True,
                    "provider": "verbx",
                    "language": language,
                    "text": text,
                    "audio_base64": audio_b64,
                    "audio_url": audio_url,
                    "mime": data.get("mime", "audio/mpeg"),
                }
            if not allow_fallback():
                return {"ok": False, "provider": "verbx", "error": response.text[:400], "status": response.status_code}
        except Exception as exc:
            if not allow_fallback():
                return {"ok": False, "provider": "verbx", "error": str(exc)}

    return {
        "ok": True,
        "provider": "browser_tts_fallback",
        "language": language,
        "text": text,
        "audio_base64": None,
        "note": "No VerbX audio returned. Client may use speechSynthesis, labelled as fallback.",
    }


async def stt(audio: bytes, filename: str, content_type: str, language: str | None) -> dict:
    if configured():
        url = _url("VERBX_STT_PATH", "/v1/stt")
        headers = _headers()
        files = {"file": (filename or "speech.webm", audio, content_type or "application/octet-stream")}
        data = {}
        if language:
            data["language"] = language
            data["lang"] = language
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.post(url, headers=headers, files=files, data=data)
            if response.status_code < 300:
                try:
                    payload = response.json()
                except Exception:
                    payload = {"text": response.text}
                text = _extract_text(payload) or ""
                return {
                    "ok": True,
                    "provider": "verbx",
                    "text": text,
                    "language": language,
                    "raw_keys": list(payload.keys()) if isinstance(payload, dict) else [],
                }
            # Some accounts expect JSON + base64 instead of multipart
            b64 = base64.b64encode(audio).decode("ascii")
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.post(
                    url,
                    headers={**headers, "Content-Type": "application/json"},
                    json={"audio_base64": b64, "filename": filename, "language": language, "mime": content_type},
                )
            if response.status_code < 300:
                payload = response.json()
                return {
                    "ok": True,
                    "provider": "verbx",
                    "text": _extract_text(payload) or "",
                    "language": language,
                }
            if not allow_fallback():
                return {"ok": False, "provider": "verbx", "error": response.text[:400], "status": response.status_code}
        except Exception as exc:
            if not allow_fallback():
                return {"ok": False, "provider": "verbx", "error": str(exc)}

    return {
        "ok": False,
        "provider": "none",
        "text": "",
        "error": "VerbX STT unavailable. Use in-browser speech recognition fallback on the client.",
        "fallback": "browser_stt",
    }


def _glossary_translate(text: str, target: str) -> str:
    catalog = load_catalog()
    by_id = signs_by_id(catalog)
    lowered = text.strip().lower()
    for sign in by_id.values():
        blob = {sign["en"].lower(), sign["hi"].lower(), sign["gloss"].lower(), sign["id"].lower().replace("_", " ")}
        blob.update(a.lower() for a in sign.get("aliases", []))
        if lowered in blob or sign["en"].lower() == lowered or sign["hi"] == text.strip():
            return sign["hi"] if target.startswith("hi") else sign["en"]
    # tiny demo glossary beyond exact glosses
    table = {
        ("hello", "hi"): "नमस्ते",
        ("thank you", "hi"): "धन्यवाद",
        ("yes", "hi"): "हाँ",
        ("no", "hi"): "नहीं",
        ("please", "hi"): "कृपया",
        ("help", "hi"): "मदद",
        ("water", "hi"): "पानी",
        ("name", "hi"): "नाम",
        ("good", "hi"): "अच्छा",
        ("stop", "hi"): "रुकिए",
        ("नमस्ते", "en"): "Hello",
        ("धन्यवाद", "en"): "Thank you",
        ("हाँ", "en"): "Yes",
        ("नहीं", "en"): "No",
        ("कृपया", "en"): "Please",
        ("मदद", "en"): "Help",
        ("पानी", "en"): "Water",
        ("नाम", "en"): "Name",
        ("अच्छा", "en"): "Good",
        ("रुकिए", "en"): "Stop",
    }
    return table.get((lowered, target[:2]), table.get((text.strip(), target[:2]), text))
