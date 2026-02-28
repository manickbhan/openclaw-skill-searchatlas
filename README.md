# SearchAtlas — OpenClaw Skill

Omni-channel marketing agent for [OpenClaw](https://openclaw.ai). Manage ClickUp messages, prioritize your inbox, and draft responses — all from your AI agent.

## Features

- **Inbox Digest** — Fetch all pending ClickUp messages (DMs, mentions, threads) with automatic priority classification
- **Channel Summaries** — Get quick summaries of any ClickUp channel
- **AI Draft Responses** — Auto-draft replies for critical and high-priority messages using Groq LLM
- **Priority Engine** — Messages classified as Critical / High / Medium / Low based on type, mentions, and context

## Install

### OpenClaw (recommended)

Paste this GitHub URL into your OpenClaw chat, or:

```bash
# Manual install
git clone https://github.com/manickbhan/openclaw-skill-searchatlas.git \
  ~/.openclaw/skills/searchatlas
cd ~/.openclaw/skills/searchatlas && pip install -r requirements.txt
```

### As MCP Server

Add to your MCP client config (Claude Code, Cursor, etc.):

```json
{
  "mcpServers": {
    "searchatlas": {
      "command": "python",
      "args": ["-m", "searchatlas.server"],
      "cwd": "/path/to/openclaw-skill-searchatlas",
      "env": {
        "CLICKUP_API_TOKEN": "your_token"
      }
    }
  }
}
```

## Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `CLICKUP_API_TOKEN` | Yes | ClickUp Personal API Token |
| `GROQ_API_KEY` | No | Enables AI-powered summaries and draft responses |

## Tools

| Tool | Description |
|---|---|
| `get_message_digest` | Fetch prioritized inbox digest (DMs, mentions, threads) |
| `summarize_channel` | Summarize recent messages in a ClickUp channel |
| `draft_response` | AI-draft responses for urgent messages |

## Priority Classification

| Priority | Criteria |
|---|---|
| CRITICAL | DM with question or @mention directed at you |
| HIGH | Any DM, thread reply to your message, or @mention |
| MEDIUM | Active channel thread (has replies) |
| LOW | Other unread messages |

## License

MIT
