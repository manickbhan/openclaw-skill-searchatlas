"""ClickUp API v3 HTTP client with pagination and rate limiting."""

from __future__ import annotations

import logging
import time
from typing import Any, Iterator

import httpx

log = logging.getLogger(__name__)

API_BASE = "https://api.clickup.com"


class RateLimitError(Exception):
    """Raised when rate limit is hit and cannot be retried."""


class ClickUpClient:
    """Thin wrapper around the ClickUp REST API."""

    def __init__(self, api_token: str, workspace_id: str | None = None):
        self.api_token = api_token
        # ClickUp uses plain token (no "Bearer" prefix)
        self._http = httpx.Client(
            base_url=API_BASE,
            headers={"Authorization": api_token, "Content-Type": "application/json"},
            timeout=30.0,
        )
        self._user: dict | None = None
        self._workspace_id = workspace_id

    # ------------------------------------------------------------------
    # Identity helpers
    # ------------------------------------------------------------------

    def get_me(self) -> dict:
        """GET /api/v2/user — returns authenticated user info."""
        if self._user is None:
            resp = self._request("GET", "/api/v2/user")
            self._user = resp.get("user", resp)
        return self._user

    @property
    def user_id(self) -> str:
        return str(self.get_me()["id"])

    @property
    def username(self) -> str:
        return self.get_me().get("username") or self.get_me().get("name", "")

    @property
    def workspace_id(self) -> str:
        if self._workspace_id:
            return self._workspace_id
        # Auto-discover from teams endpoint
        resp = self._request("GET", "/api/v2/team")
        teams = resp.get("teams", [])
        if not teams:
            raise ValueError("No workspaces found for this API token")
        self._workspace_id = str(teams[0]["id"])
        log.info("Auto-discovered workspace_id: %s", self._workspace_id)
        return self._workspace_id

    # ------------------------------------------------------------------
    # Chat API v3
    # ------------------------------------------------------------------

    def get_channels(
        self,
        *,
        is_follower: bool = True,
        channel_types: list[str] | None = None,
        with_message_since: int | None = None,
    ) -> list[dict]:
        """Fetch all chat channels (paginated)."""
        params: dict[str, Any] = {}
        if is_follower:
            params["is_follower"] = "true"
        if channel_types:
            params["channel_types"] = ",".join(channel_types)
        if with_message_since:
            params["with_message_since"] = str(with_message_since)

        url = f"/api/v3/workspaces/{self.workspace_id}/chat/channels"
        return list(self._paginate(url, params, result_key="data"))

    def get_channel_messages(
        self,
        channel_id: str,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[dict], str | None]:
        """Fetch messages for a channel. Returns (messages, next_cursor)."""
        params: dict[str, Any] = {"limit": str(limit)}
        if cursor:
            params["cursor"] = cursor
        url = f"/api/v3/workspaces/{self.workspace_id}/chat/channels/{channel_id}/messages"
        resp = self._request("GET", url, params=params)
        messages = resp.get("messages") or resp.get("data") or []
        next_cursor = resp.get("next_cursor") or resp.get("cursor")
        return messages, next_cursor

    def get_message_replies(self, message_id: str) -> list[dict]:
        """Fetch thread replies for a message."""
        url = (
            f"/api/v3/workspaces/{self.workspace_id}/chat/messages/{message_id}/replies"
        )
        try:
            resp = self._request("GET", url)
            return resp.get("replies") or resp.get("messages") or resp.get("data") or []
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return []
            raise

    def get_channel_members(self, channel_id: str) -> list[dict]:
        """Fetch members of a channel. Returns list of member dicts."""
        url = (
            f"/api/v3/workspaces/{self.workspace_id}/chat/channels/{channel_id}/members"
        )
        try:
            return list(self._paginate(url, {}, result_key="data"))
        except httpx.HTTPStatusError:
            return []

    # ------------------------------------------------------------------
    # Write operations (Chat API v3)
    # ------------------------------------------------------------------

    def send_message(self, channel_id: str, content: str) -> dict:
        """Post a top-level message to a channel."""
        url = f"/api/v3/workspaces/{self.workspace_id}/chat/channels/{channel_id}/messages"
        return self._request("POST", url, json={"content": content})

    def send_reply(self, message_id: str, content: str) -> dict:
        """Post a thread reply to a message."""
        url = (
            f"/api/v3/workspaces/{self.workspace_id}/chat/messages/{message_id}/replies"
        )
        return self._request("POST", url, json={"content": content})

    def delete_message(self, message_id: str) -> None:
        """Delete a message. Returns None on success (204)."""
        url = f"/api/v3/workspaces/{self.workspace_id}/chat/messages/{message_id}"
        resp = self._http.request("DELETE", url)
        resp.raise_for_status()

    def create_dm_channel(self, user_ids: list[str]) -> dict:
        """Create or retrieve a DM channel (idempotent).

        Returns channel dict with 'id', 'type', etc.
        """
        url = f"/api/v3/workspaces/{self.workspace_id}/chat/channels/direct_message"
        resp = self._request(
            "POST", url, json={"user_ids": [int(uid) for uid in user_ids]}
        )
        return resp.get("data", resp)

    def get_workspace_members(self) -> list[dict]:
        """Fetch all workspace members via v2 team endpoint."""
        resp = self._request("GET", f"/api/v2/team/{self.workspace_id}")
        team = resp.get("team", resp)
        return team.get("members", [])

    # ------------------------------------------------------------------
    # Low-level HTTP
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
        _retries: int = 2,
    ) -> dict:
        """Make an API request with rate-limit handling."""
        for attempt in range(_retries + 1):
            resp = self._http.request(method, url, params=params, json=json)

            # Rate limit handling
            remaining = resp.headers.get("X-RateLimit-Remaining")
            if remaining is not None and int(remaining) <= 1:
                reset = resp.headers.get("X-RateLimit-Reset")
                if reset:
                    sleep_until = int(reset) - int(time.time())
                    if sleep_until > 0:
                        log.warning("Rate limit near zero, sleeping %ds", sleep_until)
                        time.sleep(min(sleep_until, 60))

            if resp.status_code == 429:
                if attempt < _retries:
                    retry_after = int(resp.headers.get("Retry-After", "5"))
                    log.warning("429 rate limited, retrying in %ds", retry_after)
                    time.sleep(retry_after)
                    continue
                raise RateLimitError("Rate limit exceeded after retries")

            resp.raise_for_status()
            return resp.json()

        # Should not reach here
        return {}

    def _paginate(
        self,
        url: str,
        params: dict[str, Any],
        result_key: str,
    ) -> Iterator[dict]:
        """Auto-paginate cursor-based endpoints."""
        cursor: str | None = None
        while True:
            page_params = dict(params)
            if cursor:
                page_params["cursor"] = cursor
            resp = self._request("GET", url, params=page_params)
            items = resp.get(result_key) or []
            yield from items
            cursor = resp.get("next_cursor")
            if not cursor or not items:
                break

    def close(self):
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
