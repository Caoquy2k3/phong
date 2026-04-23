from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx


@dataclass
class GoLikeClient:
    base_url: str
    token: str
    t: Optional[str] = None
    timeout: float = 15.0

    def _headers(self) -> Dict[str, str]:
        headers = {
            "authorization": f"Bearer {self.token}",
            "accept": "application/json",
            "user-agent": "Mozilla/5.0 (Linux; Android 10; SM-G970F)",
        }
        if self.t:
            headers["t"] = self.t
        return headers

    def _client(self) -> httpx.Client:
        return httpx.Client(base_url=self.base_url, headers=self._headers(), timeout=self.timeout)

    def get_me(self) -> Dict[str, Any]:
        with self._client() as c:
            r = c.get("/users/me")
            r.raise_for_status()
            return r.json().get("data", {})

    def list_instagram_accounts(self) -> List[Dict[str, Any]]:
        with self._client() as c:
            r = c.get("/instagram-account")
            r.raise_for_status()
            return r.json().get("data", [])
