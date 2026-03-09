# PRD: Slack AI Knowledge Assistant

**Version:** 1.0
**Date:** 2026-03-09
**Status:** Draft

---

## 1. Overview

A Slack-integrated AI assistant that answers product behavior questions by searching indexed Confluence and Jira content. Built on top of the existing **AI File Search** core — reusing its embedding engine, RAG pipeline, and Confluence integration — and extending it with Jira ingestion and a Slack bot interface.

### 1.1 Problem Statement

Team members frequently ask product behavior questions in Slack. Answers are scattered across Confluence pages and Jira tickets. Finding the right information requires manual searching across multiple systems, which is slow and often yields incomplete answers.

### 1.2 Solution

A Slack bot that receives questions in natural language, searches a unified index of Confluence and Jira content, generates an answer with citations, and replies directly in the Slack thread.

---

## 2. User Flow

```
┌─────────┐         ┌────────────┐         ┌──────────────────┐
│  User    │         │   Slack    │         │  AI Assistant    │
│ (Slack)  │         │   API      │         │  Service         │
└────┬─────┘         └─────┬──────┘         └───────┬──────────┘
     │                     │                        │
     │  1. Sends question  │                        │
     │  ──────────────────>│                        │
     │                     │  2. Event forwarded    │
     │                     │  ─────────────────────>│
     │                     │                        │
     │                     │         ┌──────────────┴──────────────┐
     │                     │         │ 3. Embed query              │
     │                     │         │ 4. Search FAISS index       │
     │                     │         │    (Confluence + Jira data) │
     │                     │         │ 5. Build context from       │
     │                     │         │    top-k matching chunks    │
     │                     │         │ 6. Generate answer via LLM  │
     │                     │         │    with source citations    │
     │                     │         └──────────────┬──────────────┘
     │                     │                        │
     │                     │  7. Reply with answer  │
     │                     │  <─────────────────────│
     │  8. Sees answer     │                        │
     │  <──────────────────│                        │
     │   with citations    │                        │
```

**Step-by-step:**

1. User sends a question in a Slack channel or DM (e.g., *"What happens when a user resets their password?"*)
2. Slack forwards the message event to the assistant service via the Events API
3. The service embeds the question using `core/embedding.py` (all-MiniLM-L6-v2)
4. FAISS index is searched for the top-k most relevant chunks from Confluence pages and Jira tickets
5. Matching chunks are assembled into a context window
6. The LLM generates a natural-language answer with inline citations
7. The formatted answer is posted back to Slack (in-thread)
8. User sees the answer with clickable links to source Confluence pages and Jira tickets

---

## 3. Functional Requirements

### 3.1 Slack Integration

| ID | Requirement | Priority |
|----|-------------|----------|
| SL-01 | Bot listens for messages where it is mentioned (`@assistant`) or via DM | P0 |
| SL-02 | Bot replies in-thread to keep channels clean | P0 |
| SL-03 | Bot sends a typing indicator while processing | P1 |
| SL-04 | Bot formats answers using Slack Block Kit (bold, links, code blocks) | P1 |
| SL-05 | Bot supports a `/ask` slash command as an alternative to mentions | P2 |
| SL-06 | Bot handles rate limiting from Slack API gracefully | P1 |

### 3.2 Jira Integration (New)

| ID | Requirement | Priority |
|----|-------------|----------|
| JI-01 | Fetch and index Jira issues (summary, description, comments, acceptance criteria) | P0 |
| JI-02 | Support configurable JQL filters to scope which issues are indexed | P0 |
| JI-03 | Track issue `updated` timestamps for incremental sync (same pattern as Confluence sync) | P0 |
| JI-04 | Extract text from Jira's ADF (Atlassian Document Format) rich-text fields | P1 |
| JI-05 | Index issue metadata: status, labels, components, fix version | P1 |

### 3.3 RAG Pipeline (Reuse + Extend)

| ID | Requirement | Priority |
|----|-------------|----------|
| RAG-01 | Reuse existing `core/embedding.py` Embedder for indexing and querying | P0 |
| RAG-02 | Reuse existing `core/ask.py` `answer_question()` for answer generation | P0 |
| RAG-03 | Source-type metadata on each chunk (confluence / jira) to generate correct citation URLs | P0 |
| RAG-04 | Citations must include clickable links to the source Confluence page or Jira issue | P0 |
| RAG-05 | Relevance threshold filtering — return "I don't have enough information" when no chunks score above threshold | P1 |

### 3.4 Data Sync

| ID | Requirement | Priority |
|----|-------------|----------|
| DS-01 | Scheduled sync of Confluence spaces (reuse existing `core/confluence.py`) | P0 |
| DS-02 | Scheduled sync of Jira projects (new `core/jira.py`) | P0 |
| DS-03 | Configurable sync interval (default: every 30 minutes) | P1 |
| DS-04 | Manual sync trigger via admin Slack command (`/sync`) | P2 |

---

## 4. Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NF-01 | Response latency (question → answer posted) | < 15 seconds |
| NF-02 | Service uptime | 99.5% |
| NF-03 | Concurrent question handling | At least 5 simultaneous |
| NF-04 | Index size support | Up to 50,000 chunks |
| NF-05 | Secrets management | No credentials in code; use env vars or secrets manager |

---

## 5. Architecture

### 5.1 Reused Components (from AI File Search)

