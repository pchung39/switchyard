<p align="center">
  <img src="docs/switchyard-logo.jpg" alt="Switchyard logo" width="160" />
</p>

<h1 align="center">Switchyard</h1>

<p align="center">
  <strong>A durable batch inference engine with multi-tenant scheduling.</strong><br />
  Async workers push LLM jobs through a self-hosted model, account for every request under failure, and later protect live latency from batch load with admission control.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/fastapi-uvicorn-009688?style=flat-square" alt="FastAPI" />
  <img src="https://img.shields.io/badge/httpx-async-2EC4B6?style=flat-square" alt="httpx" />
  <img src="https://img.shields.io/badge/license-MIT-0B0F14?style=flat-square" alt="License" />
</p>

---

## What it does

Switchyard runs large LLM batch jobs with durable bookkeeping:

- **Async workers** call an OpenAI-compatible `/v1/chat/completions` endpoint
- **Bounded retries** with exponential backoff and jitter for timeouts, `429`, and `5xx` (never retry `400`s)
- **Terminal states** — every request ends `SUCCEEDED` or `FAILED`
- **Idempotent result storage** — at most one canonical result per request
- **Crash recovery** (Postgres leases + fencing tokens) so restarted workers finish the job without duplicate stored results
- **Admission control** (later) — token-rate quotas that trade batch throughput for live latency under mixed load

**Delivery guarantee:** at-least-once execution attempts, at most one stored result per request.

## Architecture

```text
CLI / API
   │
   ▼
Job store  ◄── workers claim requests (queue / leases)
   │
   ▼
Shared httpx.AsyncClient
   │
   ▼
Model server  (fake FastAPI now → vLLM later)
```

The model client always speaks the same HTTP shape. Swapping the fake server for vLLM is a base-URL change. The store sits behind an interface (`claim_next`, `save_result`, `mark_failed`) so in-memory v0 can become Postgres without rewriting workers.

## Project layout

```text
switchyard/
  fake_model/server.py      # FastAPI: latency, usage, injected errors
  switchyard/
    models.py               # Job, Request, Status
    store.py                # store interface + in-memory impl
    client.py               # shared httpx.AsyncClient
    retry.py                # error classification + backoff
    worker.py               # worker loop
    cli.py                  # load prompts, start workers, progress
  scripts/call_once.py      # concurrent smoke test against fake model
  tests/
  data/prompts.jsonl        # synthetic prompts
```

## Stack

| Layer | Choice |
| --- | --- |
| Runtime | Python, asyncio, FastAPI, httpx |
| Fake model | FastAPI server matching vLLM's chat completions API |
| Job state | In-memory store → Postgres (`SKIP LOCKED`, lease tokens) |
| Inference | vLLM (OpenAI-compatible) |
| Quotas | Redis token buckets |
| Tests | pytest, pytest-asyncio |

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# terminal 1
uvicorn fake_model.server:app --host 127.0.0.1 --port 8001

# terminal 2
python scripts/call_once.py
```

`call_once.py` fires 10 concurrent chat-completion requests and prints content, usage, and wall time.

## License

MIT
