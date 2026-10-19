# Token Factory feasibility — documentation inspection, 2026-10-19

Status: official documentation inspected; interface IMPLEMENTED; live integration
UNVERIFIED. No model-list API request or metered inference was made. All adapter
responses in tests are synthetic, not evidence of provider behavior.

## Documented models versus account availability
The [official Nebius cookbook Nemotron catalogue](https://github.com/nebius/token-factory-cookbook/blob/main/models/nemotron/README.md)
currently features these NVIDIA model IDs in its model links:

| Documented candidate | ID from catalogue |
| --- | --- |
| Nemotron 3.5 Lightning | `nvidia/Nemotron-3_5-Lightning` |
| Nemotron 3 Super | `nvidia/nemotron-3-super-120b-a12b` |
| Nemotron 3 Ultra | `nvidia/Nemotron-3-Ultra-550b-a55b` |

These are candidates, not a verified account model list. Older Nano examples remain
in the repository but are commented out of the featured catalogue and use differing
ID spellings. Do not infer that those examples are currently available. Keep
NEBIUS_MODEL unset until authenticated account/region verification.

The [official list-models reference](https://docs.tokenfactory.nebius.com/api-reference/models/list-models)
specifies authenticated `GET /v1/models`, optionally with `ai_project_id` and
`verbose`. This is the next source for account-visible IDs; it has not been called.

## Authentication and request contract
The [official quickstart](https://docs.tokenfactory.nebius.com/quickstart) uses
`NEBIUS_API_KEY` with Bearer authentication and the OpenAI-compatible base URL
`https://api.tokenfactory.nebius.com/v1/`. Obtain a key from the Token Factory
account. The [chat reference](https://docs.tokenfactory.nebius.com/api-reference/inference/create-chat-completion)
defines `POST /v1/chat/completions`, `model`, `messages`, token limits and
`response_format`. The adapter sends one non-streamed text-only request with
`store=false` and an output cap of 1024 tokens. It uses httpx directly to avoid an
additional SDK dependency. No model is silently substituted.

## Structured output and tools
The [structured-output guide](https://docs.tokenfactory.nebius.com/ai-models-inference/json)
documents `json_schema` and `json_object` formats. Schema support depends on the
model's JSON-mode capability tag and inference implementation. The adapter uses a
named strict JSON schema and validates the result locally with Pydantic. It rejects
unknown source/dependency references, authority fields, refusal and non-stop
completion. Documentation support does not establish that a selected Nemotron
model accepts this exact schema: that is the blocked real capability check.

The [function-calling guide](https://docs.tokenfactory.nebius.com/ai-models-inference/function-calling)
documents tools, but this milestone does not use tools or execute model actions.
No tool-support claim is made for the account or selected model.

## Limits and failure behavior
The [rate-limit guide](https://docs.tokenfactory.nebius.com/ai-models-inference/rate-limits)
describes dynamic account limits, HTTP 429 and rate-limit headers. Do not assume
example limits apply to this account. Adapter policy: zero automatic retries,
30-second HTTP timeout, no redirects, 32000-character serialized input ceiling,
and 1 MB response ceiling. These are application limits, not provider guarantees.
A 1024-token cap may truncate reasoning or JSON; truncation fails closed. No
latency, accuracy, actual token usage, price, context capacity, region entitlement,
or structured-output reliability has been measured.

## Access requirements and exact next action
Managed environment readiness reported no configured secrets/runtime variables.
NEBIUS_API_KEY is unavailable through configured access. Provider hosts also are
not in the startup environment's documented allowed-host list; the observed
network-policy state was unknown. An actual provider request has not tested egress.
Configure approved access to `api.tokenfactory.nebius.com` before a live check;
do not bypass the environment proxy or destination policy.

1. Supply a server-side Token Factory key through secret configuration, verify
   account/project/credits and provider egress, then list account-visible models.
2. Select the exact NVIDIA Nemotron model ID and confirm its JSON capability.
3. Obtain explicit approval for one bounded metered request. Only then set
   `BIDDELTA_ALLOW_METERED_INFERENCE=true` for that run.
4. Run `TokenFactory.from_env().propose(...)` on a small public synthetic amendment;
   retain sanitized request/schema, response ID, model, usage, duration, errors and
   source-reference validation. Never retain the key. Record adverse outcomes.

There is no live HTTP inference route or startup inference. Proposal output cannot
change approval state or resolve evidence. The caller must persist any live receipt
and independently conduct human impact and scope review. Automated analysis-run
persistence and the full review journey remain P0-B work.
