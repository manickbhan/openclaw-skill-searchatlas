"""MCP server exposing SearchAtlas omni-channel marketing tools."""

from __future__ import annotations

import json
import os
import sys

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .client import ClickUpClient
from .fetcher import fetch_inbox_digest
from .models import InboxDigest
from .summarizer import summarize_digest, _fallback_summarize

load_dotenv()

app = Server("searchatlas")

_client: ClickUpClient | None = None


def _get_client() -> ClickUpClient:
    global _client
    if _client is None:
        token = os.environ.get("CLICKUP_API_TOKEN")
        if not token:
            raise ValueError("CLICKUP_API_TOKEN not set")
        _client = ClickUpClient(token)
    return _client


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_message_digest",
            description=(
                "Fetch all pending ClickUp messages (DMs, mentions, thread replies, "
                "channel messages) and return a prioritized digest."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "hours": {
                        "type": "integer",
                        "description": "Lookback window in hours (default 24)",
                        "default": 24,
                    },
                    "include_read": {
                        "type": "boolean",
                        "description": "Include channels without unread messages",
                        "default": False,
                    },
                },
            },
        ),
        Tool(
            name="summarize_channel",
            description="Get a summary of recent messages in a specific ClickUp channel.",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "The ClickUp channel ID",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max messages to fetch (default 20)",
                        "default": 20,
                    },
                },
                "required": ["channel_id"],
            },
        ),
        Tool(
            name="draft_response",
            description=(
                "Given a message digest, draft suggested responses for "
                "critical and high priority items."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "hours": {
                        "type": "integer",
                        "description": "Lookback window in hours (default 24)",
                        "default": 24,
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "get_message_digest":
            return await _handle_get_digest(arguments)
        elif name == "summarize_channel":
            return await _handle_summarize_channel(arguments)
        elif name == "draft_response":
            return await _handle_draft_response(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _handle_get_digest(args: dict) -> list[TextContent]:
    client = _get_client()
    digest = fetch_inbox_digest(
        client,
        hours=args.get("hours", 24),
        include_read=args.get("include_read", False),
    )
    digest.summary = summarize_digest(digest)
    return [TextContent(type="text", text=json.dumps(digest.to_dict(), indent=2))]


async def _handle_summarize_channel(args: dict) -> list[TextContent]:
    client = _get_client()
    channel_id = args["channel_id"]
    limit = args.get("limit", 20)

    raw_msgs, _ = client.get_channel_messages(channel_id, limit=limit)
    lines = []
    for msg in raw_msgs:
        user = msg.get("user", {})
        username = user.get("username") or user.get("name", "Unknown")
        text = (msg.get("text") or msg.get("content") or "")[:300]
        lines.append(f"@{username}: {text}")

    summary = "\n".join(lines) if lines else "No messages found."
    return [TextContent(type="text", text=summary)]


async def _handle_draft_response(args: dict) -> list[TextContent]:
    client = _get_client()
    digest = fetch_inbox_digest(client, hours=args.get("hours", 24))

    # Filter to critical and high priority only
    important = [m for m in digest.messages if m.priority.value in ("critical", "high")]
    if not important:
        return [TextContent(type="text", text="No critical or high priority messages requiring response.")]

    lines = ["# Suggested Responses\n"]
    for msg in important[:10]:
        lines.append(f"## {msg.priority.emoji} {msg.channel_name} — @{msg.username}")
        lines.append(f"> {msg.text[:300]}")
        lines.append("")
        lines.append(f"**Suggested action:** Reply to @{msg.username} in #{msg.channel_name}")
        lines.append("")

    # If LLM is available, enhance with AI suggestions via Groq
    api_key = os.environ.get("GROQ_API_KEY")
    if api_key:
        try:
            from openai import OpenAI
            ai = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
            prompt = "Given these ClickUp messages that need responses, draft brief suggested replies:\n\n"
            for msg in important[:5]:
                prompt += f"- From @{msg.username} in #{msg.channel_name}: {msg.text[:200]}\n"
            prompt += "\nDraft a concise reply for each."

            response = ai.chat.completions.create(
                model="llama-3.3-70b-versatile",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            lines.append("---\n## AI-Drafted Replies\n")
            lines.append(response.choices[0].message.content)
        except Exception:
            pass

    return [TextContent(type="text", text="\n".join(lines))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
