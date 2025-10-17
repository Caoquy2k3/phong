#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import telebot
import time
import logging

# ==== 🔧 CẤU HÌNH BOT TELEGRAM ====
TOKEN = "8079740034:AAHVX9gX-Iyyy-xlaVxtQx2BbYHseaOyuZU"  # ⚠️ Thay bằng token thật
bot = telebot.TeleBot(TOKEN)

# ==== 🌍 DANH SÁCH API MAIL HỖ TRỢ ====
API_CANDIDATES = [
    "https://api.mail.tm",
    "https://api.mail.gw",
    "https://api.mail.gw.dev",
    "https://api.mail.tm/api",
]

WORKING_API = None
USER_ACCOUNTS = {}  # Lưu email, password, token theo user Telegram: {chat_id: {"email":..., "password":..., "token":...}}

# ==== 🧠 TÌM API HOẠT ĐỘNG ====
def detect_working_api():
    global WORKING_API
    print("🔍 Đang dò API mail hoạt động...")
    for base in API_CANDIDATES:
        try:
            url = base.rstrip("/") + "/domains"
            r = requests.get(url, timeout=15)
            print(f"Thử {url} → {r.status_code}")
            if r.status_code == 200 and ("domain" in r.text or "hydra:member" in r.text):
                WORKING_API = base.rstrip("/")
                print("✅ API hoạt động:", WORKING_API)
                return WORKING_API
        except Exception as e:
            print("❌ Lỗi với", base, "=>", e)
    WORKING_API = None
    print("🚫 Không tìm thấy API mail hoạt động!")
    return None

# ==== 🔐 TẠO EMAIL MỚI ====
def create_account():
    if not WORKING_API:
        detect_working_api()
        if not WORKING_API:
            return {"error": "Không thể kết nối với API nào."}

    try:
        # Lấy domain
        res = requests.get(f"{WORKING_API}/domains", timeout=15)
        res.raise_for_status()
        data = res.json()
        # mail APIs thường trả hydra:member list or plain list
        if isinstance(data, dict) and "hydra:member" in data:
            domains = data["hydra:member"]
        elif isinstance(data, list):
            domains = data
        else:
            domains = []

        if not domains:
            # fallback domain
            domain = "mail.tm"
        else:
            domain = domains[0].get("domain") if isinstance(domains[0], dict) else domains[0]

        email = f"user{int(time.time())}@{domain}"
        password = "12345678"

        # Tạo tài khoản
        acc_resp = requests.post(f"{WORKING_API}/accounts", json={"address": email, "password": password}, timeout=20)
        # Một số API trả 201 (created), một số 200
        if acc_resp.status_code not in (200, 201):
            # Có thể tài khoản đã tồn tại — tiếp tục thử lấy token
            logging.warning("Tạo account trả code %s: %s", acc_resp.status_code, acc_resp.text)

        # Lấy token (login)
        token_resp = requests.post(f"{WORKING_API}/token", json={"address": email, "password": password}, timeout=20)
        if token_resp.status_code != 200:
            return {"error": f"Lỗi lấy token ({token_resp.status_code}): {token_resp.text}"}
        token = token_resp.json().get("token")
        if not token:
            return {"error": "Không lấy được token từ API."}

        return {"email": email, "password": password, "token": token}

    except Exception as e:
        return {"error": f"Lỗi khi tạo account: {e}"}

