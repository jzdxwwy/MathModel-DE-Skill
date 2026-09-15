"""Offline contract tests for V0.6-C real LLM adapter."""
from __future__ import annotations

import json
from unittest.mock import patch

from tools.runtime.llm_config import LLMConfig
from tools.runtime.model_adapter import ModelRequest
from tools.runtime.providers.openai_compatible import OpenAICompatibleModelAdapter


def test_config_requires_endpoint_and_model():
    try:
        LLMConfig().validate()
    except ValueError as exc:
        assert "MATHMODEL_LLM_BASE_URL" in str(exc)
    else:
        raise AssertionError("missing endpoint must be rejected")


def test_structured_response_is_normalized():
    config = LLMConfig(base_url="https://example.test/v1", model="demo")
    adapter = OpenAICompatibleModelAdapter(config)
    raw = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "status": "ok",
                    "output": {"kind": "ProblemMap"},
                    "message": "accepted",
                })
            }
        }]
    }
    with patch("tools.runtime.providers.openai_compatible.urlrequest.urlopen") as mocked:
        class Response:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return json.dumps(raw).encode("utf-8")
        mocked.return_value = Response()
        response = adapter.invoke(ModelRequest("t1", "00-start", "inspect"))
    assert response.status == "ok"
    assert response.output["kind"] == "ProblemMap"


def test_safe_config_never_exposes_api_key():
    config = LLMConfig(base_url="https://example.test/v1", model="demo", api_key="SECRET")
    safe = config.safe_dict()
    assert "SECRET" not in str(safe)
    assert safe["api_key_configured"] is True
