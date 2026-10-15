# memento

A **personal knowledge / notes assistant** built end-to-end on
[agentkit](https://github.com/kakalition/agentkit).

memento captures notes, tags and organizes them, recalls them **by meaning**,
sets **durable reminders**, produces a **weekly digest**, and **learns** the
owner's note-taking preferences over time — owner-scoped, approval-gated for
writes, audited, and operable from the built-in web UI and CLI.

It is a complete, runnable agentkit application (not a framework change). Use it
as a working reference for wiring a real agent with persistence, retrieval,
scheduling, background jobs, self-learning, safety, and observability.

---

## Table of contents

- [What it does](#what-it-does)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Install](#install)
- [Configure](#configure)
- [Quickstart](#quickstart)
- [Using memento](#using-memento)
  - [CLI reference](#cli-reference)
  - [Capture and recall](#capture-and-recall)
  - [Approvals (human-in-the-loop)](#approvals-human-in-the-loop)
  - [Scheduling and durable jobs](#scheduling-and-durable-jobs)
  - [Semantic recall and embeddings](#semantic-recall-and-embeddings)
  - [Self-learning](#self-learning)
  - [Web UI](#web-ui)
- [Evaluation](#evaluation)
- [Testing and linting](#testing-and-linting)
- [Data model and storage](#data-model-and-storage)
- [Security model](#security-model)
- [Production deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)
- [Extending memento](#extending-memento)
- [Project layout](#project-layout)
- [License](#license)

---

## What it does

| Capability | How memento implements it |
| --- | --- |
| **Capture** | `capture_note(title, body, tags)` saves a note and fires `note.saved` |
| **Recall** | `search_notes(query)` searches the knowledge base by meaning, with a lexical fallback over title/body/tags |
| **Organize** | `list_notes(tag, limit)`, `get_note(id)`, `tag_note(id, tags)` |
| **Retire** | `archive_note(id)` — approval-gated; also removes the note from recall |
| **Remind** | `set_reminder(message, at)` writes a durable one-off schedule for the `remind` task |
| **Digest** | `digest` durable task sends a weekly summary (captured notes, top tags, stale notes) |
| **Stay in sync** | `sync_notes` re-indexes notes every 15 minutes and forgets archived ones |
| **Learn** | `.learning()` runs the reflect → learn → apply loop and injects lessons into the instructions |

The agent also exposes agentkit's native toolkits — database CRUD (`db_*`),
scheduler (`schedule_*`), queue (`enqueue_*`), notifications (`notify`), history,
usage/audit, knowledge admin, and skill authoring — all allow-listed and, for
writes, approval-gated.

## Architecture

```
                 ┌──────────────────────────────────────────────────────────┐
   chat / tinker │                      memento agent                        │
   web UI ───────┤  instructions + SOUL.md + learned lessons + skills index  │
                 │                                                          │
                 │  capture_note ─┐   search_notes ─┐   set_reminder ─┐      │
                 │  list_notes    │   get_note      │   tag_note      │      │
                 │  archive_note (approval)         │                 │      │
                 └────────┬───────────────┬─────────┴────────┬────────┴─────┘
                          │               │                  │
                    NoteService     KnowledgeBase       ScheduledJobRepo
                          │               │                  │
               ┌──────────▼───────┐  ┌────▼──────────┐  ┌────▼───────────────┐
   note.saved →│  notes (SQLite)  │  │ knowledge_    │  │ scheduled_jobs      │
   (event)     └──────────────────┘  │ chunks (RAG)  │  └────┬───────────────┘
        │                            └───────────────┘       │
        ├─ IndexNoteOnSave ──────────────┘                   │  sync_notes (*/15)
        └─ LogNoteSaved                                      ├─ digest   (Mon 08:00)
                                                             └─ remind   (one-off)
                                                                     │
                                                        deliver into the conversation
```

- **One domain table** (`notes`) plus the shared knowledge chunks. Reminders and
  the digest reuse agentkit's durable scheduler — no extra tables.
- **Indexing lives in a listener.** `capture_note` emits `note.saved`; the async
  `IndexNoteOnSave` listener writes the note into the knowledge base *through the
  current turn's repository session*, avoiding cross-session SQLite writes.
  `sync_notes` repairs any drift (edits, archives, restarts).
- **Writes are approval-gated.** `archive_note` and every native write tool
  (`db_create`, `db_update`, `db_delete`, `schedule_task`, `enqueue_*`, …) are
  registered with `requires_approval=True`.

## Requirements

- Python **3.11 or 3.12** (agentkit supports `>=3.11,<3.13`)
- [`uv`](https://docs.astral.sh/uv/) (recommended) or `pip`
- A **sibling `agentkit` checkout** (see [Install](#install)) — memento depends on
  it as an editable path source
- A model provider key for live turns (default: OpenAI). Tests and the offline
  path need **no** key.

## Install

memento expects the agentkit repository as a sibling directory:

```
/your/workspace/
├── agentkit/      # https://github.com/kakalition/agentkit
└── memento/       # this repository
```

```bash
# 1. clone both, side by side
cd /your/workspace
git clone https://github.com/kakalition/agentkit.git
git clone https://github.com/kakalition/memento.git

# 2. install memento (resolves agentkit from ../agentkit, editable)
cd memento
uv sync --extra dev           # add: --extra memory   (local embeddings)
```

`pyproject.toml` wires the dependency explicitly:

```toml
[tool.uv.sources]
agentkit = { path = "../agentkit", editable = true }
```

To use a different agentkit location, edit that path (or point it at a git
source). See [Extending](#extending) for details.

## Configure

```bash
cp .env.example .env
$EDITOR .env                  # at minimum, set OPENAI_API_KEY
```

Configuration is plain environment variables (12-factor). `.env` is loaded in
development and **must not be committed**.

### Environment reference

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | — | Provider key for the model in `MODEL_NAME` (**required for live turns**) |
| `MODEL_NAME` | `openai:gpt-4o-mini` | `provider:model`; providers: `openai`, `anthropic`, `google`, `groq`, `mistral`, `ollama`, `openai-compatible` |
| `AGENT_NAME` | `memento` | Agent name (also the default data subdirectory) |
| `OWNER_ID` / `OWNER_NAME` | `owner` / `Owner` | The single owner this instance serves |
| `AGENTKIT_HOME` | `~/.agentkit` | Data root; the agent home becomes `$AGENTKIT_HOME/memento` |
| `DATABASE_URL` | *(SQLite in agent home)* | Set to `postgresql://…` to use Postgres instead of SQLite |
| `QUEUE_ENABLED` | `false` | `false` runs jobs inline; `true` persists them for `agentkit queue:work` |
| `LEARNING_ENABLED` | `true` | Enable the reflect → learn → apply loop |
| `MEMORY_EMBEDDING_BACKEND` | provider default | `hash` (offline/tests) or `sentence-transformers` (real vectors; needs `--extra memory`) |
| `WEBUI_ENABLED` | `true` | Serve the operator web UI |
| `WEBUI_HOST` / `WEBUI_PORT` | `127.0.0.1` / `8787` | Web UI bind address |
| `APPROVALS_ENABLED` | `true` | Defer approval-gated tool calls to an approver |
| `APPROVAL_UI_ENABLED` | `false` | Route approvals through the in-process queue (web UI) |
| `AUTH_ENABLED` | `false` | Require an API key/JWT on HTTP surfaces (fail-closed) |
| `AUTH_API_KEYS` | — | API keys, e.g. `name:key:owner:admin` |
| `METRICS_ENABLED` | `false` | Expose Prometheus metrics at `METRICS_PATH` |
| `OBSERVABILITY` | `phoenix` | `phoenix`, `console`, `otlp`, or `off` |
| `LOG_LEVEL` / `LOG_JSON` | `INFO` / `false` | Logging |
| `DB_TOOLS_ENABLED`, `SCHEDULER_TOOLS_ENABLED`, `QUEUE_TOOLS_ENABLED`, `NOTIFICATION_TOOLS_ENABLED`, `HISTORY_TOOLS_ENABLED`, `USAGE_TOOLS_ENABLED`, `KNOWLEDGE_ADMIN_ENABLED`, `SKILL_AUTHORING_ENABLED` | `true` | Opt out of individual native toolkits |
| `TELEGRAM_BOT_TOKEN`, `SLACK_*`, `DISCORD_BOT_TOKEN`, `EMAIL_*` | — | Channels activate only when their token/env is present |

See `.env.example` for the annotated, copy-pasteable list.

## Quickstart

```bash
cd memento
cp .env.example .env          # set OPENAI_API_KEY
uv sync

uv run agentkit inspect       # tools, toolkits, allow-lists, learning state
uv run agentkit tinker        # chat with the agent
uv run agentkit serve         # web UI + scheduler at http://127.0.0.1:8787
```

Offline (no key) you can still run everything except live model turns:

```bash
uv run pytest -q
uv run ruff check .
uv run agentkit schedule:list
uv run agentkit learning:reflect --dry-run
```

## Using memento

### CLI reference

All commands boot `bootstrap:app` (override with `--bootstrap module:attr`).

```bash
uv run agentkit tinker                     # interactive REPL
uv run agentkit serve                      # web UI + scheduler + channels
uv run agentkit serve --no-webui           # headless (channels + scheduler)
uv run agentkit inspect                    # agent, tools, toolkits, allow-lists

uv run agentkit schedule:list              # durable cron + one-off jobs
uv run agentkit schedule:run               # run anything currently due

uv run agentkit queue:work                 # process queued jobs (QUEUE_ENABLED=true)
uv run agentkit queue:work --once          # drain what is available, then exit
uv run agentkit queue:failed               # list failed jobs

uv run agentkit learning:reflect           # run the reflect loop now
uv run agentkit learning:reflect --dry-run # preview without writing
uv run agentkit learning:lessons           # list learned lessons

uv run agentkit eval evals/notes.yaml      # run an eval suite
uv run agentkit note:pin                   # pin the most recent note

uv run agentkit migrate                     # create/reconcile schema
uv run agentkit db:backup --out memento.db.bak
uv run agentkit health                      # per-dependency readiness
```

### Capture and recall

From `tinker`, just talk to it (illustrative transcript):

```
agentkit> remember to ship memento before Friday #work
saved note #1: Ship memento

agentkit> what did I note about memento?
[1] note note:1 #0
Ship memento
tags: work
```

The same flows are the eval cases in `evals/notes.yaml`.

### Approvals (human-in-the-loop)

Writes defer to an approver rather than executing silently. Three ways to satisfy
them:

1. **Web UI** — set `APPROVAL_UI_ENABLED=true`; deferred calls appear in the
   approval queue and you approve/deny there.
2. **Programmatic handler** — pass `approve=` to `app.run(...)` (a callable that
   receives the pending `ApprovalRequest`s and returns `{tool_call_id: bool}`).
3. **Non-interactive runs** — wire an auto-approver when you trust the caller.

Reads (`search_notes`, `list_notes`, `get_note`, `db_find`, …) never need
approval. Only `archive_note` and the native write tools do.

### Scheduling and durable jobs

- **`sync-notes`** — every 15 minutes, re-index notes into the knowledge base and
  forget archived ones (`*/15 * * * *`).
- **`weekly-digest`** — Mondays at 08:00 (`0 8 * * 1`), delivers a summary into the
  conversation.
- **`remind`** — one-off, created by `set_reminder`, delivered at the requested
  time.
- agentkit's `memory-consolidate` (daily) and `learning-reflect` (daily) are
  scheduled by `FullStackProvider`; the console kernel deliberately does not
  duplicate them.

Schedules are stored in the database and survive restarts. Tasks are
**at-least-once**, so they are written to be idempotent (re-index replaces a
source; `remind`/`digest` append a single message per run).

```bash
uv run agentkit schedule:list
uv run agentkit schedule:run         # catch up on anything due
```

### Semantic recall and embeddings

Notes are chunked and indexed with an embedding per chunk. Search ranks by cosine
similarity and appends keyword matches, so it works with or without a real
embedder:

- **Offline / CI:** `MEMORY_EMBEDDING_BACKEND=hash` — deterministic, no downloads.
- **Production:** install local embeddings and let semantic recall shine:

  ```bash
  uv sync --extra memory
  # .env: MEMORY_EMBEDDING_BACKEND=sentence-transformers
  ```

`search_notes` formats the best passages; when nothing is indexed it falls back to
a lexical scan over title/body/tags.

### Self-learning

With `LEARNING_ENABLED=true` (default), memento:

- collects turn signals, reflects daily (`learning:reflect`) or on demand, and
  extracts **lessons**, **preferences**, and **facts**;
- stores them (lessons as procedural memory), deduped and importance-ranked;
- injects a compact lessons digest into the agent's instructions so learned
  behavior changes future turns;
- can distill recurring lessons into `SKILL.md` files (governed by
  `LEARNING_AUTO_SKILLS` / `LEARNING_SKILL_THRESHOLD`).

```bash
uv run agentkit learning:reflect --dry-run   # preview extraction
uv run agentkit learning:lessons             # inspect stored lessons
uv run agentkit learning:forget <id>         # remove one
```

### Web UI

`agentkit serve` starts an operator UI at `http://127.0.0.1:8787` (loopback by
default) showing conversations, schedules, the audit trail, memory, knowledge
sources, the approval queue, and learned lessons. Bind it elsewhere only behind a
reverse proxy with `AUTH_ENABLED=true`.

## Evaluation

`evals/notes.yaml` covers persona, capture, recall, and tagging; `evals/smoke.yaml`
is a minimal suite. Evals require a live model (a provider key):

```bash
uv run agentkit eval evals/notes.yaml
uv run agentkit eval evals/smoke.yaml
uv run agentkit eval:capture --conversation cli:tinker   # turn real chats into cases
```

## Testing and linting

Tests are **hermetic**: a temporary `AGENT_HOME`, the offline `hash` embedder, and
PydanticAI `FunctionModel` for turn-level tests. No network, no key.

```bash
uv run pytest -q          # test suite
uv run ruff check .       # lint
```

What the suite covers:

- repository/service CRUD and owner scoping;
- note → knowledge-base indexing and recall (offline embedder);
- durable task registration and schedule registration (`sync-notes`,
  `weekly-digest`, no duplicate core schedules);
- native allow-list enforcement (unknown model → error) and approval flags
  (`archive_note`/`db_delete` require approval);
- the built agent exposing the expected tools/toolkits;
- a `FunctionModel`-driven turn that captures a note;
- the digest summary builder and the `remind`/`digest` tasks delivering into the
  conversation.

## Data model and storage

Everything lives under the agent home (`$AGENTKIT_HOME/memento`, default
`~/.agentkit/memento`): a SQLite database (libSQL), storage, and logs.

`Note` (table `notes`): `id`, `owner_id` (indexed), `title`, `body`, `tags`
(normalized lowercase, comma-separated), `source` (`chat`/`cli`/`web`), `pinned`,
`archived`, `created_at`, `updated_at`. Schema is created from model metadata at
startup; drifted columns are reconciled automatically — no migration step needed.

```bash
uv run agentkit migrate
uv run agentkit db:backup --out memento.db.bak    # WAL-safe backup
uv run agentkit db:restore memento.db.bak --yes
```

## Security model

- **Owner scoping** — every repository query filters by `owner_id`.
- **Deny-by-default allow-lists** — the app names the one reachable model
  (`note`), the tasks (`sync_notes`, `digest`, `remind`), and the job (`sync`);
  nothing else is reachable by the model.
- **Approval-gated writes** — destructive/mutating tools defer to an approver.
- **Audited** — writes append to agentkit's hash-chained audit log.
- **No raw SQL** — the database toolkit works through typed repositories only.

## Production deployment

### Process model

One process supervises the scheduler, the web UI, and any channels
(`agentkit serve`). Keep **exactly one scheduler leader**. If you enable the
durable queue, run workers alongside it:

```bash
# leader: web UI + scheduler + channels
uv run agentkit serve

# workers (scale horizontally; the queue is DB-backed)
QUEUE_ENABLED=true uv run agentkit queue:work
```

### Recommended production settings

```dotenv
# model + data
MODEL_NAME=openai:gpt-4o-mini
AGENTKIT_HOME=/data

# security
APPROVALS_ENABLED=true
APPROVAL_UI_ENABLED=true
AUTH_ENABLED=true
AUTH_API_KEYS=memento:REPLACE_ME:owner:admin
WEBUI_HOST=127.0.0.1          # keep loopback; terminate TLS at a proxy

# durability + scale
QUEUE_ENABLED=true
# DATABASE_URL=postgresql://user:pass@host/memento   # optional; single writer

# operations
METRICS_ENABLED=true
OBSERVABILITY=otlp
OTLP_ENDPOINT=http://collector:4318
LOG_JSON=true
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# recall
MEMORY_EMBEDDING_BACKEND=sentence-transformers   # requires --extra memory
```

### Reverse proxy and TLS

Bind the web UI to `127.0.0.1` and put nginx/Caddy in front. Example Caddy:

```
memento.example.com {
    reverse_proxy 127.0.0.1:8787
}
```

### Health and metrics

- `GET /healthz` (liveness) and `GET /readyz` (readiness) on the web app.
- `GET /api/health` for per-dependency readiness; `agentkit health` locally.
- Prometheus metrics at `METRICS_PATH` (default `/metrics`) when
  `METRICS_ENABLED=true`: turns and latency, tool errors, queue depth, scheduler
  runs, estimated cost.

### Container

```dockerfile
FROM python:3.12-slim

WORKDIR /app
# memento expects agentkit as a sibling of the project:
COPY agentkit /agentkit
COPY memento  /app/memento
WORKDIR /app/memento
RUN pip install --no-cache-dir uv && uv sync --frozen --no-dev

ENV AGENTKIT_HOME=/data
VOLUME ["/data"]
EXPOSE 8787
CMD ["uv", "run", "agentkit", "serve"]
```

The single `/data` volume persists the database, artifacts, and logs.

### Backups and upgrades

```bash
uv run agentkit db:backup --out /backups/memento-$(date +%F).db
# deploy new code, then:
uv run agentkit migrate
```

## Troubleshooting

| Symptom | Likely cause / fix |
| --- | --- |
| `OpenAIError: Missing credentials` | `OPENAI_API_KEY` unset in `.env`; set it (or use another provider via `MODEL_NAME`) |
| `agentkit` cannot be resolved / `uv sync` fails | the sibling `agentkit` checkout is missing — see [Install](#install) |
| A write tool "does nothing" | it was deferred for approval; enable `APPROVAL_UI_ENABLED` or pass an approver |
| `search_notes` returns nothing | no notes indexed yet (capture one), or run `agentkit schedule:run` / `sync_notes` |
| Recall is keyword-only | install `--extra memory` and set `MEMORY_EMBEDDING_BACKEND=sentence-transformers` |
| Jobs never run | `QUEUE_ENABLED=true` requires a running `agentkit queue:work`; or use the scheduler-queued tasks |
| Database is locked | two writers on one SQLite file; keep one scheduler/worker leader |
| Web UI unreachable off-box | it binds loopback by default — set `WEBUI_HOST` behind a proxy + auth |

## Extending memento

- **A normalized tag table.** Add a `Tag` model and a `NoteTag` join, add both to
  `Agent.database({...})` and `App.models({...})`, and include them in `sync_notes`.
- **A channel** (Telegram/Slack/…). Uncomment its token in `.env`;
  `FullStackProvider` wires the gateway and `Reminder`/`NotesDigest` can target it.
- **Another capture surface.** Call `NoteService.capture(...)` from a CLI command
  or webhook and emit `note.saved` — indexing happens automatically.
- **A different agentkit source.** Point `[tool.uv.sources].agentkit` at a git tag
  or a published distribution instead of `../agentkit`.

## Project layout

```
bootstrap.py                       # App(name="memento", ...) + providers
app/
  Agents/assistant.py              # build_assistant(kb) — the agent builder
  Console/Kernel.py                # schedule: sync-notes + weekly-digest
  Console/Commands/PinNote.py      # agentkit note:pin
  Events/NoteSaved.py              # note.saved payload
  Listeners/IndexNoteOnSave.py     # index a saved note into the knowledge base
  Listeners/LogNoteSaved.py        # log every saved note
  Jobs/SyncNotes.py                # re-index notes (job + durable task)
  Jobs/Digest.py                   # weekly digest (durable task)
  Jobs/Remind.py                   # deliver a reminder (durable task)
  Models/Note.py                   # the note table
  Notifications/                   # NoteSaved, NotesDigest, Reminder
  Policies/MementoPolicy.py        # ToolPolicy
  Repositories/                    # AppRepositories + NoteRepository
  Services/NoteService.py          # capture / search / tag / archive / pin
  Support/                         # tag helpers, index text, delivery
  Tools/notes.py                   # capture_note, search_notes, … set_reminder
config/{app,learning,memory,channels}.py
skills/{note-formats,daily-review}/SKILL.md
prompts/system.md
SOUL.md
evals/{smoke,notes}.yaml
tests/
```

## License

MIT. See [LICENSE](./LICENSE). memento is a companion use-case for
[agentkit](https://github.com/kakalition/agentkit).