# ==== 📬 LẤY DANH SÁCH MAIL ====
def get_inbox(token, page=1):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{WORKING_API}/messages"
        params = {"page": page}
        r = requests.get(url, headers=headers, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        mails = data.get("hydra:member", []) if isinstance(data, dict) else data
        return mails
    except Exception as e:
        return {"error": f"Lỗi khi lấy hộp thư: {e}"}

# ==== 🔍 ĐỌC NỘI DUNG MAIL (OTP) ====
def read_mail(token, msg_id):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{WORKING_API}/messages/{msg_id}", headers=headers, timeout=20)
        r.raise_for_status()
        data = r.json()
        # Các trường thường có: from, to, subject, text, html, intro, createdAt
        subject = data.get("subject") or "(không tiêu đề)"
        from_addr = data.get("from", {}).get("address") if isinstance(data.get("from"), dict) else data.get("from")
        created = data.get("createdAt", "")
        # Prefer text, then html, then intro
        body = data.get("text") or data.get("intro") or data.get("html") or "(Không có nội dung)"
        # Nếu body là HTML, bạn có thể strip tags hoặc gửi thẳng (Telegram hỗ trợ HTML only with parse_mode)
        # Truncate long bodies
        if isinstance(body, str) and len(body) > 3500:
            body = body[:3500] + "\n\n[...truncated]"
        return {"subject": subject, "from": from_addr, "date": created, "body": body}
    except Exception as e:
        return {"error": f"Lỗi khi đọc mail: {e}"}

# ==== 🗑️ XÓA MAIL ====
def delete_mail(token, msg_id):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.delete(f"{WORKING_API}/messages/{msg_id}", headers=headers, timeout=20)
        if r.status_code in (200, 204):
            return {"ok": True}
        return {"error": f"Không thể xóa ({r.status_code}): {r.text}"}
    except Exception as e:
        return {"error": f"Lỗi khi xóa mail: {e}"}

# ==== 🔹 LỆNH TELEGRAM ====
@bot.message_handler(commands=['start'])
def cmd_start(message):
    txt = (
        "Xin chào! Bot email tạm thời.\n\n"
        "Lệnh:\n"
        "/new - Tạo tài khoản mail mới\n"
        "/inbox - Liệt kê email (mới nhất)\n"
        "/read <id> - Đọc email chi tiết\n"
        "/delete <id> - Xóa email\n"
        "/me - Thông tin account hiện tại\n"
        "/api - Hiện API đang dùng\n"
    )
    bot.reply_to(message, txt)

@bot.message_handler(commands=['api'])
def cmd_api(message):
    bot.reply_to(message, f"API hiện dùng: {WORKING_API or 'Chưa kết nối'}")

@bot.message_handler(commands=['new'])
def cmd_new(message):
    chat_id = message.chat.id
    bot.reply_to(message, "Đang tạo account, vui lòng chờ...")
    res = create_account()
    if isinstance(res, dict) and res.get("error"):
        bot.reply_to(message, f"❌ {res['error']}")
        return
    if not isinstance(res, dict):
        bot.reply_to(message, "❌ Lỗi không xác định khi tạo account.")
        return
    # store
    USER_ACCOUNTS[chat_id] = res
    bot.reply_to(message, f"✅ Đã tạo account!\nEmail: {res['email']}\nMật khẩu: {res['password']}\n(Use /inbox để kiểm tra mail)")

@bot.message_handler(commands=['me'])
def cmd_me(message):
    acc = USER_ACCOUNTS.get(message.chat.id)
    if not acc:
        bot.reply_to(message, "Bạn chưa có account. Gõ /new để tạo.")
        return
    bot.reply_to(message, f"Email: {acc['email']}\nPassword: {acc['password']}\nToken: {acc['token'][:24]}...")

@bot.message_handler(commands=['inbox'])
def cmd_inbox(message):
    acc = USER_ACCOUNTS.get(message.chat.id)
    if not acc:
        bot.reply_to(message, "Bạn chưa có account. Gõ /new để tạo.")
        return
    bot.reply_to(message, "Đang lấy hộp thư...")
    mails = get_inbox(acc['token'], page=1)
    if isinstance(mails, dict) and mails.get("error"):
        bot.reply_to(message, mails["error"])
        return
    if not mails:
        bot.reply_to(message, "📭 Hộp thư trống.")
        return
    # Build message list (limit to 10)
    lines = []
    for m in mails[:10]:
        mid = m.get("id")
        subj = m.get("subject") or "(không tiêu đề)"
        frm = m.get("from", {}).get("address") if isinstance(m.get("from"), dict) else m.get("from")
        created = m.get("createdAt", "")
        lines.append(f"ID: `{mid}`\nFrom: {frm}\nSubject: {subj}\nDate: {created}\n---")
    bot.reply_to(message, "\n".join(lines))

@bot.message_handler(commands=['read'])
def cmd_read(message):
    acc = USER_ACCOUNTS.get(message.chat.id)
    if not acc:
        bot.reply_to(message, "Bạn chưa có account. Gõ /new để tạo.")
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Dùng: /read <message_id>")
        return
    mid = parts[1].strip()
    bot.reply_to(message, f"Đang đọc mail {mid} ...")
    res = read_mail(acc['token'], mid)
    if isinstance(res, dict) and res.get("error"):
        bot.reply_to(message, res["error"])
        return
    # send body (plain text). If body contains HTML it's sent raw.
    out = f"Subject: {res['subject']}\nFrom: {res['from']}\nDate: {res['date']}\n\n{res['body']}"
    # Telegram has message length limits; split if needed
    if len(out) <= 4000:
        bot.reply_to(message, out)
    else:
        # split into chunks
        for i in range(0, len(out), 3500):
            bot.reply_to(message, out[i:i+3500])

@bot.message_handler(commands=['delete'])
def cmd_delete(message):
    acc = USER_ACCOUNTS.get(message.chat.id)
    if not acc:
        bot.reply_to(message, "Bạn chưa có account. Gõ /new để tạo.")
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Dùng: /delete <message_id>")
        return
    mid = parts[1].strip()
    res = delete_mail(acc['token'], mid)
    if isinstance(res, dict) and res.get("error"):
        bot.reply_to(message, res["error"])
    else:
        bot.reply_to(message, f"🗑️ Đã xóa message {mid}")

@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.reply_to(message, "Không rõ lệnh. Gõ /start để xem các lệnh.")

# ==== 🚀 CHẠY BOT ====
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("🤖 Bot Telegram đang chạy...")
    detect_working_api()
    # Nếu muốn auto-detect liên tục, có thể gọi detect_working_api() định kỳ (không bắt buộc)
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            logging.exception("Polling lỗi, retry sau 5s: %s", e)
            time.sleep(5)