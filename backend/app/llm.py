"""Thin async client for a local Ollama server.

Exposes two helpers:
  - generate(): free-form completion
  - generate_json(): completion constrained to a JSON object, with a
    forgiving parser + one repair retry, because local 7B models occasionally
    wrap JSON in prose or code fences.
"""
import json
import re
import httpx

from . import config


class LLMError(RuntimeError):
    pass


async def generate(prompt: str, *, system: str | None = None, model: str | None = None,
                   temperature: float = 0.2, fmt_json: bool = False) -> str:
    payload = {
        "model": model or config.LLM_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }
    if system:
        payload["system"] = system
    if fmt_json:
        payload["format"] = "json"   # Ollama-native JSON grammar constraint
    async with httpx.AsyncClient(timeout=config.LLM_TIMEOUT) as client:
        try:
            r = await client.post(f"{config.OLLAMA_HOST}/api/generate", json=payload)
            r.raise_for_status()
        except httpx.HTTPError as e:
            raise LLMError(f"Ollama request failed: {e}") from e
        return r.json().get("response", "")


def _extract_json(text: str):
    """Best-effort pull of the first JSON object/array from a model reply."""
    text = text.strip()
    # strip ```json ... ``` fences
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # fall back to the outermost {...} or [...]
    for open_c, close_c in (("{", "}"), ("[", "]")):
        start, end = text.find(open_c), text.rfind(close_c)
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                continue
    return None


async def generate_json(prompt: str, *, system: str | None = None,
                        model: str | None = None, temperature: float = 0.1):
    """Return parsed JSON. Retries once with a stricter nudge on failure."""
    raw = await generate(prompt, system=system, model=model,
                         temperature=temperature, fmt_json=True)
    parsed = _extract_json(raw)
    if parsed is not None:
        return parsed
    repair = (
        "Your previous reply was not valid JSON. Reply with ONLY a single valid "
        "JSON value and nothing else.\n\n" + prompt
    )
    raw = await generate(repair, system=system, model=model,
                        temperature=0.0, fmt_json=True)
    parsed = _extract_json(raw)
    if parsed is None:
        raise LLMError("Model did not return parseable JSON.")
    return parsed


async def health() -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{config.OLLAMA_HOST}/api/tags")
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        return {"ok": True, "models": models}