| Component | Module | What It Provides |
|-----------|--------|------------------|
| Embedding engine | `core/embedding.py` | FAISS indexing + similarity search (all-MiniLM-L6-v2, 384-dim) |
| RAG pipeline | `core/ask.py` | Context assembly + LLM answer generation with citations |
| Confluence client | `core/confluence.py` | Confluence Cloud page fetching and text extraction |
| Text extraction | `core/extract.py` | PDF/DOCX/TXT/MD parsing (for any attached documents) |
| Configuration | `core/config.py` | Centralized constants, speed presets, path management |
| Database | `core/database.py` | SQLite metadata storage |

### 5.2 New Components

| Component | Module | Purpose |
|-----------|--------|---------|
| Slack bot | `slack/bot.py` | Slack Events API listener, message handling, reply formatting |
| Slack formatter | `slack/formatter.py` | Convert RAG answers + citations into Slack Block Kit messages |
| Jira client | `core/jira.py` | Jira Cloud REST API client — fetch issues, extract text, track sync state |
| Sync scheduler | `services/sync.py` | APScheduler-based periodic sync for Confluence + Jira |
| App entry point | `slack_app.py` | Main process — starts Slack bot + sync scheduler |

### 5.3 Deployment Topology

```
┌─────────────────────────────────────────────────┐
│                 Host / Container                │
│                                                 │
│  ┌─────────────┐   ┌─────────────────────────┐  │
│  │  Slack Bot   │   │   Sync Scheduler        │  │
│  │  (bolt-py)   │   │   (APScheduler)         │  │
│  │              │   │                         │  │
│  │  Listens for │   │  Confluence sync (30m)  │  │
│  │  events      │   │  Jira sync (30m)        │  │
│  └──────┬───────┘   └────────────┬────────────┘  │
│         │                        │               │
│         └────────┬───────────────┘               │
│                  ▼                               │
│  ┌──────────────────────────────┐                │
│  │    AI File Search Core       │                │
│  │  embedding / ask / config    │                │
│  ├──────────────────────────────┤                │
│  │  FAISS index  │  SQLite DB   │                │
│  └──────────────────────────────┘                │
└─────────────────────────────────────────────────┘
```

---

## 6. Citation Format

Answers posted to Slack follow this format:

```
<answer text>

📄 Sources:
• <Confluence page title> — <space> · <link>
• <JIRA-123>: <issue summary> · <link>
```

Each source is a clickable Slack link pointing to the original Confluence page or Jira issue.

---

## 7. Configuration

All configuration via environment variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `SLACK_BOT_TOKEN` | Slack Bot User OAuth Token (`xoxb-...`) | Yes |
| `SLACK_APP_TOKEN` | Slack App-Level Token for Socket Mode (`xapp-...`) | Yes |
| `SLACK_SIGNING_SECRET` | Request verification secret | Yes |
| `CONFLUENCE_URL` | Confluence Cloud base URL | Yes |
| `CONFLUENCE_USER` | Confluence API user email | Yes |
| `CONFLUENCE_TOKEN` | Confluence API token | Yes |
| `CONFLUENCE_SPACES` | Comma-separated space keys to index | Yes |
| `JIRA_URL` | Jira Cloud base URL | Yes |
| `JIRA_USER` | Jira API user email | Yes |
| `JIRA_TOKEN` | Jira API token | Yes |
| `JIRA_JQL` | JQL filter for issues to index (default: `project IN (...)`) | No |
| `SYNC_INTERVAL_MINUTES` | Sync frequency (default: 30) | No |
| `LOG_LEVEL` | Logging level (default: INFO) | No |

---

## 8. New Dependencies

| Package | Purpose |
|---------|---------|
| `slack-bolt` | Slack Bot framework (Events API, Socket Mode) |
| `slack-sdk` | Slack Web API client |
| `jira` or `atlassian-python-api` (already installed) | Jira REST API client |

> **Note:** `atlassian-python-api` is already a dependency and supports both Confluence and Jira APIs, so no additional Jira library is needed.

---

## 9. Milestones

| Phase | Scope | Deliverable |
|-------|-------|-------------|
| **Phase 1** | Jira integration + unified index | `core/jira.py`, updated embedding pipeline with source-type metadata |
| **Phase 2** | Slack bot + answer formatting | `slack/bot.py`, `slack/formatter.py`, `slack_app.py` |
| **Phase 3** | Sync scheduler + deployment | `services/sync.py`, Dockerfile, deployment config |
| **Phase 4** | Polish + observability | Logging, error handling, metrics, rate-limit handling |

---

## 10. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM latency exceeds Slack's 3s acknowledgement window | Bot appears unresponsive | Acknowledge immediately, process async, post reply when ready |
| Jira ADF parsing misses content | Incomplete answers | Fallback to plain-text rendering; iterative improvement |
| FAISS index grows beyond memory | Service crashes | Monitor index size; shard or switch to HNSW if needed |
| Slack rate limits during high usage | Dropped replies | Queue outbound messages with exponential backoff |
| Stale indexed content | Incorrect answers | Short sync intervals + manual `/sync` command |

---

## 11. Out of Scope (v1)

- Multi-workspace Slack support
- User authentication / permission-based answer filtering
- Feedback loop (thumbs up/down on answers)
- Conversation memory (follow-up questions in thread)
- Indexing Slack message history
- Web UI for this bot (existing AI File Search UI remains separate)
