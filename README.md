<p align="center">
  <img src="docs/switchyard-logo.jpg" alt="Switchyard logo" width="160" />
</p>

<h1 align="center">Switchyard</h1>

<p align="center">
  <strong>A durable batch inference engine with multi-tenant scheduling.</strong><br />
  Sort live and batch LLM traffic onto the right track — like a rail switchyard.
</p>

<p align="center">
  <a href="#stages"><img src="https://img.shields.io/badge/stage-A%20in%20progress-F5A524?style=flat-square" alt="Stage A" /></a>
  <a href="#stack"><img src="https://img.shields.io/badge/python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" /></a>
  <a href="#stack"><img src="https://img.shields.io/badge/fastapi-uvicorn-009688?style=flat-square" alt="FastAPI" /></a>
  <a href="#guarantee"><img src="https://img.shields.io/badge/delivery-at--least--once-2EC4B6?style=flat-square" alt="Delivery" /></a>
  <a href="https://github.com/pchung39/switchyard"><img src="https://img.shields.io/badge/license-MIT-0B0F14?style=flat-square" alt="License" /></a>
</p>

---

## Why Switchyard?

Most “batch over an LLM” demos stop at a happy-path script. Switchyard is built to answer harder questions:

- What happens when a worker dies mid-request?
- How do you keep **at most one** stored result per prompt?
- How much does protecting live latency cost you in batch throughput?

It targets the kinds of systems problems inference companies care about — retries, recovery, fencing, and admission control — with **tests and measurements** behind every claim.

## Guarantee

> **At-least-once execution attempts, with at most one canonical stored result per request.**

A model call may run twice after a crash (that costs money; it is safe). A unique constraint alone is not the guarantee — lease fencing, idempotent saves, and terminal states are.

| Decision | v1 choice |
| --- | --- |
| When is a request accepted? | When job + request rows commit in Postgres (Stage B+) |
| Terminal failure = accounted for? | Yes — every request ends `SUCCEEDED` or `FAILED` |
| Conflicting outputs? | First committed result wins |
| Stale worker writes? | Rejected via fencing / lease token |

## Stages

Build in four stages. Do not start the next until the stop condition passes.

| Stage | Deliverable | Stop condition |
| --- | --- | --- |
| **A** Execution fundamentals | Async workers → fake HTTP model; bounded retries; terminal states | Every input reaches a terminal state; clean shutdown |
| **B** Durable batch engine | Postgres jobs, leases, crash recovery, idempotent results | Kill/restart workers; every request accounted for; no duplicate results |
| **C** Real inference | Swap fake backend for vLLM; publish baseline metrics | Reproducible throughput / latency / cost with model + GPU recorded |
| **D** Multi-tenant scheduling | Token-rate quotas; live vs batch admission control | Measured tradeoff between throughput, latency, and fairness |

Stages A–C are a complete, defensible project. Stage D is what makes it distinctive for inference companies.

## Architecture (target)

```text
                 ┌─────────────┐
   live traffic ─►│   API       │
                 └──────┬──────┘
                        │
                 ┌──────▼──────┐     ┌─────────┐
                 │  Scheduler  │────►│  Redis  │  quotas / admission
                 └──────┬──────┘     └─────────┘
                        │
   batch jobs ──► Postgres queue ◄── workers (fenced leases)
                        │
                        ▼
                     vLLM / GPU
```

Stages A–C build the batch path (API → store → workers → model). Stage D adds the live path, Redis, and admission control.

## Current status

**Stage A, step 1** — fake OpenAI-compatible server + concurrent client smoke test.

- `fake_model/server.py` — FastAPI `/v1/chat/completions` with random latency and usage accounting
- `scripts/call_once.py` — 10 concurrent requests via `asyncio.gather`

Next up: in-memory store, one worker over 1,000 prompts, then 10 workers, retries, and idempotent saves.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# terminal 1 — fake model
uvicorn fake_model.server:app --host 127.0.0.1 --port 8001

# terminal 2 — concurrent smoke test
python scripts/call_once.py
```

## Project layout

```text
switchyard/
  fake_model/server.py      # FastAPI app: random delay, injected errors
  switchyard/
    models.py               # Job, Request dataclasses; Status enum
    store.py                # in-memory store behind an interface
    client.py               # one shared httpx.AsyncClient
    retry.py                # error classification and backoff
    worker.py               # the worker loop
    cli.py                  # load file, start workers, print progress
  scripts/call_once.py      # early HTTP smoke / concurrency check
  tests/
  data/prompts.jsonl        # 1,000 synthetic prompts
```

## Stack

| Layer | Choice | Why |
| --- | --- | --- |
| Workers / API | Python, FastAPI, asyncio, httpx | Async fits model calls that mostly wait |
| Fake model | Small FastAPI server shaped like vLLM | Real HTTP failures from day one; swap via URL |
| Job state | Postgres (Stage B) | One source of truth; `SKIP LOCKED` queue |
| Self-hosted model | vLLM on Modal (Stage C) | OpenAI-compatible; real metrics |
| Quotas | Redis token buckets (Stage D) | Atomic check-and-take per tenant |

## Hard problems (interview material)

1. **Fencing stale workers** — lease tokens so a late write after expiry cannot overwrite a newer claim
2. **Claiming without double-processing** — `SELECT … FOR UPDATE SKIP LOCKED` (+ why Postgres beats Kafka here at this scale)
3. **Bounded retries** — retry timeouts / 429 / 5xx with exponential backoff + jitter; never retry 400s
4. **What admission control cannot do** — it cannot preempt work already inside vLLM
5. **Quota semantics** — reserve prompt + `max_tokens`, refund unused on completion

## Out of scope

Web UI, real multi-user auth, Kubernetes, multi-region, DB-loss protection, streaming batch results, and fine-tuning.

## License

MIT — see the badge above. Contributions and issue reports welcome once Stage A is green.
