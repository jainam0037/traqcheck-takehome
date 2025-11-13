import json, os, time
from typing import Any, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

_JSON_TIMEOUT_SECS = float(os.getenv("LLM_JSON_TIMEOUT", "12"))

class LLMError(Exception): ...

def _extract_json_block(text: str) -> Optional[Dict[str, Any]]:
    """
    Robust JSON extraction from a text response that *should* be pure JSON.
    Falls back to scanning for the first {...} block if needed.
    """
    try:
        return json.loads(text)
    except Exception:
        pass
    # crude brace matcher
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        blob = text[start:end+1]
        try:
            return json.loads(blob)
        except Exception:
            return None
    return None

@retry(
    reraise=False,
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=0.4, min=0.4, max=2),
    retry=retry_if_exception_type(LLMError),
)

def generate_text(system: str, user: str) -> str | None:
    """
    Basic text generation. Returns None if no provider/key configured or on error.
    """
    prov = (os.getenv("LLM_PROVIDER") or "").lower()
    try:
        if prov == "openai":
            import requests, json
            key = os.getenv("OPENAI_API_KEY")
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            if not key:
                return None
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            data = {"model": model, "messages": [{"role":"system","content":system},{"role":"user","content":user}]}
            r = requests.post(url, headers=headers, data=json.dumps(data), timeout=30)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()

        if prov == "openrouter":
            import requests, json
            key = os.getenv("OPENROUTER_API_KEY")
            model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
            if not key:
                return None
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            data = {"model": model, "messages":[{"role":"system","content":system},{"role":"user","content":user}]}
            r = requests.post(url, headers=headers, data=json.dumps(data), timeout=30)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()

        if prov == "anthropic":
            import requests, json, os
            key = os.getenv("ANTHROPIC_API_KEY")
            model = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
            if not key:
                return None
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            data = {
                "model": model,
                "system": system,
                "max_tokens": 600,
                "messages": [{"role":"user","content":user}],
            }
            r = requests.post(url, headers=headers, data=json.dumps(data), timeout=30)
            r.raise_for_status()
            return "".join(part.get("text","") for part in r.json()["content"]).strip()
    except Exception:
        return None
    return None

def generate_structured(schema: Dict[str, Any], system_prompt: str, user_prompt: str) -> Optional[Dict[str, Any]]:
    """
    Provider-agnostic structured JSON generator.
    Returns dict on success, or None if provider/key is missing or call fails.
    """
    provider = os.getenv("LLM_PROVIDER", "").lower().strip()
    if not provider:
        return None

    try:
        if provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            t0 = time.time()
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
                response_format={"type": "json_object"},  # ask for strict JSON
            )
            if time.time() - t0 > _JSON_TIMEOUT_SECS:
                raise LLMError("timeout")
            content = resp.choices[0].message.content or ""
            return _extract_json_block(content)

        if provider == "openrouter":
            import httpx
            model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
            headers = {
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY','')}",
                "Content-Type": "application/json",
                # Optional; some models require a referer:
                "HTTP-Referer": "https://github.com/jainam0037/traqcheck-takehome",
                "X-Title": "TraqCheck Takehome",
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0,
                "response_format": {"type": "json_object"},
            }
            with httpx.Client(timeout=_JSON_TIMEOUT_SECS) as http:
                r = http.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                r.raise_for_status()
                data = r.json()
            content = data["choices"][0]["message"]["content"]
            return _extract_json_block(content)

        if provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            model = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
            msg = client.messages.create(
                model=model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=0,
            )
            # Concatenate text blocks
            parts = []
            for b in msg.content:
                if getattr(b, "type", None) == "text":
                    parts.append(b.text)
                elif isinstance(b, dict) and b.get("type") == "text":
                    parts.append(b.get("text", ""))
            content = "\n".join(parts)
            return _extract_json_block(content)

        # Unknown provider
        return None

    except Exception as e:
        # Swallow errors for the take-home; caller will fallback
        return None

