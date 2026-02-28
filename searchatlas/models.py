"""Data models for ClickUp message digest."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime


class ChannelType(str, enum.Enum):
    CHANNEL = "CHANNEL"
    DM = "DM"
    GROUP_DM = "GROUP_DM"


class Priority(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @property
    def emoji(self) -> str:
        return {
            Priority.CRITICAL: "🔴",
            Priority.HIGH: "🟠",
            Priority.MEDIUM: "🟡",
            Priority.LOW: "🟢",
        }[self]


@dataclass
class MessageInfo:
    id: str
    text: str
    user_id: str
    username: str
    created_at: datetime
    channel_id: str
    channel_name: str
    channel_type: ChannelType
    reply_count: int = 0
    is_mention: bool = False
    is_thread_reply: bool = False
    priority: Priority = Priority.MEDIUM

    @classmethod
    def from_api(
        cls,
        data: dict,
        channel_id: str,
        channel_name: str,
        channel_type: ChannelType,
        user_lookup: dict[str, str] | None = None,
    ) -> MessageInfo:
        # user_id is a top-level string in the v3 API
        uid = str(data.get("user_id") or "")
        # Resolve username from lookup table (populated from channel members)
        username = (user_lookup or {}).get(uid, "Unknown")

        # Timestamp: "date" field in v3, fallback to "created_at"
        created_ms = data.get("date") or data.get("created_at") or data.get("date_created") or 0
        return cls(
            id=data["id"],
            text=data.get("content") or data.get("text") or "",
            user_id=uid,
            username=username,
            created_at=datetime.fromtimestamp(int(created_ms) / 1000) if created_ms else datetime.now(),
            channel_id=channel_id,
            channel_name=channel_name,
            channel_type=channel_type,
            reply_count=data.get("replies_count") or data.get("reply_count") or 0,
        )


@dataclass
class ChannelSummary:
    id: str
    name: str
    type: ChannelType
    latest_comment_at: int = 0  # unix ms
    num_unread: int = 0
    mention_count: int = 0
    has_unread: bool = False
    messages: list[MessageInfo] = field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict) -> ChannelSummary:
        ch_type_raw = data.get("type") or "CHANNEL"
        try:
            ch_type = ChannelType(ch_type_raw)
        except ValueError:
            ch_type = ChannelType.CHANNEL

        # Channel name: for DMs use member names, fall back to "name"
        name = data.get("name") or ""
        if not name and ch_type in (ChannelType.DM, ChannelType.GROUP_DM):
            members = data.get("members") or []
            name = ", ".join(
                m.get("username") or m.get("name") or "?" for m in members[:3]
            )

        # Counts may or may not be present depending on API version
        counts = data.get("counts") or {}
        return cls(
            id=str(data["id"]),
            name=name or f"Channel {data['id']}",
            type=ch_type,
            latest_comment_at=data.get("latest_comment_at") or 0,
            num_unread=counts.get("num_unread") or 0,
            mention_count=counts.get("mention_count") or 0,
            has_unread=counts.get("has_unread", False),
        )


@dataclass
class InboxDigest:
    user_id: str
    username: str
    fetched_at: datetime = field(default_factory=datetime.now)
    channels: list[ChannelSummary] = field(default_factory=list)
    messages: list[MessageInfo] = field(default_factory=list)
    summary: str | None = None

    @property
    def by_priority(self) -> dict[Priority, list[MessageInfo]]:
        result: dict[Priority, list[MessageInfo]] = {p: [] for p in Priority}
        for msg in self.messages:
            result[msg.priority].append(msg)
        return result

    @property
    def total_unread(self) -> int:
        return sum(ch.num_unread for ch in self.channels)

    @property
    def total_mentions(self) -> int:
        return sum(ch.mention_count for ch in self.channels)

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "fetched_at": self.fetched_at.isoformat(),
            "total_unread": self.total_unread,
            "total_mentions": self.total_mentions,
            "channels": [
                {
                    "id": ch.id,
                    "name": ch.name,
                    "type": ch.type.value,
                    "num_unread": ch.num_unread,
                    "mention_count": ch.mention_count,
                }
                for ch in self.channels
            ],
            "messages": [
                {
                    "id": m.id,
                    "text": m.text[:500],
                    "username": m.username,
                    "channel_name": m.channel_name,
                    "channel_type": m.channel_type.value,
                    "priority": m.priority.value,
                    "is_mention": m.is_mention,
                    "is_thread_reply": m.is_thread_reply,
                    "created_at": m.created_at.isoformat(),
                }
                for m in self.messages
            ],
        }
