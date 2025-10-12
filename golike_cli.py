#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from golike_client import (
    AUTH_FILE,
    Auth,
    GoLikeClient,
    delete_auth,
    load_auth,
    save_auth,
)


def cmd_login(args: argparse.Namespace) -> int:
    token = (args.token or "").strip()
    t_val = (args.t or "").strip()

    if not token:
        token = input("👉 Nhập Authorization (Bearer ... hoặc chỉ token): ").strip()
    if token.lower().startswith("bearer "):
        token = token[len("bearer ") :].strip()

    if not t_val:
        t_val = input("👉 Nhập T (bắt buộc): ").strip()

    if not token or not t_val:
        print("❌ Authorization hoặc T bị trống.")
        return 2

    client = GoLikeClient(token=token, t=t_val, device=args.device)
    me = client.get_me()
    if not me:
        print("❌ Đăng nhập thất bại. Vui lòng kiểm tra Authorization/T.")
        return 3

    save_auth(token, t_val, AUTH_FILE)
    print("✅ Đăng nhập thành công và đã lưu vào auth.json")
    print(f"👤 ID: {me.get('id')} | Tên: {me.get('name')} | Xu: {me.get('coin')}")
    return 0


def _ensure_auth(args: argparse.Namespace) -> Optional[Auth]:
    if args.token and args.t:
        return Auth(token=args.token.strip().replace("Bearer ", ""), t=args.t.strip())
    auth = load_auth(AUTH_FILE)
    if not auth:
        print("❌ Chưa đăng nhập. Hãy chạy: python golike_cli.py login")
        return None
    return auth


def cmd_me(args: argparse.Namespace) -> int:
    auth = _ensure_auth(args)
    if not auth:
        return 2
    client = GoLikeClient(token=auth.token, t=auth.t, device=args.device)
    me = client.get_me()
    if not me:
        print("❌ Không lấy được thông tin người dùng.")
        return 3
    print(json.dumps(me, ensure_ascii=False, indent=2))
    return 0


def cmd_ig_accounts(args: argparse.Namespace) -> int:
    auth = _ensure_auth(args)
    if not auth:
        return 2
    client = GoLikeClient(token=auth.token, t=auth.t, device=args.device)
    accounts = client.get_instagram_accounts()
    if not accounts:
        print("⚠️ Chưa có Instagram nào được liên kết.")
        return 0
    for idx, acc in enumerate(accounts, start=1):
        print(f"{idx}. ID={acc.get('id')} | User={acc.get('instagram_username')}")
    return 0


def cmd_run_ig(args: argparse.Namespace) -> int:
    auth = _ensure_auth(args)
    if not auth:
        return 2
    client = GoLikeClient(token=auth.token, t=auth.t, device=args.device)
    accounts = client.get_instagram_accounts()
    if not accounts:
        print("⚠️ Không có Instagram để chạy job.")
        return 0

    print(f"➡ Bắt đầu chạy job giả lập cho {len(accounts)} tài khoản...")
    for acc in accounts:
        uname = acc.get("instagram_username")
        acc_id = acc.get("id")
        print(f"  • Lấy job cho {uname} (ID: {acc_id})... ✅ (placeholder)")
    print("✅ Hoàn tất (demo)")
    return 0


def cmd_logout(_: argparse.Namespace) -> int:
    if delete_auth(AUTH_FILE):
        print("✅ Đã xoá thông tin đăng nhập.")
        return 0
    print("⚠️ Không tìm thấy hoặc không xoá được auth.json.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="golike",
        description="CLI tương tác với GoLike (đăng nhập, xem thông tin, tài khoản IG, chạy job giả lập)",
    )
    parser.add_argument("--device", choices=["android", "ios"], default="android", help="Thiết bị giả lập cho User-Agent")
    parser.add_argument("--token", help="Authorization token (tuỳ chọn, nếu không có sẽ dùng auth.json)")
    parser.add_argument("--t", help="Giá trị T (tuỳ chọn, nếu không có sẽ dùng auth.json)")

    sub = parser.add_subparsers(dest="command", required=True)

    p_login = sub.add_parser("login", help="Đăng nhập và lưu auth")
    p_login.add_argument("--token", help="Authorization token (có thể nhập sau)")
    p_login.add_argument("--t", help="Giá trị T (có thể nhập sau)")
    p_login.set_defaults(func=cmd_login)

    p_me = sub.add_parser("me", help="Xem thông tin người dùng")
    p_me.set_defaults(func=cmd_me)

    p_ig = sub.add_parser("ig-accounts", help="Liệt kê tài khoản Instagram đã liên kết")
    p_ig.set_defaults(func=cmd_ig_accounts)

    p_run_ig = sub.add_parser("run-ig", help="Chạy job giả lập cho Instagram (demo)")
    p_run_ig.set_defaults(func=cmd_run_ig)

    p_logout = sub.add_parser("logout", help="Xoá đăng nhập (xoá auth.json)")
    p_logout.set_defaults(func=cmd_logout)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
