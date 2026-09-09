"""AI providers. The platform runs fully without one (NullProvider); OpenAI is an optional adapter.

Safety class YELLOW: outputs are drafts or candidate detections for a human to review, never sacred text.
Text prompts carry only structured facts (names, counts, surah names, ayah numbers) — never Quran text — and the
system prompt forbids quoting or generating verses. Speech transcripts are compared against the verified text
and are never displayed as Quran. See docs/design/07-religious-ai-safety.md.
"""
from __future__ import annotations

import json
import secrets
import urllib.error
import urllib.request

from django.conf import settings


class AiUnavailable(Exception):
    """No provider configured, or the provider failed. Callers turn this into HTTP 503."""


class AiProvider:
    name = "null"
    model = ""
    asr_model = ""

    def complete(self, system: str, user: str, *, max_tokens: int = 400, temperature: float = 0.4) -> str:
        raise AiUnavailable("no AI provider configured")

    def transcribe(self, audio: bytes, filename: str, mime: str, *, language: str = "ar", prompt: str = "") -> str:
        raise AiUnavailable("no speech provider configured")


class NullProvider(AiProvider):
    """Default: the feature is present but inert. Endpoints answer 503 ai_unavailable."""


def _multipart(fields: dict[str, str], file_field: str, filename: str, mime: str, data: bytes) -> tuple[bytes, str]:
    boundary = "----talaqqi" + secrets.token_hex(12)
    out = bytearray()
    for k, v in fields.items():
        out += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    out += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{file_field}\"; filename=\"{filename}\"\r\nContent-Type: {mime}\r\n\r\n".encode()
    out += data + f"\r\n--{boundary}--\r\n".encode()
    return bytes(out), f"multipart/form-data; boundary={boundary}"


class OpenAIProvider(AiProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str, base_url: str = "https://api.openai.com/v1", asr_model: str = "gpt-4o-mini-transcribe", timeout: int = 60):
        if not api_key:
            raise AiUnavailable("OPENAI_API_KEY is empty")
        self.api_key, self.model, self.asr_model, self.base_url, self.timeout = api_key, model, asr_model, base_url.rstrip("/"), timeout

    def _post(self, path: str, data: bytes, content_type: str) -> dict:
        req = urllib.request.Request(f"{self.base_url}{path}", data=data, method="POST",
                                     headers={"Content-Type": content_type, "Authorization": f"Bearer {self.api_key}"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:  # pragma: no cover - network
            detail = e.read()[:300].decode("utf-8", errors="replace")
            raise AiUnavailable(f"openai http {e.code}: {detail}") from e
        except (urllib.error.URLError, TimeoutError, OSError) as e:  # pragma: no cover - network
            raise AiUnavailable(f"openai unreachable: {e}") from e

    def complete(self, system, user, *, max_tokens=400, temperature=0.4):
        body = {"model": self.model, "temperature": temperature, "max_tokens": max_tokens,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        data = self._post("/chat/completions", json.dumps(body).encode("utf-8"), "application/json")
        try:
            return (data["choices"][0]["message"]["content"] or "").strip()
        except (KeyError, IndexError, TypeError) as e:  # pragma: no cover
            raise AiUnavailable("openai: malformed response") from e

    def transcribe(self, audio, filename, mime, *, language="ar", prompt=""):
        fields = {"model": self.asr_model, "language": language, "response_format": "json"}
        if prompt:
            fields["prompt"] = prompt
        body, ctype = _multipart(fields, "file", filename, mime, audio)
        data = self._post("/audio/transcriptions", body, ctype)
        text = data.get("text") if isinstance(data, dict) else None
        if not isinstance(text, str):  # pragma: no cover
            raise AiUnavailable("openai: malformed transcription")
        return text.strip()


class FakeProvider(AiProvider):
    """Deterministic provider for tests and offline demos."""
    name = "fake"
    model = "fake-1"
    asr_model = "fake-asr"

    def __init__(self, reply: str = "مسودة تجريبية.", transcript: str = ""):
        self.reply, self.transcript, self.calls, self.audio_calls = reply, transcript, [], []

    def complete(self, system, user, *, max_tokens=400, temperature=0.4):
        self.calls.append((system, user))
        return self.reply

    def transcribe(self, audio, filename, mime, *, language="ar", prompt=""):
        self.audio_calls.append((len(audio), filename, mime))
        if self.transcript or not prompt:
            return self.transcript
        # Offline demo: a plausible recitation derived from the expected text, with a few slips
        # (every 6th word dropped, every 9th altered) so the report has something to show.
        words = prompt.split()
        out = []
        for i, w in enumerate(words):
            if i % 6 == 5:
                continue
            out.append(w[:-1] + "ه" if i % 9 == 3 and len(w) > 2 else w)
        return " ".join(out)


def get_provider() -> AiProvider:
    kind = (getattr(settings, "AI_PROVIDER", "null") or "null").lower()
    if kind == "openai":
        return OpenAIProvider(getattr(settings, "OPENAI_API_KEY", ""), getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"),
                              getattr(settings, "OPENAI_BASE_URL", "https://api.openai.com/v1"), getattr(settings, "OPENAI_ASR_MODEL", "gpt-4o-mini-transcribe"))
    if kind == "fake":
        return FakeProvider()
    return NullProvider()
