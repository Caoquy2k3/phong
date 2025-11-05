from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


DEFAULT_DATA_DIR = Path(os.environ.get("GOLIKE_DATA_DIR", Path.home() / ".golike"))
DEFAULT_DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_CONFIG_PATH = DEFAULT_DATA_DIR / "config.yaml"
DEFAULT_STORAGE_STATE = DEFAULT_DATA_DIR / "storage_state.json"
DEFAULT_COOKIES_PATH = DEFAULT_DATA_DIR / "cookies.json"


class LoginConfig(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    login_url: str = Field(
        default="https://app.golike.net/",
        description="Landing/login URL for GoLike app.",
    )
    two_factor: bool = False


class AppConfig(BaseModel):
    headless: bool = True
    slow_mo_ms: int = 0
    user_agent: Optional[str] = None
    viewport_width: int = 1280
    viewport_height: int = 800
    timeout_ms: int = 30000


class Config(BaseModel):
    login: LoginConfig = Field(default_factory=LoginConfig)
    app: AppConfig = Field(default_factory=AppConfig)
    # GoLike API auth and endpoint
    class AuthConfig(BaseModel):
        token: Optional[str] = None
        t: Optional[str] = None
        base_api_url: str = "https://gateway.golike.net/api"

    auth: AuthConfig = Field(default_factory=AuthConfig)
    storage_state: Path = Field(default=DEFAULT_STORAGE_STATE)
    cookies_path: Path = Field(default=DEFAULT_COOKIES_PATH)

    @staticmethod
    def load(path: Optional[Path] = None) -> "Config":
        cfg_path = path or DEFAULT_CONFIG_PATH
        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {}

        # env overrides
        env_headless = os.environ.get("GOLIKE_HEADLESS")
        if env_headless is not None:
            data.setdefault("app", {})["headless"] = env_headless.lower() in ("1", "true", "yes")
        env_user = os.environ.get("GOLIKE_USERNAME")
        if env_user:
            data.setdefault("login", {})["username"] = env_user
        env_pass = os.environ.get("GOLIKE_PASSWORD")
        if env_pass:
            data.setdefault("login", {})["password"] = env_pass

        # API auth overrides
        env_token = os.environ.get("GOLIKE_TOKEN")
        if env_token:
            data.setdefault("auth", {})["token"] = env_token
        env_t = os.environ.get("GOLIKE_T")
        if env_t:
            data.setdefault("auth", {})["t"] = env_t

        cfg = Config.model_validate(data)
        # normalize paths
        cfg.storage_state = Path(cfg.storage_state)
        cfg.cookies_path = Path(cfg.cookies_path)
        cfg.storage_state.parent.mkdir(parents=True, exist_ok=True)
        cfg.cookies_path.parent.mkdir(parents=True, exist_ok=True)
        return cfg

    def save(self, path: Optional[Path] = None) -> None:
        cfg_path = path or DEFAULT_CONFIG_PATH
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        data = yaml.safe_dump(self.model_dump(mode="python"), allow_unicode=True, sort_keys=False)
        with open(cfg_path, "w", encoding="utf-8") as f:
            f.write(data)
