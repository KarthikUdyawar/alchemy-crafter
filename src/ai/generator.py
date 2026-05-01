"""
Ollama AI integration — prompt, HTTP call, parse, retry.
"""

import re
import time
import httpx

from src.config import config
from src.cache import get_recent_context
from src.logger import get_logger

log = get_logger("ai")

_RESULT_RE = re.compile(r"result:\s*(.+)", re.IGNORECASE)
_MAX_RETRIES = 2
_RETRY_DELAY = 1.0
_VALID_OUTPUT = re.compile(r"^[a-z][a-z ]{0,28}[a-z]$")   # 2–30 chars, lowercase, letters+spaces


def _build_prompt(a: str, b: str, context: list[str]) -> str:
    recent = ", ".join(context) if context else "none"
    return f"""You are an alchemy engine. Output ONE element name. Nothing else.
 
Known elements: {recent}
 
Rules:
- ONE word only (no compound words, no spaces, no hyphens)
- Must be a real, physical substance: mud, steam, lava, ash, glass, ice, sand, smoke
- Historically or scientifically plausible — no fantasy words
- Lowercase only, letters only
- Do NOT combine the input words (mudwater, firewater, earthsteam are INVALID)
- Do NOT repeat either input element
 
Combine: {a} + {b}
result:"""
 
def _parse_response(text: str) -> str | None:
    """Extract and validate element name from Ollama response."""
    # Try "result: <word>" pattern first
    match = re.search(r"result:\s*([a-z]+)", text.lower())
    if match:
        candidate = match.group(1).strip()
        if 2 <= len(candidate) <= 30:
            return candidate
 
    # Fallback: first line that's a single lowercase word
    for line in text.splitlines():
        line = line.strip().lower()
        if re.match(r"^[a-z]{2,30}$", line):
            return line
 
    return None


def generate_recipe(a: str, b: str) -> str | None:
    """
    Call Ollama with retry. Returns lowercased element name or None.
    """
    context = get_recent_context()
    prompt = _build_prompt(a, b, context)
    payload = {
        "model": config.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 20},
    }

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=config.OLLAMA_TIMEOUT) as client:
                resp = client.post(f"{config.OLLAMA_URL}/api/generate", json=payload)
                resp.raise_for_status()
                raw = resp.json().get("response", "")
                result = _parse_response(raw)

                if result:
                    log.info(
                        "AI generated '%s' for %s+%s (attempt %d)",
                        result,
                        a,
                        b,
                        attempt,
                    )
                    return result

                log.warning("AI response unparseable (attempt %d): %r", attempt, raw)

        except httpx.TimeoutException:
            log.warning("Ollama timeout (attempt %d/%d)", attempt, _MAX_RETRIES)
        except httpx.HTTPStatusError as e:
            log.error("Ollama HTTP %s (attempt %d)", e.response.status_code, attempt)
        except Exception as e:
            log.error("Ollama unexpected error (attempt %d): %s", attempt, e)

        if attempt < _MAX_RETRIES:
            time.sleep(_RETRY_DELAY)

    log.error("AI failed after %d attempts for %s+%s", _MAX_RETRIES, a, b)
    return None
