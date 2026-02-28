"""Priority classification for ClickUp messages."""

from __future__ import annotations

import re

from .models import ChannelType, MessageInfo, Priority


def classify_message(msg: MessageInfo, current_user_id: str) -> Priority:
    """Assign priority based on message characteristics.

    Rules (highest wins):
      CRITICAL — direct mention of current user in a DM, or a question directed at user
      HIGH     — any DM / thread reply to user's message / explicit @mention
      MEDIUM   — unread channel message with reply_count > 0 (active thread)
      LOW      — other unread channel messages
    """
    is_dm = msg.channel_type in (ChannelType.DM, ChannelType.GROUP_DM)
    is_from_other = msg.user_id != current_user_id
    has_question = bool(re.search(r"\?\s*$", msg.text.strip()))

    # Critical: DM with a question directed at you, or explicit @mention in DM
    if is_dm and is_from_other and (has_question or msg.is_mention):
        return Priority.CRITICAL

    # High: any DM from someone else, thread reply, or @mention
    if is_dm and is_from_other:
        return Priority.HIGH
    if msg.is_thread_reply and is_from_other:
        return Priority.HIGH
    if msg.is_mention:
        return Priority.HIGH

    # Medium: active channel thread
    if msg.channel_type == ChannelType.CHANNEL and msg.reply_count > 0:
        return Priority.MEDIUM

    # Low: everything else
    return Priority.LOW


def classify_messages(
    messages: list[MessageInfo], current_user_id: str
) -> list[MessageInfo]:
    """Classify all messages in-place and return them sorted by priority."""
    priority_order = {
        Priority.CRITICAL: 0,
        Priority.HIGH: 1,
        Priority.MEDIUM: 2,
        Priority.LOW: 3,
    }
    for msg in messages:
        msg.priority = classify_message(msg, current_user_id)
    messages.sort(key=lambda m: (priority_order[m.priority], m.created_at))
    return messages
