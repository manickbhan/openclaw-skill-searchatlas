"""LLM-based digest summarization via Groq Cloud with graceful fallback."""

from __future__ import annotations

import logging
import os

from openai import OpenAI, RateLimitError, APIError, APIConnectionError

from .models import InboxDigest, Priority

log = logging.getLogger(__name__)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "openai/gpt-oss-120b"
MAX_RETRIES = 3
BASE_DELAY = 10


def summarize_digest(digest: InboxDigest) -> str:
    """Summarize the inbox digest using Groq, falling back to a simple summary."""
    api_key = os.environ.get("GROQ_API_KEY")
    if api_key:
        try:
            return _llm_summarize(digest, api_key)
        except Exception as exc:
            log.warning("LLM summarization failed, using fallback: %s", exc)

    return _fallback_summarize(digest)


def _llm_summarize(digest: InboxDigest, api_key: str) -> str:
    """Use Groq Cloud to summarize the digest and suggest actions."""
    import time

    client = OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)

    # Build a concise prompt with message details
    msg_lines = []
    for msg in digest.messages[:30]:
        msg_lines.append(
            f"- [{msg.priority.value.upper()}] #{msg.channel_name} "
            f"({msg.channel_type.value}) from @{msg.username}: "
            f"{msg.text[:300]}"
        )

    messages_text = "\n".join(msg_lines) if msg_lines else "(no messages)"

    prompt = f"""You are summarizing a ClickUp message inbox digest for {digest.username}.

Stats: {len(digest.messages)} messages across {len(digest.channels)} channels, \
{digest.total_mentions} mentions.

Messages (sorted by priority):
{messages_text}

Provide:
1. A brief executive summary (2-3 sentences)
2. Action items grouped by priority (critical first)
3. For each thread/conversation: recommend whether the user should RESPOND (with a suggested brief reply) or can IGNORE
4. Suggested next steps

Be concise. Use markdown formatting."""

    # Retry with backoff on rate limits
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                max_tokens=3000,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content.strip()
        except RateLimitError as exc:
            last_error = exc
            delay = BASE_DELAY * (2 ** attempt)
            log.warning("Rate limited (attempt %d/%d), retrying in %ds", attempt + 1, MAX_RETRIES, delay)
            time.sleep(delay)

    raise last_error


def _fallback_summarize(digest: InboxDigest) -> str:
    """Simple text summary without LLM."""
    by_priority = digest.by_priority
    lines = [
        f"## Inbox Digest for {digest.username}",
        f"**{len(digest.messages)} messages** across "
        f"**{len(digest.channels)} channels** | "
        f"{digest.total_mentions} mentions",
        "",
    ]

    for priority in Priority:
        msgs = by_priority[priority]
        if not msgs:
            continue
        lines.append(f"### {priority.emoji} {priority.value.upper()} ({len(msgs)})")
        for msg in msgs[:10]:
            snippet = msg.text[:120].replace("\n", " ")
            lines.append(
                f"- **{msg.channel_name}** — @{msg.username}: {snippet}"
            )
        if len(msgs) > 10:
            lines.append(f"  _...and {len(msgs) - 10} more_")
        lines.append("")

    if not digest.messages:
        lines.append("_No pending messages — inbox zero!_")

    return "\n".join(lines)
