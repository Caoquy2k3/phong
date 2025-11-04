# toolgop_uiautomator2.py
import json
import os, time
import cloudscraper
import requests
import socket
import subprocess
import re
from time import sleep
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from rich.text import Text

# NEW: uiautomator2
try:
    import uiautomator2 as u2
except Exception:
    u2 = None

# --- CẤU HÌNH FILES ---
AUTH_FILE = "golike_auth.json"
ADB_DEVICES_FILE = "adb_devices.json"
# removed coordinate files usage - no coordinates anymore
TELEGRAM_CHAT_ID_FILE = "telegram_chat_id.txt"

# --- DỌN DẸP --- (xóa file chat id cũ nếu có)
if os.path.exists(TELEGRAM_CHAT_ID_FILE):
    try:
        os.remove(TELEGRAM_CHAT_ID_FILE)
        print(f"[Đã xoá file {TELEGRAM_CHAT_ID_FILE} để đảm bảo không lưu Chat ID.]")
    except Exception as e:
        print(f"[Cảnh báo: Không thể xoá file {TELEGRAM_CHAT_ID_FILE}: {e}]")

console = Console()

# --- CẤU HÌNH CHỦ TOOL (bạn) ---
TOOL_OWNER_BOT_TOKEN = "8230870404:AAGri9A07HH-6nOA91j-kCnuFUW-SEEU64U"  # giữ nguyên (nếu có)

