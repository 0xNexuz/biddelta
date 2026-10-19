"""Synthetic HTTP contract tests only, NOT real inference evidence."""
import json
import httpx
import pytest
from pydantic import SecretStr
from biddelta.nemotron import Proposal, TokenFactory

MODEL = "nvidia/Nemotron-3_5-Lightning"


def adapter(handler, **kwargs):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return TokenFactory(SecretStr("synthetic-test-key"), MODEL, client=client, **kwargs)


def reply(proposal=None, finish="stop", refusal=None):
    return {"id": "synthetic-response", "model": MODEL, "usage": {"total_tokens": 12},
            "choices": [{"finish_reason": finish, "message": {"refusal": refusal,
                "content": json.dumps(proposal or {"changes": [{"source_span_id": "s1",
                 "description": "Proposed deadline change", "requirement_ids": ["r1"]}],
                 "unresolved_notes": ["Human scope review required"]})}}]}


def test_disabled_adapter_never_sends_request():
    def unexpected(request):
        pytest.fail("Disabled adapter attempted network")
    with pytest.raises(PermissionError, match="disabled"):
        adapter(unexpected).propose({"s1": "text"}, ["r1"])


def test_missing_credentials_rejected_before_request():
    client = TokenFactory(SecretStr(""), MODEL, allow_metered=True)
    with pytest.raises(ValueError, match="unavailable"):
        client.propose({"s1": "text"}, ["r1"])


def test_synthetic_request_format_and_source_validation():
    def handler(request):
        assert str(request.url) == "https://api.tokenfactory.nebius.com/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer synthetic-test-key"
        payload = json.loads(request.content)
        assert payload["response_format"]["json_schema"]["schema"] == Proposal.model_json_schema()
        assert payload["response_format"]["json_schema"]["strict"] is True
        assert payload["max_tokens"] == 1024 and payload["store"] is False
        return httpx.Response(200, json=reply())
    result = adapter(handler, allow_metered=True).propose({"s1": "Untrusted source"}, ["r1"])
    assert result.request_id == "synthetic-response"
    assert result.proposal.unresolved_notes


@pytest.mark.parametrize("data", [reply(finish="length"), reply(refusal="Refused"),
    reply({"changes": [{"source_span_id": "fake", "description": "x", "requirement_ids": ["r1"]}],
           "unresolved_notes": []}),
    reply({"changes": [{"source_span_id": "s1", "description": "x", "requirement_ids": ["fake"]}],
           "unresolved_notes": []}),
    reply({"changes": [], "unresolved_notes": [], "approved": True}), {"choices": []}],
    ids=["truncated", "refusal", "bad-source", "bad-dependency", "authority-field", "empty-choices"])
def test_unsafe_or_malformed_synthetic_outputs_rejected(data):
    with pytest.raises(ValueError):
        adapter(lambda _: httpx.Response(200, json=data), allow_metered=True).propose({"s1": "text"}, ["r1"])


def test_provider_failure_has_no_retry():
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(429, json={"error": "synthetic throttling"})
    with pytest.raises(RuntimeError, match="429"):
        adapter(handler, allow_metered=True).propose({"s1": "text"}, ["r1"])
    assert len(calls) == 1
