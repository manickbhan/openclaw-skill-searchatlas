---
name: searchatlas
description: "Omni-channel marketing agent — manage ClickUp messages, Slack unreads, and GitLab tickets from one place. Fetch inbox digests, prioritize by urgency, draft responses, and triage across all your marketing channels."
homepage: https://github.com/manickbhan/openclaw-skill-searchatlas
metadata: { "openclaw": { "emoji": "🔍", "requires": { "env": ["CLICKUP_API_TOKEN"], "bins": ["python3"] }, "primaryEnv": "CLICKUP_API_TOKEN" } }
---

# SearchAtlas — Omni-Channel Marketing Agent

Manage your marketing communications across ClickUp, Slack, and GitLab from a single agent interface. Fetch inbox digests, auto-prioritize messages by urgency, draft responses, and keep your team in sync.

## Setup

1. Install dependencies:

```bash
cd ~/.openclaw/skills/searchatlas && pip install -r requirements.txt
```

2. Set your ClickUp API token:

```bash
export CLICKUP_API_TOKEN="your_token_here"
```

Optional environment variables:

| Variable | Purpose |
|---|---|
| `CLICKUP_API_TOKEN` | **Required.** ClickUp Personal API Token |
| `GROQ_API_KEY` | Optional. Enables AI-powered digest summaries and draft responses via Groq |
| `SLACK_TOKEN` | Optional. Enables Slack unread management |
| `GITLAB_TOKEN` | Optional. Enables GitLab ticket operations |

## MCP Server

This skill includes a Model Context Protocol (MCP) server that exposes ClickUp tools. To use it as an MCP server:

```bash
python searchatlas/server.py
```

Configure in your MCP client:

```json
{
  "mcpServers": {
    "searchatlas": {
      "command": "python",
      "args": ["~/.openclaw/skills/searchatlas/searchatlas/server.py"],
      "env": {
        "CLICKUP_API_TOKEN": "your_token"
      }
    }
  }
}
```

## Tools

### `get_message_digest`

Fetch all pending ClickUp messages (DMs, mentions, thread replies, channel messages) and return a prioritized digest.

**Parameters:**
- `hours` (int, default 24) — Lookback window in hours
- `include_read` (bool, default false) — Include channels without unread messages

**Example prompt:** "Show me my ClickUp inbox digest for the last 8 hours"

### `summarize_channel`

Get a summary of recent messages in a specific ClickUp channel.

**Parameters:**
- `channel_id` (string, required) — The ClickUp channel ID
- `limit` (int, default 20) — Max messages to fetch

**Example prompt:** "Summarize the last 20 messages in channel 8chy2nm-1357411"

### `draft_response`

Draft suggested responses for critical and high priority inbox items using AI.

**Parameters:**
- `hours` (int, default 24) — Lookback window in hours

**Example prompt:** "Draft responses for my urgent ClickUp messages"

## Priority Classification

Messages are automatically classified:

| Priority | Criteria |
|---|---|
| **CRITICAL** | DM with a question directed at you, or explicit @mention in DM |
| **HIGH** | Any DM, thread reply to your message, or @mention |
| **MEDIUM** | Active channel thread (reply_count > 0) |
| **LOW** | Other unread channel messages |

## Architecture

```
searchatlas/
├── server.py        # MCP server (stdio transport)
├── client.py        # ClickUp API v3 HTTP client
├── fetcher.py       # Inbox digest orchestration
├── classifier.py    # Priority classification engine
├── models.py        # Data models (channels, messages, priorities)
└── summarizer.py    # LLM summarization via Groq
```

## ClickUp API Reference

### Read Operations
- `GET /api/v3/workspaces/{ws}/chat/channels` — List channels
- `GET /api/v3/workspaces/{ws}/chat/channels/{ch}/messages` — Channel messages
- `GET /api/v3/workspaces/{ws}/chat/messages/{msg}/replies` — Thread replies

### Write Operations
- `POST /api/v3/workspaces/{ws}/chat/channels/direct_message` — Create/get DM channel
- `POST /api/v3/workspaces/{ws}/chat/channels/{ch}/messages` — Send message
- `POST /api/v3/workspaces/{ws}/chat/messages/{msg}/replies` — Thread reply

### Important Conventions
- Auth header: `Authorization: <token>` (no Bearer prefix)
- DM creation is idempotent — returns existing channel if one exists
- Thread replies MUST use the `/replies` endpoint, NOT the channel messages endpoint with a `parent` field