# --- HÀM TELEGRAM ---
def send_telegram_message(message, chat_id, bot_token):
    if not bot_token or bot_token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        return False
    if not chat_id:
        return False
    chat_id = str(chat_id).strip()
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {'chat_id': chat_id, 'text': message, 'parse_mode': 'Markdown'}
        response = requests.post(url, data=payload, timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def get_telegram_updates(bot_token):
    if bot_token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        return []
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        params = {'limit': 5, 'offset': -5}
        response = requests.get(url, params=params, timeout=5).json()
        return response.get('result', [])
    except Exception:
        return []

# --- KIỂM TRA MẠNG ---
def kiem_tra_mang():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
    except OSError:
        rprint(Panel("[bold red]Mạng không ổn định hoặc bị mất kết nối. Vui lòng kiểm tra lại mạng.[/bold red]", border_style="red"))

kiem_tra_mang()

# Banner
ascii_art = """
░█▀▀░█▀█░░░▀█▀░▀█▀░█░█░░░▀█▀░█▀█░█░█
░█░█░█░█░░░░█░░░█░░█▀▄░░░░█░░█░█░█▀▄
░▀▀▀░▀▀▀░░░░▀░░▀▀▀░▀░▀░░░░▀░░▀▀▀░▀░▀
"""
centered_text = Text(ascii_art, justify="center", style="bold blue")
info_text = Text.from_markup("\n" + "[bold yellow]Auto Golike Tiktok Tool[/bold yellow]\n" + "[bold yellow]Phiên Bản: V2.3 (uiautomator2)[/bold yellow]", justify="center")
banner = Panel(Text.assemble(centered_text, info_text), title="[bold blue]AUTO TIKTOK TOOL[/bold blue]", border_style="blue")

def tao_panel_trang_thai_live(dem, tong, nickname, bot_token, chat_id):
    tele_status = "❌ OFF"
    tele_style = "bold red"
    if bot_token and bot_token != "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        if chat_id:
            chat_id_display = f"{chat_id[:8]}...{chat_id[-3:]}" if len(chat_id) > 11 else chat_id
            tele_status = f"✅ ON ({chat_id_display})"
            tele_style = "bold green"
        else:
            tele_status = "⚠️ BOT OK, CHAT ID CHƯA CÓ"
            tele_style = "bold yellow"

    status_text = Text.assemble(
        Text.from_markup(f"[bold white]NICK ĐANG LÀM:[/bold white] [bold cyan]{nickname}[/bold cyan]"),
        Text.from_markup("\n"),
        Text.from_markup(f"[bold green]JOB ĐÃ LÀM:[/bold green] [bold yellow]{dem:,.0f}[/bold yellow]"),
        Text.from_markup(" | "),
        Text.from_markup(f"[bold green]TỔNG XU:[/bold green] [bold yellow]{tong:,.0f} VNĐ[/bold yellow]"),
        Text.from_markup("\n"),
        Text.from_markup("[bold white]BOT TELEGRAM:[/bold white] "),
        Text.from_markup(tele_status, style=tele_style)
    )

    return Panel(status_text, title="[bold cyan]LIVE STATUS[/bold cyan]", border_style="magenta", width=60)

def hien_thi_man_hinh(dem, tong, nickname, bot_token, chat_id):
    os.system('cls' if os.name== 'nt' else 'clear')
    console.print(banner)
    console.print(tao_panel_trang_thai_live(dem, tong, nickname, bot_token, chat_id))

os.system('cls' if os.name== 'nt' else 'clear')
console.print(banner)

# --- QUẢN LÝ AUTH GOLIKE ---
def load_save_credentials():
    auth_data = {}
    try:
        with open(AUTH_FILE, 'r') as f:
            auth_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    author = auth_data.get('Authorization', '')
    token = auth_data.get('T', '')

    rprint(Panel("[bold cyan]ĐĂNG NHẬP GOLIKE AUTH[/bold cyan]", border_style="yellow"))

    if author and token:
        rprint(f"[bold green]Đã tìm thấy thông tin đăng nhập đã lưu.[/bold green]")
        rprint(f"[bold green]Nhập 1 để vào TOOL Golike TikTok [/bold green]")
        rprint(f"[bold blue]     HOẶC LÀ[/bold blue]")
        select = console.input(f"[bold green]Nhập AUTHORIZATION khác : [/bold green][bold yellow]")
        if select != "1":
            author = select
            token = console.input("[bold green]🚀 Nhập T : [/bold green][bold yellow]")
    else:
        author = console.input("[bold green] 💸 NHẬP AUTHORIZATION GOLIKE : [/bold green][bold yellow]")
        token = console.input("[bold green]💸  NHẬP TOKEN (T CỦA GOLIKE): [/bold green][bold yellow]")

    with open(AUTH_FILE, 'w') as f:
        json.dump({'Authorization': author, 'T': token}, f, indent=4)

    return author, token

author, token = load_save_credentials()

headers = {
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json;charset=utf-8',
    'Authorization': author,
    't': token,
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
    'Referer': 'https://app.golike.net/account/manager/tiktok',
}
scraper = cloudscraper.create_scraper()
os.system('cls' if os.name== 'nt' else 'clear')
console.print(banner)

# --- HÀM GOLIKE (giữ nguyên) ---
def chonacc():
    try:
        response = scraper.get('https://gateway.golike.net/api/tiktok-account', headers=headers, json={}).json()
        return response
    except Exception:
        return {"status": 500}

def nhannv(account_id):
    try:
        params = {'account_id': account_id, 'data': 'null'}
        response = scraper.get('https://gateway.golike.net/api/advertising/publishers/tiktok/jobs', headers=headers, params=params, json={})
        return response.json()
    except Exception:
        return {"status": 500, "message": "Lỗi kết nối"}

def hoanthanh(ads_id, account_id):
    try:
        json_data = {'ads_id': ads_id, 'account_id': account_id, 'async': True, 'data': None}
        response = scraper.post('https://gateway.golike.net/api/advertising/publishers/tiktok/complete-jobs', headers=headers, json=json_data, timeout=6)
        return response.json()
    except Exception:
        return {"status": 500}

def baoloi(ads_id, object_id, account_id, loai):
    try:
        json_data1 = {
            'description': 'Tôi đã làm Job này rồi',
            'users_advertising_id': ads_id,
            'type': 'ads',
            'provider': 'tiktok',
            'fb_id': account_id,
            'error_type': 6,
        }
        scraper.post('https://gateway.golike.net/api/report/send', headers=headers, json=json_data1)
        json_data2 = {'ads_id': ads_id, 'object_id': object_id, 'account_id': account_id, 'type': loai}
        scraper.post('https://gateway.golike.net/api/advertising/publishers/tiktok/skip-jobs', headers=headers, json=json_data2)
    except Exception:
        pass

chontktiktok = chonacc()

def dsacc():
    if chontktiktok.get("status") != 200:
        rprint(Panel("[bold red] Authorization hoặc T sai. Vui lòng kiểm tra lại.[/bold red]", border_style="red"))
        quit()
    table = Table(title="[bold magenta]DANH SÁCH ACC TIKTOK TRONG ACC GOLIKE[/bold magenta]", header_style="bold cyan", border_style="green")
    table.add_column("STT", style="bold green", justify="center")
    table.add_column("Nickname", style="bold yellow")
    table.add_column("Trạng thái", style="bold red", justify="center")
    for i in range(len(chontktiktok["data"])):
        nickname = chontktiktok["data"][i]["nickname"]
        stt = str(i + 1)
        trang_thai = "[bold green]✅ Online[/bold green]"
        table.add_row(stt, nickname, trang_thai)
    console.print(table)

# --- Khởi tạo giao diện & chọn acc ---
os.system('cls' if os.name== 'nt' else 'clear')
console.print(banner)
dsacc()
rprint(f"[bold magenta]═══════════════════════════════════[/bold magenta]")

# Lựa chọn tài khoản
while True:
    try:
        rprint(Panel("[bold red] Chọn tài khoản TIKTOK bạn muốn chạy : [/bold red]", border_style="yellow"))
        luachon_str = console.input("[bold yellow]Nhập số thứ tự:[/bold yellow] ")
        if not luachon_str.isdigit():
            raise ValueError
        luachon = int(luachon_str)
        if luachon < 1 or luachon > len(chontktiktok["data"]):
            rprint(Panel(f"[bold red] Acc Này Không Có Trong Danh Sách Cấu Hình ({len(chontktiktok['data'])} tài khoản). Vui lòng nhập lại.[/bold red]", border_style="red"))
            continue
        account_id = chontktiktok["data"][luachon - 1]["id"]
        nickname_hien_tai = chontktiktok["data"][luachon - 1]["nickname"]
        break
    except ValueError:
        rprint(Panel("[bold red] Sai Định Dạng. Vui lòng nhập số! [/bold red]", border_style="red"))

# Delay
while True:
    try:
        rprint(Panel(f"[bold green]  Delay thực hiện job : [/bold green][bold yellow]", border_style="yellow"))
        delay = int(console.input("[bold yellow]Nhập số giây delay:[/bold yellow] "))
        break
    except ValueError:
        rprint(Panel("[bold red] Sai Định Dạng. Vui lòng nhập số! [/bold red]", border_style="red"))

# Thất bại bao nhiêu lần đổi acc
while True:
    try:
        rprint(Panel(f"[bold green]  Thất bại bao nhiêu lần thì đổi acc tiktok  : [/bold green]", border_style="yellow"))
        doiacc = int(console.input("[bold yellow]Nhập số lần thất bại:[/bold yellow] "))
        break
    except ValueError:
        rprint(Panel("[bold red]🚀 Nhập Vào 1 Số 🚀[/bold red]", border_style="red"))

# Chọn loại nv
rprint(Panel("[bold yellow]CHỌN NV[/bold yellow]", border_style="cyan"))
rprint("[bold green][1] NV Follow[/bold green]")
rprint("[bold green][2] NV Like[/bold green]")
rprint("[bold green][3] Cả hai NV (Follow và Like)[/bold green]")

while True:
    try:
        rprint(Panel("[bold green]🔫 Chọn loại nv : [/bold green][bold yellow]", border_style="yellow"))
        loai_nhiem_vu = int(console.input("[bold yellow]Nhập lựa chọn (1/2/3):[/bold yellow] "))
        if loai_nhiem_vu in [1, 2, 3]:
            break
        else:
            rprint(Panel("[bold red]Vui lòng chọn số từ 1 đến 3![/bold red]", border_style="red"))
    except ValueError:
        rprint(Panel("[bold red]Sai định dạng! Vui lòng nhập số.[/bold red]", border_style="red"))

# --- TELEGRAM CONFIG (session-only) ---
TELEGRAM_CHAT_ID = None
rprint(Panel("[bold yellow]CẤU HÌNH THÔNG BÁO TELEGRAM (KHÔNG LƯU ID CHAT)[/bold yellow]", border_style="cyan"))

if TOOL_OWNER_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE" or not TOOL_OWNER_BOT_TOKEN:
    rprint(Panel("[bold red]❌ Chủ tool chưa cấu hình Bot Token. Tính năng Telegram bị vô hiệu hóa.[/bold red]", border_style="red"))
else:
    rprint("[bold green]Bạn có muốn nhận thông báo Telegram không? (Y/N)[/bold green]")
    enable_tele = console.input("[bold yellow]Nhập Y hoặc N:[/bold yellow] ").strip().upper()
    if enable_tele == 'Y':
        rprint(Panel(f"[bold blue]THIẾT LẬP CHAT ID (CHỈ DÙNG TRONG PHIÊN NÀY):[/bold blue] 1. Nhắn tin bất kỳ cho Bot Telegram của bạn. 2. Chọn 1 trong 3 tùy chọn bên dưới.", border_style="blue"))
        while True:
            rprint("[bold green]Tùy chọn:[/bold green]")
            rprint("[bold yellow][Nhập ID][/bold yellow] Nhập Chat ID thủ công.")
            rprint("[bold yellow][1][/bold yellow] Tìm Chat ID tự động.")
            rprint("[bold yellow][Enter][/bold yellow] Bỏ qua (vô hiệu hóa Telegram cho phiên này).")
            action = console.input("[bold green]Chọn (ID/1/Enter):[/bold green] [bold yellow]").strip()
            if action == '1':
                updates = get_telegram_updates(TOOL_OWNER_BOT_TOKEN)
                found_ids = set()
                for update in updates:
                    if 'message' in update and 'chat' in update['message']:
                        chat_id = str(update['message']['chat']['id'])
                        found_ids.add(chat_id)
                if found_ids:
                    rprint(Panel("[bold green]✅ Đã tìm thấy các CHAT ID tiềm năng:[/bold green]", border_style="green"))
                    id_list = list(found_ids)
                    for idx, id_found in enumerate(id_list):
                        rprint(f"[bold yellow][{idx+1}][/bold yellow] ID: [bold cyan]{id_found}[/bold cyan]")
                    rprint("[bold green]Vui lòng nhập ID chính xác của bạn (hoặc số thứ tự):[/bold green]")
                    id_choice = console.input("[bold yellow]Nhập ID hoặc STT: [/bold yellow]").strip()
                    final_id = None
                    if id_choice.isdigit():
                        try:
                            index = int(id_choice) - 1
                            if 0 <= index < len(id_list):
                                final_id = id_list[index]
                        except:
                            pass
                    if final_id or (id_choice.lstrip('-').isdigit() or (id_choice.startswith('-') and id_choice[1:].isdigit())):
                        TELEGRAM_CHAT_ID = final_id or id_choice
                        break
                    rprint("[bold red]Không tìm thấy ID bạn nhập trong danh sách hoặc nhập sai. Vui lòng thử lại.[/bold red]")
                else:
                    rprint(Panel("[bold red]❌ Không tìm thấy tin nhắn mới nào. Đảm bảo bạn đã nhắn tin cho Bot và Bot Token là chính xác.[/bold red]", border_style="red"))
            elif action.lstrip('-').isdigit() or (action.startswith('-') and action[1:].isdigit()):
                TELEGRAM_CHAT_ID = action
                break
            elif not action:
                rprint(Panel("[bold red]❌ Bạn đã bỏ qua nhập Chat ID. Tính năng Telegram bị vô hiệu hóa.[/bold red]", border_style="red"))
                TELEGRAM_CHAT_ID = None
                break
            else:
                rprint("[bold red]Nhập không hợp lệ. Vui lòng nhập ID (số), '1', hoặc Enter.[/bold red]")

        if TELEGRAM_CHAT_ID:
            test_msg = "*✅ Cấu hình Telegram thành công!* Bạn sẽ nhận được thông báo Job tại đây. *ID này KHÔNG được lưu lại và sẽ phải nhập lại trong lần chạy sau.*"
            if send_telegram_message(test_msg, TELEGRAM_CHAT_ID, TOOL_OWNER_BOT_TOKEN):
                rprint(Panel(f"[bold green]✅ Gửi tin nhắn TEST thành công! Chat ID: {TELEGRAM_CHAT_ID}[/bold green]", border_style="green"))
            else:
                rprint(Panel(f"[bold red]❌ Lỗi gửi tin nhắn TEST. Chat ID có thể sai hoặc Bot Token không hợp lệ. Tính năng bị vô hiệu hóa.[/bold red]", border_style="red"))
                TELEGRAM_CHAT_ID = None
    else:
        rprint(Panel("[bold yellow]Tính năng Telegram bị vô hiệu hóa.[/bold yellow]", border_style="yellow"))

# ----------------- QUẢN LÝ THIẾT BỊ ADB -----------------
def get_adb_prop(device_id, prop_name):
    try:
        result = subprocess.run(f"adb -s {device_id} shell getprop {prop_name}", shell=True, capture_output=True, text=True, timeout=3)
        return result.stdout.strip()
    except Exception:
        return "N/A"

def load_adb_metadata():
    try:
        with open(ADB_DEVICES_FILE, 'r') as f:
            data = json.load(f)
            return {dev['id']: dev for dev in data}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_adb_devices(devices_dict):
    with open(ADB_DEVICES_FILE, 'w') as f:
        json.dump(list(devices_dict.values()), f, indent=4)

def scan_and_get_all_devices():
    saved_metadata = load_adb_metadata()
    active_devices_list = []
    try:
        adb_output = os.popen("adb devices").read().strip().split('\n')
        device_ids = []
        for line in adb_output[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == 'device':
                device_ids.append(parts[0])
        for device_id in device_ids:
            dev_info = saved_metadata.get(device_id)
            if not dev_info or dev_info.get("model") == "N/A" or dev_info.get("android_version") == "N/A":
                console.print(f"[bold yellow]→ Đang quét chi tiết cho thiết bị mới: {device_id}...[/bold yellow]")
                device_model = get_adb_prop(device_id, "ro.product.model")
                android_version_raw = get_adb_prop(device_id, "ro.build.version.release")
                android_version = f"Android {android_version_raw}" if android_version_raw not in ["", "N/A"] else "N/A"
                dev_info = {"name": device_model, "id": device_id, "model": device_model, "android_version": android_version, "last_account": saved_metadata.get(device_id, {}).get("last_account", "No Info")}
                saved_metadata[device_id] = dev_info
            active_devices_list.append(dev_info)
    except Exception as e:
        console.print(f"[bold red]Lỗi khi quét ADB devices: {e}[/bold red]")
    save_adb_devices(saved_metadata)
    return active_devices_list

def list_adb_devices(devices):
    rprint(Panel(Text("Danh sách thiết bị ADB đang kết nối", justify="center"), border_style="blue"))
    table = Table(header_style="bold magenta", border_style="cyan")
    table.add_column("STT", style="bold green", justify="center")
    table.add_column("ID DEVICES", style="bold cyan")
    table.add_column("DEVICE MODEL", style="bold yellow")
    table.add_column("ANDROID VERSION", style="bold green")
    table.add_column("LAST ACCOUNT", style="bold white")
    if not devices:
        table.add_row(Text("Không có thiết bị ADB nào đang kết nối (device)", justify="center", style="red"), "", "", "", "")
    for i, dev in enumerate(devices):
        table.add_row(str(i), dev.get("id", "N/A"), dev.get("model", "N/A"), dev.get("android_version", "N/A"), dev.get("last_account", "No Info"))
    console.print(table)
    rprint("══════════════════════════════════════════════════════════════")
    rprint("[bold yellow]Nhập [add] để [Thêm/Ghép nối thiết bị Wifi ADB mới (cần IP:PORT + 6 số PIN)][/bold yellow]")
    rprint("══════════════════════════════════════════════════════════════")

def add_adb_device():
    rprint(Panel("[bold cyan]THÊM THIẾT BỊ MỚI (PAIRING/CONNECT)[/bold cyan]", border_style="yellow"))
    ip_port = console.input("[bold green]Nhập IP:PORT (Ghép nối, ví dụ 172.16.0.2:42703): [/bold green][bold yellow]")
    pin_code = console.input("[bold green]Nhập mã Pin 6 số (bỏ trống nếu đã xác minh, hoặc chỉ muốn Connect): [/bold green][bold yellow]")
    ip_port_connect = ip_port
    if pin_code:
        rprint(f"[bold cyan]Đang ghép nối với {ip_port} bằng Pin: {pin_code}...[/bold cyan]")
        try:
            pair_result = subprocess.run(f"adb pair {ip_port} {pin_code}", shell=True, capture_output=True, text=True, timeout=5)
            rprint(f"[bold white]{pair_result.stdout.strip()}[/bold white]")
            if "Successfully paired" not in pair_result.stdout:
                rprint(Panel("[bold red]Ghép nối thất bại. Vui lòng kiểm tra lại IP/Port và mã Pin.[/bold red]", border_style="red"))
                return
        except Exception as e:
            rprint(Panel(f"[bold red]Lỗi khi ghép nối: {e}[/bold red]", border_style="red"))
            return
        rprint("══════════════════════════════════════════════════════════════")
        rprint("[bold green]Hãy nhập lại IP:Port mới (Port đã thay đổi sau khi ghép nối) để kết nối[/bold green]")
        ip_port_connect = console.input("[bold green]Nhập IP:PORT (Kết nối, ví dụ 172.16.0.2:39201): [/bold green][bold yellow]")
    rprint(f"[bold cyan]Đang kết nối ADB với {ip_port_connect}...[/bold cyan]")
    os.system(f"adb connect {ip_port_connect}")
    time.sleep(2)
    devices_output = os.popen("adb devices").read()
    if ip_port_connect in devices_output and "device" in devices_output:
        rprint(Panel(f"[bold green]Kết nối ADB thành công với {ip_port_connect}![/bold green]", border_style="green"))
    else:
        rprint(Panel(f"[bold red]Kết nối thất bại với {ip_port_connect}. Vui lòng kiểm tra lại.[/bold red]", border_style="red"))

# --- CHỌN ADB VÀ THIẾT LẬP ---
adb_device_id = None
selected_device = {}

os.system('cls' if os.name== 'nt' else 'clear')
console.print(banner)
rprint(Panel("[bold cyan]THIẾT LẬP ADB / UIAUTOMATOR2[/bold cyan]", border_style="yellow"))
rprint(f"[bold green][1] Sử dụng ADB (Android 11+) + uiautomator2 (tự click theo UI)[/bold green]")
rprint(f"[bold green][2] Không dùng ADB, chỉ mở app (Dùng auto-click ngoài) - (không khuyến nghị)[/bold green]")
rprint(Panel(f"[bold red] Nhập lựa chọn: [/bold red][bold yellow]", border_style="yellow"))
adbyn = console.input("[bold yellow]Nhập lựa chọn (1/2):[/bold yellow] ")

if adbyn == "1":
    while True:
        adb_devices = scan_and_get_all_devices()
        os.system('cls' if os.name== 'nt' else 'clear')
        console.print(banner)
        list_adb_devices(adb_devices)
        if not adb_devices:
            chon_tb = console.input("[bold yellow]Nhập [add] để thêm thiết bị hoặc Enter để quét lại: [/bold yellow]")
        else:
            rprint(f"[bold green]Nhập số thứ tự [bold cyan]của thiết bị[/bold cyan] cần chạy (ví dụ 0) [bold magenta]HOẶC[/bold magenta] nhập [bold yellow]add[/bold yellow] để thêm thiết bị:[/bold green]", end="")
            chon_tb = console.input("[bold yellow]")
        if chon_tb.lower() == 'add':
            add_adb_device()
            continue
        try:
            stt_list = [int(i.strip()) for i in chon_tb.split(',') if i.strip().isdigit()]
            if stt_list and 0 <= stt_list[0] < len(adb_devices):
                selected_device = adb_devices[stt_list[0]]
                adb_device_id = selected_device['id']
                rprint(f"[bold cyan]Đang kết nối lại với thiết bị: {adb_device_id}...[/bold cyan]")
                os.system(f"adb connect {adb_device_id}")
                time.sleep(1)
                devices_output = os.popen("adb devices").read()
                if f"{adb_device_id}\tdevice" not in devices_output:
                    rprint(Panel(f"[bold red]Kết nối lại với {adb_device_id} thất bại. Vui lòng kiểm tra kết nối Wifi ADB.[/bold red]", border_style="red"))
                    continue
                rprint(Panel("[bold green]Đã chọn thiết bị thành công![/bold green]", border_style="green"))
                break
            elif not chon_tb.strip():
                os.system('cls' if os.name== 'nt' else 'clear')
                console.print(banner)
                continue
            else:
                rprint(Panel("[bold red]Lựa chọn không hợp lệ hoặc thiết bị không tồn tại trong danh sách (Chắc chắn đã kết nối ADB).[/bold red]", border_style="red"))
        except:
            rprint(Panel("[bold red]Lựa chọn không hợp lệ. Vui lòng nhập số thứ tự hoặc 'add'.[/bold red]", border_style="red"))
elif adbyn == "2":
    rprint(Panel("[bold yellow]Không sử dụng ADB. Vui lòng tự thực hiện thao tác click thủ công hoặc dùng auto-click bên ngoài.[/bold yellow]", border_style="yellow"))

# --- MAIN LOOP VARIABLES ---
dem = 0
tong = 0
checkdoiacc = 0
dsaccloi = []
accloi = ""
nickname_hien_tai = chontktiktok["data"][luachon - 1]["nickname"]

hien_thi_man_hinh(dem, tong, nickname_hien_tai, TOOL_OWNER_BOT_TOKEN, TELEGRAM_CHAT_ID)
rprint(Panel("[bold green]Bắt Đầu Bú Job + Kiếm Xiền (uiautomator2 mode)[/bold green]", border_style="yellow"))

# ----------------- Helper: connect to uiautomator2 -----------------
def connect_uiautomator2(serial_or_ip):
    """Try to connect to device via uiautomator2. Returns device instance or None."""
    if u2 is None:
        return None
    # Try different connect methods gracefully
    try:
        # Preferred: connect to adb backend with serial
        d = u2.connect(serial_or_ip)
        # simple check
        d.deviceInfo  # will raise if not connected
        return d
    except Exception:
        try:
            d = u2.connect(serial_or_ip)  # retry same
            return d
        except Exception:
            try:
                # fallback connect_adb if available
                if hasattr(u2, "connect_adb"):
                    d = u2.connect_adb(serial_or_ip)
                    return d
            except Exception:
                return None
    return None

# ----------------- Helper: perform UI action -----------------
def perform_ui_action(d, job_type, timeout=6):
    """
    d: uiautomator2 device
    job_type: "like" or "follow"
    returns (success: bool, action_desc: str)
    """
    # Normalize
    job_type = job_type.lower()
    start = time.time()

    def safe_click(elem, desc=None):
        try:
            if elem.exists(timeout=1):
                elem.click()
                return True
        except Exception:
            pass
        return False

    # Try multiple selectors (content-desc, text, resourceId, xpath)
    if job_type == "like":
        # possible content-desc English or localized; try many heuristics
        candidates = [
            lambda: d(description="Like"),
            lambda: d(description="Like Button"),
            lambda: d(description="Thích"),
            lambda: d(resourceId="com.zhiliaoapp.musically:id/aw"),  # example resourceId (may vary)
            lambda: d(text="Like"),
            lambda: d(text="Thích"),
            lambda: d.xpath('//android.widget.ImageView[contains(@content-desc,"Like")]'),
            lambda: d.xpath('//android.widget.ImageView[contains(@content-desc,"Thích")]'),
            lambda: d.xpath('//android.widget.ImageView[contains(@resource-id,"like")]'),
        ]
        for cand in candidates:
            try:
                elem = cand()
                if elem is None:
                    continue
                if safe_click(elem):
                    return True, f"Clicked Like using {getattr(elem, '_selector', 'selector')}"
            except Exception:
                continue
        # As a last resort, try clicking any heart-like image near right side (best-effort)
        try:
            imgs = d(className="android.widget.ImageView")
            for i in range(min(10, imgs.count)):
                try:
                    el = imgs.get(i)
                    desc = el.info.get("contentDescription") or ""
                    if "like" in desc.lower() or "thích" in desc.lower():
                        el.click()
                        return True, "Clicked Like via heuristic ImageView"
                except Exception:
                    continue
        except Exception:
            pass
        return False, "Không tìm thấy nút Like"

    elif job_type == "follow":
        candidates = [
            lambda: d(text="Follow"),
            lambda: d(text="Theo dõi"),
            lambda: d(text="Following"),  # sometimes shows Following -> we skip if already following
            lambda: d(description="Follow"),
            lambda: d(resourceId="com.zhiliaoapp.musically:id/at"),  # example; may vary
            lambda: d.xpath('//android.widget.Button[contains(@text,"Follow")]'),
            lambda: d.xpath('//android.widget.Button[contains(@text,"Theo dõi")]'),
            lambda: d.xpath('//android.widget.TextView[contains(@text,"Follow")]'),
        ]
        for cand in candidates:
            try:
                elem = cand()
                if elem is None:
                    continue
                # If element text indicates already following, skip
                try:
                    txt = elem.get_text() if hasattr(elem, "get_text") else ""
                    if txt and ("Following" in txt or "Đang theo dõi" in txt):
                        return False, "Đã follow trước đó"
                except Exception:
                    pass
                if safe_click(elem):
                    return True, f"Clicked Follow using selector"
            except Exception:
                continue
        # Another heuristic: look for "Follow" buttons by class and content
        try:
            btns = d(className="android.widget.Button")
            for i in range(min(10, btns.count)):
                try:
                    el = btns.get(i)
                    txt = el.info.get("text") or ""
                    if "follow" in txt.lower() or "theo dõi" in txt.lower():
                        el.click()
                        return True, "Clicked Follow via heuristic Button"
                except Exception:
                    continue
        except Exception:
            pass
        return False, "Không tìm thấy nút Follow"

    else:
        return False, "Loại job không hỗ trợ"

# -------------------------------------------------------------
# --- VÒNG LẶP CHÍNH ---
# -------------------------------------------------------------
while True:
    # đổi acc logic
    if checkdoiacc == doiacc:
        dsaccloi.append(chontktiktok["data"][luachon - 1]["nickname"])
        hien_thi_man_hinh(dem, tong, nickname_hien_tai, TOOL_OWNER_BOT_TOKEN, TELEGRAM_CHAT_ID)
        rprint(Panel(f"[bold red] Acc Tiktok {nickname_hien_tai} gặp vấn đề hoặc bị nhả🚨[/bold red]", border_style="red"))
        dsacc()
        while True:
            try:
                rprint(Panel("[bold green]🚀 Chọn tài khoản mới đê : [/bold green][bold yellow]", border_style="yellow"))
                luachon = int(console.input("[bold yellow]Nhập số thứ tự:[/bold yellow] "))
                if luachon < 1 or luachon > len(chontktiktok["data"]):
                    rprint(Panel(f"[bold red]🚀 Acc Này Không Có Trong Danh Sách Cấu Hình. Vui lòng nhập lại Acc Khác : [/bold red][bold yellow]", border_style="red"))
                    continue
                account_id = chontktiktok["data"][luachon - 1]["id"]
                nickname_hien_tai = chontktiktok["data"][luachon - 1]["nickname"]
                checkdoiacc = 0
                hien_thi_man_hinh(dem, tong, nickname_hien_tai, TOOL_OWNER_BOT_TOKEN, TELEGRAM_CHAT_ID)
                rprint(Panel("[bold green]Bắt Đầu Bú Job + Kiếm Xiền[/bold green]", border_style="yellow"))
                break
            except ValueError:
                rprint(Panel("[bold red] Sai Định Dạng !!![/bold red]", border_style="red"))

    # lấy job
    nhanjob = None
    job_found = False
    with console.status(f'[bold yellow]💸 Đang get job, chờ 2s...[/bold yellow]') as status:
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            try:
                nhanjob = nhannv(account_id)
                if nhanjob and nhanjob.get("status") == 200 and nhanjob["data"].get("link") and nhanjob["data"].get("object_id"):
                    job_found = True
                    break
                elif nhanjob and nhanjob.get("status") == 200 and (nhanjob.get("data") is None or nhanjob.get("data") == {}):
                    status.update(f"[bold yellow]Hết job khả dụng trên Golike. Đợi 10s và thử lại...[/bold yellow]")
                    time.sleep(10)
                    retry_count = 0
                    break
                else:
                    status.update(f"[bold red]Lỗi API khi nhận job (Status: {nhanjob.get('status', 'N/A')}). Thử lại lần {retry_count + 1}.[/bold red]")
                    retry_count += 1
                    time.sleep(2)
            except Exception:
                status.update(f"[bold red]Lỗi kết nối khi nhận job. Thử lại lần {retry_count + 1}.[/bold red]")
                retry_count += 1
                time.sleep(1)

    if not job_found:
        if nhanjob and nhanjob.get("status") == 200 and (nhanjob.get("data") is None or nhanjob.get("data") == {}):
            continue
        hien_thi_man_hinh(dem, tong, nickname_hien_tai, TOOL_OWNER_BOT_TOKEN, TELEGRAM_CHAT_ID)
        rprint(Panel("[bold red]Không nhận được job hợp lệ sau nhiều lần thử. Chờ 5s và thử lại.[/bold red]", border_style="red"))
        time.sleep(5)
        continue

    # job info
    ads_id = nhanjob["data"]["id"]
    link = nhanjob["data"]["link"]
    object_id = nhanjob["data"]["object_id"]
    job_type = nhanjob["data"]["type"]

    if (loai_nhiem_vu == 1 and job_type != "follow") or (loai_nhiem_vu == 2 and job_type != "like") or (job_type not in ["follow", "like"]):
        baoloi(ads_id, object_id, account_id, job_type)
        hien_thi_man_hinh(dem, tong, nickname_hien_tai, TOOL_OWNER_BOT_TOKEN, TELEGRAM_CHAT_ID)
        rprint(Panel(f"[bold yellow]→ Bỏ qua Job [bold blue]{job_type}[/bold blue] vì không được chọn.[/bold yellow]", border_style="yellow", width=60))
        continue

    # Thực thi job
    try:
        hien_thi_man_hinh(dem, tong, nickname_hien_tai, TOOL_OWNER_BOT_TOKEN, TELEGRAM_CHAT_ID)
        adb_action = "Chế độ manual. Vui lòng tự click thủ công."
        device_info_text = ""

        if adbyn == "1":
            device_id_display = adb_device_id
            device_model_display = selected_device.get('model', 'N/A')
            device_info_text = f"[[bold magenta]MODEL: {device_model_display}[/bold magenta] | [bold yellow]ID: {device_id_display}[/bold yellow]]"

            # Connect uiautomator2 to device
            d = connect_uiautomator2(adb_device_id)
            if d is None:
                # If cannot connect uiautomator2, fallback: try adb am start (but won't click)
                os.system(f'adb -s {adb_device_id} shell am start -a android.intent.action.VIEW -d "{link}" > /dev/null 2>&1')
                adb_action = "Không kết nối uiautomator2 - mở link bằng adb nhưng không tự click (bỏ qua)."
                execution_panel = Panel(Text.from_markup(f"[bold red]Không thể kết nối uiautomator2 với thiết bị {adb_device_id}. Bỏ qua thao tác tự động.[/bold red]\n{adb_action}"), title="[bold red]UIAUTOMATOR2 LỖI[/bold red]", border_style="red")
                console.print(execution_panel)
            else:
                # Open link using am start via device shell (safer) - ensures TikTok opens in foreground
                try:
                    d.shell(f'am start -a android.intent.action.VIEW -d "{link}"')
                except Exception:
                    # fallback to adb shell
                    os.system(f'adb -s {adb_device_id} shell am start -a android.intent.action.VIEW -d "{link}" > /dev/null 2>&1')

                # give app time to load UI
                time.sleep(3)

                success, action_desc = perform_ui_action(d, job_type)
                if success:
                    adb_action = f"uiautomator2: {action_desc}"
                else:
                    adb_action = f"uiautomator2 FAILED: {action_desc}"
                    # Report error to Golike: mark as skip/failed
                    baoloi(ads_id, object_id, account_id, job_type)

        else:
            # Non-ADB mode: try to open via termux-open-url (as before), but cannot click
            try:
                subprocess.run(["termux-open-url", link], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                os.system(f'am start -a android.intent.action.VIEW -d "{link}"')
            adb_action = "Không dùng ADB - mở link bằng Termux/Local (không tự click)."

        execution_panel = Panel(Text.from_markup(f"[bold cyan]→ Nhận Job: {device_info_text} [bold blue]{job_type.upper()}[/bold blue][/bold cyan]\n[bold white]  Đang mở link TikTok...[/bold white]\n[bold green]  Đã chờ TikTok 3s.[/bold green]\n[bold magenta]→ [bold yellow]Action:[/bold yellow] {adb_action}[/bold magenta]"), title=f"[bold blue]THỰC THI JOB {job_type.upper()}[/bold blue]", border_style="blue", width=60)
        console.print(execution_panel)

    except Exception as e:
        baoloi(ads_id, object_id, account_id, job_type)
        hien_thi_man_hinh(dem, tong, nickname_hien_tai, TOOL_OWNER_BOT_TOKEN, TELEGRAM_CHAT_ID)
        error_message = f"Lỗi thực thi: {str(e)}"
        error_panel = Panel(Text.from_markup(f"[bold red]❌ Bỏ qua job do lỗi: {error_message}[/bold red]"), title=f"[bold red]JOB {job_type.upper()} BÁO LỖI[/bold red]", border_style="red")
        console.print(error_panel)
        continue

    # Đếm ngược delay
    with console.status(f"[bold cyan]Chờ {delay}s để bú tiền ...[/bold cyan]"):
        time.sleep(delay)

    # Hoàn thành job - gọi API hoanthanh
    console.print(" " * 60, end="\r")
    max_attempts = 2
    attempts = 0
    nhantien = None
    while attempts < max_attempts:
        try:
            nhantien = hoanthanh(ads_id, account_id)
            if nhantien and nhantien.get("status") == 200:
                break
        except:
            pass
        attempts += 1
        time.sleep(0.5)

    # Kết quả
    if nhantien and nhantien.get("status") == 200:
        dem += 1
        tien = nhantien["data"]["prices"]
        tong += tien
        hien_thi_man_hinh(dem, tong, nickname_hien_tai, TOOL_OWNER_BOT_TOKEN, TELEGRAM_CHAT_ID)
        local_time = time.localtime()
        h = f"{local_time.tm_hour:02d}"
        m = f"{local_time.tm_min:02d}"
        s = f"{local_time.tm_sec:02d}"
        result_table = Table(title=f"[bold green]✅ HOÀN THÀNH JOB #{dem}[/bold green]", title_style="bold yellow", border_style="green", show_header=False, width=60, show_lines=True)
        result_table.add_column("THÔNG TIN JOB", style="bold white")
        job_info = Text.assemble(
            Text.from_markup("[bold green]TRẠNG THÁI:[/bold green] DC TIỀN RÙI  "),
            Text.from_markup("[bold blue]LOẠI JOB:[/bold blue] "), (job_type.upper(), "bold white"), ("  \n"),
            Text.from_markup("[bold yellow]TIỀN NHẬN:[/bold yellow] +"), (f"{tien:,.0f} VNĐ", "bold white"), ("  \n"),
            Text.from_markup("[bold white]THỜI GIAN:[/bold white] "), (f"{h}:{m}:{s}", "bold white"),
        )
        result_table.add_row(job_info)
        console.print(result_table)

        if TELEGRAM_CHAT_ID and TOOL_OWNER_BOT_TOKEN != "YOUR_TELEGRAM_BOT_TOKEN_HERE":
            telegram_text = (
                f"*✅ HOÀN THÀNH JOB #{dem}*\\n"
                f"- Nick: *{nickname_hien_tai}*\\n"
                f"- Loại: `{job_type.upper()}`\\n"
                f"- Tiền: `+{tien:,.0f} VNĐ`\\n"
                f"- Tổng: `JOB {dem} | {tong:,.0f} VNĐ`\\n"
                f"- Thời gian: {h}:{m}:{s}"
            )
            send_telegram_message(telegram_text, TELEGRAM_CHAT_ID, TOOL_OWNER_BOT_TOKEN)

        time.sleep(0.7)
        checkdoiacc = 0
    else:
        try:
            baoloi(ads_id, object_id, account_id, job_type)
            hien_thi_man_hinh(dem, tong, nickname_hien_tai, TOOL_OWNER_BOT_TOKEN, TELEGRAM_CHAT_ID)
            error_message = "Acc nhả/Hoàn thành lỗi."
            error_panel = Panel(Text.from_markup(f"[bold red]❌ Bỏ qua job do lỗi: {error_message}[/bold red]"), title=f"[bold red]JOB {job_type.upper()} BÁO LỖI[/bold red]", border_style="red")
            console.print(error_panel)
            sleep(1)
            checkdoiacc += 1
        except:
            pass