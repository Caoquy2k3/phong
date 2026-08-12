#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests

BASE_URL = "https://gateway.golike.net"
AUTH_FILE = "auth.json"


@dataclass(frozen=True)
class Auth:
    token: str
    t: str


def save_auth(token: str, t: str, auth_path: str = AUTH_FILE) -> None:
    data = {"token": token.strip().replace("Bearer ", ""), "t": t.strip()}
    with open(auth_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_auth(auth_path: str = AUTH_FILE) -> Optional[Auth]:
    if not os.path.exists(auth_path):
        return None
    try:
        with open(auth_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        token = (data.get("token") or "").strip().replace("Bearer ", "")
        t_val = (data.get("t") or "").strip()
        if token and t_val:
            return Auth(token=token, t=t_val)
    except Exception:
        return None
    return None


def delete_auth(auth_path: str = AUTH_FILE) -> bool:
    try:
        if os.path.exists(auth_path):
            os.remove(auth_path)
            return True
    except Exception:
        return False
    return False


def _build_headers(token: str, t: str, device: str = "android") -> Dict[str, str]:
    if device == "ios":
        user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)"
    else:
        user_agent = "Mozilla/5.0 (Linux; Android 10; SM-G970F)"

    headers = {
        "authorization": f"Bearer {token}",
        "user-agent": user_agent,
        "accept": "application/json",
    }
    if t:
        headers["t"] = t
    return headers


class GoLikeClient:
    def __init__(self, token: str, t: str, device: str = "android", timeout_s: int = 15) -> None:
        self._headers = _build_headers(token=token, t=t, device=device)
        self._timeout_s = timeout_s

    def _request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        url = f"{BASE_URL}{path}"
        try:
            resp = requests.request(method=method, url=url, headers=self._headers, timeout=self._timeout_s, **kwargs)
            resp.raise_for_status()
            try:
                return resp.json()
            except ValueError:
                return {"error": "invalid_json", "text": resp.text}
        except requests.RequestException as exc:
            return {"error": "request_failed", "detail": str(exc)}

    def get_me(self) -> Dict[str, Any]:
        res = self._request("GET", "/api/users/me")
        return res.get("data", {}) if isinstance(res, dict) else {}

    def get_instagram_accounts(self) -> List[Dict[str, Any]]:
        res = self._request("GET", "/api/instagram-account")
        return res.get("data", []) if isinstance(res, dict) else []

    # Placeholder for future actions
    # def get_jobs(self, ...):
    #     pass
