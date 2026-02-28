"""Orchestration: fetch channels, messages, detect mentions and threads."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from .classifier import classify_messages
from .client import ClickUpClient
from .models import ChannelSummary, ChannelType, InboxDigest, MessageInfo

log = logging.getLogger(__name__)

STATE_FILE = Path(".clickup_state.json")


def _load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def fetch_inbox_digest(
    client: ClickUpClient,
    *,
    hours: int = 24,
    max_messages_per_channel: int = 50,
    include_read: bool = False,
) -> InboxDigest:
    """Fetch all pending messages and build a classified digest."""
    cutoff = datetime.now() - timedelta(hours=hours)
    cutoff_ms = int(cutoff.timestamp() * 1000)
    user_id = client.user_id
    username = client.username
    state = _load_state()

    log.info("Fetching channels (lookback=%dh, user=%s / %s)", hours, user_id, username)

    # Fetch all channels (paginated)
    raw_channels = client.get_channels(is_follower=False)
    log.info("Total channels in workspace: %d", len(raw_channels))

    # Filter to channels with recent activity
    active_channels = [
        ch for ch in raw_channels
        if (ch.get("latest_comment_at") or 0) > cutoff_ms
    ]
    log.info("Channels with activity in last %dh: %d", hours, len(active_channels))

    # Prioritize: DMs/Group DMs first, then most-recent channels
    dms = [ch for ch in active_channels if ch.get("type") in ("DM", "GROUP_DM")]
    channels_only = [ch for ch in active_channels if ch.get("type") == "CHANNEL"]
    channels_only.sort(key=lambda c: c.get("latest_comment_at", 0), reverse=True)
    channels_to_fetch = dms + channels_only[:30]

    log.info(
        "Fetching messages from %d DMs/Group DMs + %d channels",
        len(dms), min(len(channels_only), 30),
    )

    channels: list[ChannelSummary] = []
    all_messages: list[MessageInfo] = []

    for raw_ch in channels_to_fetch:
        ch = ChannelSummary.from_api(raw_ch)

        # For DMs/Group DMs, fetch members to resolve names
        user_lookup: dict[str, str] = {}
        if ch.type in (ChannelType.DM, ChannelType.GROUP_DM) or not ch.name or ch.name.startswith("Channel "):
            members = client.get_channel_members(ch.id)
            for m in members:
                uid = str(m.get("id", ""))
                uname = m.get("username") or m.get("name") or "Unknown"
                user_lookup[uid] = uname
            # Name DM channels after the other person
            if ch.type in (ChannelType.DM, ChannelType.GROUP_DM) and (not ch.name or ch.name.startswith("Channel ")):
                other_names = [
                    user_lookup[uid] for uid in user_lookup
                    if uid != user_id
                ]
                if other_names:
                    ch.name = ", ".join(other_names)

        log.info("  -> %s (%s)", ch.name, ch.type.value)

        # Fetch messages
        try:
            raw_msgs, _ = client.get_channel_messages(
                ch.id, limit=max_messages_per_channel
            )
        except Exception as exc:
            log.warning("Failed to fetch messages for %s: %s", ch.name, exc)
            continue

        # If we don't have a user_lookup yet (channel), build one from message senders
        # We'll resolve what we can

        for raw_msg in raw_msgs:
            msg = MessageInfo.from_api(
                raw_msg, ch.id, ch.name, ch.type, user_lookup=user_lookup,
            )

            # Skip messages older than cutoff
            if msg.created_at < cutoff:
                continue

            # Skip own messages (but check for thread replies)
            if msg.user_id == user_id:
                if msg.reply_count > 0:
                    _fetch_thread_replies(
                        client, msg, user_id, all_messages, ch, user_lookup,
                    )
                continue

            # Detect mentions
            if _text_mentions_user(msg.text, username):
                msg.is_mention = True

            ch.messages.append(msg)
            all_messages.append(msg)

        if ch.messages:
            channels.append(ch)
            newest = max(ch.messages, key=lambda m: m.created_at)
            state[f"last_seen_{ch.id}"] = newest.created_at.isoformat()

    # Classify all messages by priority
    classify_messages(all_messages, user_id)
    _save_state(state)

    log.info(
        "Digest complete: %d messages across %d channels",
        len(all_messages), len(channels),
    )

    return InboxDigest(
        user_id=user_id,
        username=username,
        channels=channels,
        messages=all_messages,
    )


def _fetch_thread_replies(
    client: ClickUpClient,
    parent_msg: MessageInfo,
    user_id: str,
    all_messages: list[MessageInfo],
    channel: ChannelSummary,
    user_lookup: dict[str, str],
) -> None:
    """Fetch replies to a user's message and add non-user replies."""
    try:
        replies = client.get_message_replies(parent_msg.id)
    except Exception:
        log.warning("Failed to fetch replies for message %s", parent_msg.id)
        return

    for raw_reply in replies:
        reply = MessageInfo.from_api(
            raw_reply, channel.id, channel.name, channel.type,
            user_lookup=user_lookup,
        )
        if reply.user_id != user_id:
            reply.is_thread_reply = True
            channel.messages.append(reply)
            all_messages.append(reply)


def _text_mentions_user(text: str, username: str) -> bool:
    """Check if message text contains an @mention of the user."""
    if not username:
        return False
    text_lower = text.lower()
    return f"@{username.lower()}" in text_lower or "@manick" in text_lower
