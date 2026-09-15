"""Provider-neutral adapter for OpenAI-compatible chat-completions APIs.

The implementation intentionally uses only Python's standard library so the
runtime does not acquire a provider SDK dependency. It can target hosted APIs,
private gateways, or local OpenAI-compatible servers.
"""
from __future__ import annotations

import json
from typing import Any, Dict
from urllib import error, request as urlrequest

from ..llm_config import LLMConfig
from ..model_adapter import ModelRequest, ModelResponse


class OpenAICompatibleModelAdapter:
    """Invoke an OpenAI-compatible ``/chat/completions`` endpoint."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.config.validate()

    def _endpoint(self) -> str:
        base = self.config.base_url.rstrip("/")
        if base.endswith("/chat/completions"):
            return base
        if base.endswith("/v1"):
            return f"{base}/chat/completions"
        return f"{base}/v1/chat/completions"

    @staticmethod
    def _system_prompt() -> str:
        return (
            "You are the LLM execution layer of MathModel-DE-Skill. "
            "Follow the supplied stage Skill and return a structured response. "
            "Do not invent data, numerical results, references, or execution evidence. "
            "If a requested action cannot be verified, say so explicitly."
        )

    def _build_payload(self, req: ModelRequest) -> Dict[str, Any]:
        context = json.dumps(req.context, ensure_ascii=False, indent=2, default=str)
        user_message = (
            f"TASK_ID: {req.task_id}\n"
            f"STAGE: {req.stage}\n"
            f"INSTRUCTION:\n{req.instruction}\n\n"
            f"RUNTIME CONTEXT:\n{context}\n\n"
            "Return JSON with keys: status, output, message. "
            "output must be an object."
        )
        return {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": self._system_prompt()},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0,
        }

    def invoke(self, request: ModelRequest) -> ModelResponse:
        payload = json.dumps(self._build_payload(request), ensure_ascii=False).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        http_request = urlrequest.Request(
            self._endpoint(), data=payload, headers=headers, method="POST"
        )
        try:
            with urlrequest.urlopen(http_request, timeout=self.config.timeout) as response:
                raw_bytes = response.read()
                raw = json.loads(raw_bytes.decode("utf-8"))
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            return ModelResponse(
                status="error",
                message=f"LLM HTTP {exc.code}: {body[:1000]}",
            )
        except (error.URLError, TimeoutError, OSError) as exc:
            return ModelResponse(status="error", message=f"LLM connection failed: {exc}")
        except json.JSONDecodeError as exc:
            return ModelResponse(status="error", message=f"LLM returned invalid JSON: {exc}")

        content = self._extract_content(raw)
        parsed = self._parse_structured_content(content)
        if parsed is not None:
            return ModelResponse(
                status=str(parsed.get("status", "ok")),
                output=parsed.get("output") if isinstance(parsed.get("output"), dict) else {},
                message=str(parsed.get("message", "")),
                raw=raw,
            )
        return ModelResponse(status="ok", output={"text": content}, raw=raw)

    @staticmethod
    def _extract_content(raw: Dict[str, Any]) -> str:
        choices = raw.get("choices") or []
        if not choices:
            raise ValueError("LLM response contains no choices")
        message = choices[0].get("message") or {}
        content = message.get("content", "")
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
            content = "".join(parts)
        return str(content)

    @staticmethod
    def _parse_structured_content(content: str) -> Dict[str, Any] | None:
        text = content.strip()
        if text.startswith("```") and text.endswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1]).strip()
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            return None
        return value if isinstance(value, dict) else None
