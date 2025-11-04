# coding: utf-8
import os
import sys
import time
import json
import random 
import requests
import itertools
import traceback 
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.table import Table
from rich.style import Style
from rich.box import DOUBLE, HEAVY, HEAVY_EDGE, ROUNDED 
from rich.markup import escape 
import requests.exceptions # Thêm thư viện để bắt lỗi Redirect

# --- Configuration & Setup ---

# BẬT MÀU SẮC TRỞ LẠI VÀ THIẾT LẬP MÀU CHỦ ĐẠO
console = Console(force_terminal=True, color_system="truecolor") 
# Tắt cảnh báo requests
requests.packages.urllib3.disable_warnings() 

# Hằng số
LOCK_TIME_SECONDS = 600 # 10 phút tạm ngưng khi tài khoản IG bị block/login required

# File paths
AUTHORIZATION_FILE = "Authorization.txt"
LOGIN_INFO_FILE = "login_IG.json" 
USER_AGENT_FILE = "user_agent.txt" 
CONFIG_FILE = "config.json" # <--- FILE CẤU HÌNH MỚI

# =========================================================================
# 📢 CẤU HÌNH: THÔNG BÁO TELEGRAM MỚI (CHỈ CẦN CHAT ID CỦA NGƯỜI DÙNG, KHÔNG LƯU FILE)
# =========================================================================
# ⚠️ CỐ ĐỊNH TOKEN CỦA BOT CHỦ TOOL TẠI ĐÂY!
# (Người dùng không cần biết token này, chỉ cần biết Chat ID)
GLOBAL_TELEGRAM_TOKEN = "8230870404:AAGri9A07HH-6nOA91j-kCnuFUW-SEEU64U" 

# GLOBAL_TELEGRAM_CHAT_ID sẽ được lưu trong bộ nhớ (không lưu ra file)
GLOBAL_TELEGRAM_CHAT_ID = None
# =========================================================================

# GoLike API Endpoints
API_BASE = "https://gateway.golike.net/api"
INSTAGRAM_ACCOUNT_URL = f"{API_BASE}/instagram-account"
GET_JOBS_URL = f"{API_BASE}/advertising/publishers/instagram/jobs"
COMPLETE_JOBS_URL = f"{API_BASE}/advertising/publishers/instagram/complete-jobs"
REPORT_URL = f"{API_BASE}/report/send"
SKIP_JOBS_URL = f"{API_BASE}/advertising/publishers/instagram/skip-jobs"

# User-Agent mặc định và toàn cục
DEFAULT_USER_AGENT = 'Mozilla/50 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
# Biến này sẽ được cập nhật sau khi người dùng nhập
GLOBAL_USER_AGENT = DEFAULT_USER_AGENT 

# Cấu trúc dữ liệu cho mỗi tài khoản Instagram
# [{"id": 1234, "username": "user_a", "cookies": "ig_cookies", "fail_count": 0, "success_count": 0, "is_locked": False, "lock_until": 0}, ...]
ACCOUNTS_LIST = [] 

# IG Headers cơ bản cho đăng nhập
IG_LOGIN_HEADERS = {
    'Accept': '*/*',
    'Accept-Language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'https://www.instagram.com',
    'Referer': 'https://www.instagram.com/accounts/login/',
    'User-Agent': GLOBAL_USER_AGENT, 
    'X-Csrftoken': 'missing',
    'X-Instagram-Ajax': '1007802778',
    'X-Ig-App-Id': '936619743392459',
}
IG_LOGIN_URL = 'https://www.instagram.com/accounts/login/ajax/'

# --- Utility Functions ---

def trim_title_for_panel(title: str, max_width: int = 60) -> str:
    """Cắt bớt tiêu đề nếu nó quá dài để tránh lỗi tràn Panel trên một số terminal."""
    if len(title) > max_width:
        return title[:max_width-3] + "..."
    return title

def safe_dict_check(data, context="API"):
    """
    Kiểm tra an toàn. Đảm bảo dữ liệu là dictionary. 
    Nếu không phải, trả về một dictionary lỗi để ngăn chặn crash FATAL ERROR: 'str' object has no attribute 'get'.
    """
    if not data:
         error_message = f"Critical Error: {context} returned empty data. Returning 500."
         return {"status": 500, "message": error_message, "critical_safe_check_fail": True}
         
    if not isinstance(data, dict):
        error_message = f"Critical Error: {context} returned type {type(data)} instead of dict. Raw data: {str(data)[:50]}"
        return {"status": 500, "message": error_message, "critical_safe_check_fail": True}
    return data

def get_cookie_file_path(username: str):
    """Trả về đường dẫn file cookies theo username."""
    return f"cookies_{username}.txt"

def clear_screen():
    """Xóa màn hình Termux/CMD/PowerShell. Tương thích đa nền tảng."""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_base_headers(authorization: str = None):
    """Trả về headers chuẩn cho API GoLike. Đã cập nhật User-Agent."""
    headers = {
        'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8',
        'Referer': 'https://app.golike.net/',
        'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'Sec-Ch-ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': "Windows",
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'T': 'VFZSak1FMTZZM3BOZWtFd1RtYzlQUT09',
        'User-Agent': GLOBAL_USER_AGENT, 
        'Content-Type': 'application/json;charset=utf-8'
    }
    if authorization:
        headers['Authorization'] = authorization
    return headers

def safe_file_rw(file_path: str, mode: str, content: any = None): # Cập nhật type hint cho content
    """Đọc/ghi/xóa/ghi JSON/đọc JSON file an toàn."""
    try:
        if mode == 'r':
            if not os.path.exists(file_path):
                return None
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        elif mode == 'w' and content is not None:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        elif mode == 'd':
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        elif mode == 'wj' and content is not None:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=4) # Thêm indent để dễ đọc
            return True
        elif mode == 'rj':
            if not os.path.exists(file_path):
                return None
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)

    except IOError as e:
        console.print(f"❌ [bold red]Lỗi thao tác file {file_path}: {e}[/bold red]")
        # Không thoát chương trình, chỉ dừng thao tác file
        return None
    except json.JSONDecodeError:
        console.print(f"❌ [bold red]Lỗi đọc file JSON {file_path}.[/bold red]")
        return None
    return False

# --- CÁC HÀM CẤU HÌNH MỚI ---

DEFAULT_CONFIG = {
    "delay": 5,
    "lannhan_lan2": True,
    "doiacc_fail_limit": 5,
    "job_success_limit": 10,
    "job_ratio": "1,1", # Like,Follow
    "chedo_job": 12 # 1: Follow, 2: Like, 12: All
}

def load_config():
    """Tải cấu hình từ file config.json."""
    config = safe_file_rw(CONFIG_FILE, 'rj')
    if config:
        # Hợp nhất với cấu hình mặc định để đảm bảo không bị thiếu key mới
        return {**DEFAULT_CONFIG, **config}
    return None

def save_config(settings: dict):
    """Lưu cấu hình hiện tại vào file config.json."""
    return safe_file_rw(CONFIG_FILE, 'wj', settings)

# --------------------------

# --- HÀM get_real_ip_info ĐÃ CẬP NHẬT THEO YÊU CẦU ---
def get_real_ip_info():
    """
    Lấy IP công cộng và thông tin địa lý chi tiết (Quốc gia, Tỉnh/Thành phố) 
    với cơ chế dự phòng và gọi API ngẫu nhiên.
    """
    
    # Danh sách các API dịch vụ IP, với các hàm xử lý dữ liệu tương ứng
    # Hàm xử lý: lambda data -> dict {"ip": str, "location": str}
    api_services = [
        # API 1: ip-api.com
        {
            "url": 'http://ip-api.com/json', 
            "handler": lambda data: {
                "ip": data.get('query', 'N/A'),
                "location": f"{data.get('city', 'N/A')}, {data.get('regionName', 'N/A')}, {data.get('country', 'N/A')}"
            },
            "success_key": 'status',
            "success_value": 'success'
        },
        # API 2: ipwhois.app/json
        {
            "url": 'https://ipwhois.app/json',
            "handler": lambda data: {
                "ip": data.get('ip', 'N/A'),
                "location": f"{data.get('city', 'N/A')}, {data.get('region', 'N/A')}, {data.get('country', 'N/A')}"
            },
            "success_key": 'success',
            "success_value": True
        },
        # API 3: ipinfo.io/json
        {
            "url": 'https://ipinfo.io/json', 
            "handler": lambda data: {
                "ip": data.get('ip', 'N/A'),
                "location": f"{data.get('city', 'N/A')}, {data.get('region', 'N/A')}, {data.get('country', 'N/A')}"
            },
            "success_key": 'ip', # Kiểm tra sự tồn tại của key 'ip'
            "success_value": lambda v: v is not None # Logic kiểm tra giá trị
        },
        # API 4: freegeoip.app/json/
        {
            "url": 'https://freegeoip.app/json/', 
            "handler": lambda data: {
                "ip": data.get('ip', 'N/A'),
                "location": f"{data.get('city', 'N/A')}, {data.get('region_name', 'N/A')}, {data.get('country_name', 'N/A')}"
            },
            "success_key": 'ip',
            "success_value": lambda v: v is not None
        }
    ]
    
    # Xáo trộn danh sách API để gọi ngẫu nhiên
    random.shuffle(api_services)
    
    for api in api_services:
        try:
            response = requests.get(api['url'], timeout=5)
            response.raise_for_status() # Lỗi HTTP sẽ ném exception
            data = response.json()
            
            is_success = False
            
            # Kiểm tra trạng thái thành công
            if api['success_key'] in data:
                expected_value = api['success_value']
                actual_value = data[api['success_key']]
                
                if callable(expected_value):
                    is_success = expected_value(actual_value)
                else:
                    is_success = (actual_value == expected_value)
            
            if is_success:
                return api['handler'](data)
                
        except requests.exceptions.RequestException:
            # Bỏ qua, thử API tiếp theo
            continue
        except json.JSONDecodeError:
            # Bỏ qua, thử API tiếp theo
            continue 

    # Trả về mặc định nếu tất cả API đều thất bại
    return {"ip": "N/A", "location": "Không thể lấy vị trí"}
# --- KẾT THÚC HÀM get_real_ip_info ĐÃ CẬP NHẬT ---

def create_job_cycler(ratio_str: str, lam: list):
    """
    Tạo một iterator chu kỳ các loại job dựa trên tỉ lệ và lựa chọn.
    ratio_str: "1,2" (Like,Follow)
    lam: ["like", "follow"]
    """
    if not lam:
        return itertools.cycle([])
        
    try:
        parts = [int(p.strip()) for p in ratio_str.split(',') if p.strip().isdigit()]
        if len(parts) != 2:
            raise ValueError("Invalid ratio format")
            
        # parts[0] là tỉ lệ Like, parts[1] là tỉ lệ Follow
        ratio_like, ratio_follow = parts
        
    except ValueError:
        # Mặc định 1:1 nếu nhập sai
        ratio_like, ratio_follow = 1, 1

    jobs = []
    if "like" in lam and ratio_like > 0:
        jobs.extend(["like"] * ratio_like)
    if "follow" in lam and ratio_follow > 0:
        jobs.extend(["follow"] * ratio_follow)
        
    if not jobs:
        return itertools.cycle([])

    return itertools.cycle(jobs)

# --- Display Functions ---

def display_banner():
    """Hiển thị banner."""
    clear_screen()
    
    banner_art = Text(justify="center")
    art_lines = """
 ██████╗  ██████╗ ██╗     ██╗██╗  ██╗███████╗    ██╗ ██████╗ 
██╔════╝ ██╔═══██╗██║     ██║██║ ██╔╝██╔════╝    ██║██╔════╝ 
██║  ███╗██║   ██║██║     ██║█████╔╝ █████╗      ██║██║  ███╗
██║  ██║██║   ██║██║     ██║██╔═██╗ ██╔══╝      ██║██║  ██║
╚██████╔╝╚██████╔╝███████╗██║██║  ██╗███████╗    ██║╚██████╔╝
 ╚═════╝  ╚══════╝ ╚══════╝╚═╝╚╚═╝  ╚═╝╚═════╝    ╚═╝ ╚═════╝
    """
    
    for line in art_lines.split('\n'):
        if line.strip():
            banner_art.append(Text(line.strip(), style="bold yellow") + "\n")
            
    console.print(Panel(
        banner_art, 
        title=trim_title_for_panel("[bold cyan]✨ INSTAGRAM TOOL VIP (MULTI-ACCOUNT) ✨"), 
        border_style=Style(color="cyan", bold=True), 
        padding=(1, 1),
        title_align="center",
        box=HEAVY_EDGE
    ))

def display_current_info(authorization: str):
    """Hiển thị trạng thái Authorization và IP thật cùng vị trí địa lý."""
    
    ip_info = get_real_ip_info()
    
    auth_status = Text()
    auth_status.append(f"Authorization: ")
    auth_status.append(f"{'ĐÃ KẾT NỐI' if authorization else 'CHƯA CÓ'}", style=f"bold {'green' if authorization else 'red'}")
    
    # Đã thêm màu cho các thông tin trạng thái
    ip_display = Text(f" Địa Chỉ IP  : {ip_info['ip']}", style="bold magenta")
    location_display = Text(f" Vị trí  : {ip_info['location']}", style="bold green")
    ua_display = Text(f" User-Agent  : {GLOBAL_USER_AGENT[:50]}...", style="bold cyan")
    
    info_table = Table(title="[bold yellow]🌍 TRẠNG THÁI HIỆN TẠI 🌍[/bold yellow]", border_style="bold yellow", show_header=False, show_lines=False)
    info_table.add_column("Key", style="bold green")
    info_table.add_column("Value")
    
    info_table.add_row(" Authorization:", auth_status)
    info_table.add_row("", ip_display)
    info_table.add_row("", location_display)
    info_table.add_row("", ua_display) 
    info_table.add_row(" Tài khoản IG:", f"[bold magenta]{len(ACCOUNTS_LIST)}[/bold magenta] đã chọn") 
    
    console.print(Panel(
        info_table, 
        border_style="deep_sky_blue1", 
        title_align="center",
        box=HEAVY_EDGE
    ))

# --- User-Agent Function ---

def get_user_agent():
    """Xử lý việc nhập và lưu User-Agent."""
    global GLOBAL_USER_AGENT
    
    display_banner()
    
    current_ua = safe_file_rw(USER_AGENT_FILE, 'r')
    if current_ua:
        GLOBAL_USER_AGENT = current_ua
    
    IG_LOGIN_HEADERS['User-Agent'] = GLOBAL_USER_AGENT

    ua_menu_text = Text(justify="left")
    
    # FIX: Tối ưu hóa cách nối Text để đảm bảo màu sắc
    ua_menu_text.append(f" ✈ User-Agent hiện tại: {GLOBAL_USER_AGENT[:50]}...", style="bold white")
    ua_menu_text.append("\n ✈ ", style="bold white").append("1", style="bold cyan").append(" : Dùng User-Agent hiện tại niếu bị lỗi gì thì dùng User-Agent  mặt định ", style="bold white")
    ua_menu_text.append("\n ✈ ", style="bold white").append("2", style="bold cyan").append(" : Nhập User-Agent mới (Sẽ được lưu)", style="bold white")
    ua_menu_text.append("\n ✈ ", style="bold white").append("3", style="bold cyan").append(" : Xóa và dùng User-Agent Mặc định", style="bold white")
    
    console.print(Panel(
        ua_menu_text,
        title=trim_title_for_panel("[bold yellow]👤 LỰA CHỌN USER-AGENT 👤[/bold yellow]"),
        border_style="yellow",
        box=HEAVY_EDGE, 
        title_align="center"
    ))
    
    prompt_default = "1"
    
    while True:
        choice = Prompt.ask(f" ✈ [bold yellow]Nhập Lựa Chọn (1/2/3)[/bold yellow]", default=prompt_default).strip()
        
        if choice == '1':
            break
        
        elif choice == '2':
            console.print("[bold yellow]════════════════════════════════════════════════[/bold yellow]")
            new_ua = Prompt.ask(f" ✈ [bold cyan]Nhập User-Agent mới[/bold cyan]").strip()
            if new_ua:
                safe_file_rw(USER_AGENT_FILE, 'w', new_ua)
                GLOBAL_USER_AGENT = new_ua
                console.print(f"✔ [bold green]Đã lưu User-Agent mới![/bold green]")
                break
            else:
                console.print("[bold red]User-Agent không được để trống![/bold red]")
                
        elif choice == '3':
            if safe_file_rw(USER_AGENT_FILE, 'd'):
                console.print(f"✔ [bold green]Đã xóa {USER_AGENT_FILE}![/bold green]")
            GLOBAL_USER_AGENT = DEFAULT_USER_AGENT
            console.print(f"✔ [bold green]Đã chuyển về User-Agent mặc định.[/bold green]")
            break
            
        else:
            console.print("❌ [bold red]Lựa chọn không hợp lệ! Hãy nhập lại.[/bold red]")

    IG_LOGIN_HEADERS['User-Agent'] = GLOBAL_USER_AGENT
    console.print(f"✔ [bold green]Sử dụng User-Agent: {GLOBAL_USER_AGENT[:50]}...[/bold green]")
    time.sleep(1) 

# --- Authorization Function ---

def get_authorization():
    """Xử lý file Authorization."""
    display_banner()
    
    console.print("✅ [bold green]ĐANG CHẠY CODE PYTHON ĐÃ NÂNG CẤP HỖ TRỢ ĐA TÀI KHOẢN INSTAGRAM![/bold green]") 
    
    current_auth = safe_file_rw(AUTHORIZATION_FILE, 'r')
    display_current_info(current_auth) 
    
    auth_menu_text = Text(justify="left")
    # FIX: Tối ưu hóa cách nối Text để đảm bảo màu sắc
    auth_menu_text.append(" ✈ Nhập ", style="bold white").append("1", style="bold cyan").append(" để vào Tool Instagram", style="bold white")
    auth_menu_text.append("\n ✈ Nhập ", style="bold white").append("2", style="bold cyan").append(" Để Xóa Authorization Hiện Tại", style="bold white")
    
    console.print(Panel(
        auth_menu_text,
        title=trim_title_for_panel("[bold cyan]✈️ LỰA CHỌN TÁC VỤ ✈️[/bold cyan]"),
        border_style="cyan",
        box=HEAVY_EDGE, 
        title_align="center"
    ))
    
    while True:
        choice = Prompt.ask(f" ✈ [bold yellow]Nhập Lựa Chọn (1 hoặc 2)[/bold yellow]").strip()
        if choice in ['1', '2']:
            choice = int(choice)
            break
        console.print("❌ [bold red]Lựa chọn không hợp lệ! Hãy nhập lại.[/bold red]")

    if choice == 2:
        if safe_file_rw(AUTHORIZATION_FILE, 'd'):
            console.print(f"✔ [bold green]Đã xóa {AUTHORIZATION_FILE}![/bold green]")
        else:
            console.print(f"! [bold yellow]File {AUTHORIZATION_FILE} không tồn tại![/bold yellow]")
        console.print("👉 [bold white]Vui lòng nhập lại thông tin![/bold white]")

    auth_content = safe_file_rw(AUTHORIZATION_FILE, 'r')
    
    while not auth_content:
        console.print("[bold yellow]════════════════════════════════════════════════[/bold yellow]")
        auth_content = Prompt.ask(f" ✈ [bold cyan]Nhập Authorization[/bold cyan]").strip()
        if auth_content:
            safe_file_rw(AUTHORIZATION_FILE, 'w', auth_content)
        else:
            console.print("[bold red]Authorization không được để trống![/bold red]")

    return auth_content

# --- Instagram Login/Cookies Functions ---

def ig_login(username: str, password: str):
    """Đăng nhập Instagram bằng tài khoản/mật khẩu và trả về chuỗi cookies."""
    
    IG_LOGIN_HEADERS['User-Agent'] = GLOBAL_USER_AGENT
    
    with requests.Session() as s:
        try:
            # 1. Get CSRF Token
            r = s.get('https://www.instagram.com/accounts/login/', headers=IG_LOGIN_HEADERS, timeout=10)
            csrf_token = s.cookies.get('csrftoken')
            
            if not csrf_token:
                console.print("❌ [bold red]Không lấy được CSRF token ban đầu. Đăng nhập thất bại.[/bold red]")
                return None
            
            IG_LOGIN_HEADERS['X-Csrftoken'] = csrf_token
            
            # 2. Login POST
            login_data = {
                'username': username,
                'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{password}',
                'queryParams': {},
                'optIntoOneTap': 'false'
            }
            
            console.print("⏳ [bold yellow]Đang gửi yêu cầu đăng nhập...[/bold yellow]")
            
            r_login = s.post(IG_LOGIN_URL, headers=IG_LOGIN_HEADERS, data=login_data, timeout=10)
            login_json = r_login.json()

            if login_json.get('authenticated'):
                console.print("✅ [bold green]Đăng nhập thành công![/bold green]")
                cookie_str = "; ".join([f"{k}={v}" for k, v in s.cookies.items()])
                safe_file_rw(get_cookie_file_path(username), 'w', cookie_str)
                return cookie_str
            
            elif login_json.get('two_factor_required'):
                console.print("⚠️ [bold yellow]Yêu cầu xác thực hai yếu tố (2FA). Vui lòng nhập Cookies thủ công![/bold yellow]")
                return None

            else:
                console.print(f"❌ [bold red]Đăng nhập thất bại. Message: {login_json.get('message', 'Lỗi không rõ')}[/bold red]")
                return None
            
        except requests.exceptions.RequestException as e:
            console.print(f"❌ [bold red]Lỗi kết nối khi đăng nhập IG: {e}[/bold red]")
            return None
        except Exception as e:
            console.print(f"❌ [bold red]Lỗi không xác định khi đăng nhập IG: {e}[/bold red]")
            return None

def get_cookies_for_account(username: str):
    """Cho phép người dùng nhập hoặc đăng nhập để lấy cookies cho một tài khoản cụ thể. 
    Enter để bỏ qua."""
    
    cookies_file = get_cookie_file_path(username)
    cookies = safe_file_rw(cookies_file, 'r')
    
    while True:
        display_banner()
        display_current_info(safe_file_rw(AUTHORIZATION_FILE, 'r'))
        
        cookies_menu_text = Text(justify="left")
        
        cookies_menu_text.append(f" 🍪 Quản lý Cookies cho tài khoản: {username} 🍪 ", style="bold yellow")
        
        if cookies:
            cookies_menu_text.append("\n ✈ Cookies hiện tại: ", style="bold white").append("ĐÃ TÌM THẤY", style="bold green")
            cookies_menu_text.append("\n ✈ Nhập ", style="bold white").append("ENTER", style="bold cyan").append(" : Dùng Cookies hiện tại và TIẾP TỤC sang nick tiếp theo", style="bold white")
            cookies_menu_text.append("\n ✈ Nhập ", style="bold white").append("1", style="bold cyan").append(" : Nhập Cookies Thủ công mới (sẽ ghi đè)", style="bold white")
            cookies_menu_text.append("\n ✈ Nhập ", style="bold white").append("2", style="bold cyan").append(" : Đăng nhập bằng tài khoản/mật khẩu IG (Tạo cookies mới)", style="bold white")
            
            prompt_default = "" 
        else:
            cookies_menu_text.append("\n ✈ ", style="bold white").append("Chưa có Cookies IG", style="bold red")
            cookies_menu_text.append("\n ✈ Nhập ", style="bold white").append("ENTER", style="bold cyan").append(" : Bỏ qua tài khoản này (Không chạy)", style="bold white")
            cookies_menu_text.append("\n ✈ Nhập ", style="bold white").append("1", style="bold cyan").append(" : Nhập Cookies Thủ công", style="bold white")
            cookies_menu_text.append("\n ✈ Nhập ", style="bold white").append("2", style="bold cyan").append(" : Đăng nhập bằng tài khoản/mật khẩu IG (Tạo cookies)", style="bold white")
            
            prompt_default = ""

        console.print(Panel(
            cookies_menu_text,
            title=trim_title_for_panel(f"[bold magenta]QUẢN LÝ COOKIES: {username}[/bold magenta]"),
            border_style="magenta",
            box=HEAVY_EDGE, 
            title_align="center"
        ))
        
        choice = Prompt.ask(f" ✈ [bold yellow]Nhập Lựa Chọn (Enter/1/2)[/bold yellow]", default=prompt_default).strip()
        
        if choice == '': # Người dùng nhấn ENTER
            if cookies:
                console.print(f"✔ [bold green]Sử dụng Cookies cũ cho {username}.[/bold green]")
                return cookies # Cookies đã có, dùng luôn
            else:
                console.print(f"❌ [bold red]Bỏ qua tài khoản {username} (Không có Cookies).[/bold red]")
                return None # Cookies chưa có, bỏ qua
        
        elif choice == '1': # Nhập Cookies Thủ công mới
            if cookies and safe_file_rw(get_cookie_file_path(username), 'd'):
                console.print(f"✔ [bold green]Đã xóa cookies cũ![/bold green]")
            
            cookies_content = Prompt.ask(f" ✈ [bold cyan]Nhập Cookies cho {username}[/bold cyan]").strip()
            
            if cookies_content:
                safe_file_rw(get_cookie_file_path(username), 'w', cookies_content)
                console.print(f"✔ [bold green]Đã lưu Cookies mới cho {username}.[/bold green]")
                return cookies_content
            else:
                console.print("[bold red]Cookies không được để trống! Thử lại.[/bold red]")
                time.sleep(1)
                
        elif choice == '2': # Đăng nhập bằng tài khoản/mật khẩu
            username_login = Prompt.ask(f" ✈ [bold cyan]Nhập lại Username IG ({username})[/bold cyan]", default=username).strip()
            password = Prompt.ask(f" ✈ [bold cyan]Nhập Mật khẩu IG cho {username}[/bold cyan]", password=True).strip()
            
            new_cookies = ig_login(username_login, password)
            if new_cookies:
                console.print(f"✔ [bold green]Đã đăng nhập thành công cho {username}.[/bold green]")
                return new_cookies
            else:
                console.print("[bold red]Đăng nhập thất bại. Vui lòng thử lại.[/bold red]")
                time.sleep(2) 
        
        else:
            console.print("❌ [bold red]Lựa chọn không hợp lệ! Hãy nhập Enter, 1, hoặc 2.[/bold red]")
            time.sleep(1)

# --- GoLike API Functions ---

def chonacc(authorization: str):
    headers = get_base_headers(authorization)
    try:
        response = requests.get(INSTAGRAM_ACCOUNT_URL, headers=headers, timeout=5)
        response.raise_for_status()
        
        try:
            return response.json()
        except json.JSONDecodeError:
            return {"status": 500, "message": "API Error", "detail": f"Dữ liệu trả về không phải JSON: {response.text[:50]}..."}
            
    except requests.exceptions.RequestException as e:
        return {"status": 500, "message": f"Network Error: {e}"}
    except Exception as e:
        return {"status": 500, "message": f"Unexpected Error in chonacc: {e}"}

def nhannv(account_id: int, authorization: str):
    headers = get_base_headers(authorization)
    params = {
        'instagram_account_id': account_id,
        'data': 'null'
    }
    try:
        response = requests.get(GET_JOBS_URL, headers=headers, params=params, timeout=5)
        
        if response.status_code == 200:
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"status": 500, "message": "API Error: Invalid JSON (200 OK)", "raw_response": response.text}
        elif response.status_code == 400:
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"status": 400, "message": "Account error: Non-JSON 400 response", "detail": response.text[:50]}
        else:
            return {"status": response.status_code, "message": f"HTTP Error: {response.status_code}"}
            
    except requests.exceptions.RequestException as e:
        return {"status": 500, "message": f"Network Error: {e}"}
    except Exception as e:
        return {"status": 500, "message": f"Unexpected Error in nhannv: {e}"}

def hoanthanh(ads_id: str, account_id: int, authorization: str):
    headers = get_base_headers(authorization)
    data = {
        'instagram_users_advertising_id': ads_id,
        'instagram_account_id': account_id,
        'async': True,
        'data': None
    }
    
    try:
        response = requests.post(COMPLETE_JOBS_URL, headers=headers, json=data, timeout=10, verify=True) 
        
        if response.status_code == 200:
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"status": 500, "error": "Lỗi giải mã JSON (200 OK)"}
        else:
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"status": response.status_code, "error": f"Lỗi HTTP {response.status_code} - Dữ liệu không phải JSON."}

    except requests.exceptions.RequestException as e:
        return {'error': f'Không thể kết nối đến server hoặc timeout: {e}', 'status': 500} 
    except Exception as e:
        return {'error': f'Lỗi không mong muốn trong hoanthanh: {e}', 'status': 500}


def baoloi(ads_id: str, object_id: str, account_id: int, job_type: str, authorization: str):
    headers = get_base_headers(authorization)
    
    data1 = {
        'description': 'Tôi đã làm Job này rồi',
        'users_advertising_id': ads_id,
        'type': 'ads',
        'provider': 'instagram',
        'fb_id': account_id,
        'error_type': 6
    }
    try:
        requests.post(REPORT_URL, headers=headers, json=data1, timeout=5)
    except requests.exceptions.RequestException:
        pass

    data2 = {
        'ads_id': ads_id,
        'object_id': object_id,
        'account_id': account_id,
        'type': job_type
    }
    try:
        response = requests.post(SKIP_JOBS_URL, headers=headers, json=data2, timeout=5)
        
        try:
            return response.json()
        except json.JSONDecodeError:
            return {"status": 500, "message": f"Lỗi giải mã JSON (Skip Job): {response.text[:50]}..."}
            
    except requests.exceptions.RequestException as e:
        return {"status": 500, "message": f"Network Error on skip: {e}"}

# --- Telegram Functions MỚI (ĐÃ CẬP NHẬT) ---

def send_telegram_message(message: str):
    """Gửi tin nhắn thông báo qua Telegram."""
    # Chỉ cần kiểm tra Chat ID vì Token đã được Hardcode
    if not (GLOBAL_TELEGRAM_TOKEN and GLOBAL_TELEGRAM_TOKEN != "YOUR_HARDCODED_TELEGRAM_BOT_TOKEN_HERE" and GLOBAL_TELEGRAM_CHAT_ID):
        return False
        
    try:
        token = GLOBAL_TELEGRAM_TOKEN
        chat_id = GLOBAL_TELEGRAM_CHAT_ID

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'parse_mode': 'HTML', 
            'text': message
        }
        # Tăng timeout cho việc gửi Telegram
        response = requests.post(url, data=payload, timeout=15) 
        return response.status_code == 200
        
    except requests.exceptions.RequestException:
        return False
    except Exception:
        return False

def tool_get_chat_id():
    """Công cụ giúp người dùng lấy Chat ID từ Bot Token của họ (HOẶC BOT CHỦ)."""
    console.print("\n[bold yellow]═════════════ CÔNG CỤ TÌM KIẾM CHAT ID TELEGRAM ═════════════[/bold yellow]")
    
    # Sử dụng token cố định nếu có
    if GLOBAL_TELEGRAM_TOKEN and GLOBAL_TELEGRAM_TOKEN != "YOUR_HARDCODED_TELEGRAM_BOT_TOKEN_HERE":
        token_to_use = GLOBAL_TELEGRAM_TOKEN
        console.print(f"ℹ️ [bold white]Sử dụng Token Bot Chủ để tìm Chat ID. Hãy chat bất kỳ với Bot của bạn.[/bold white]")
    else:
        # Nếu chưa cố định token, yêu cầu người dùng nhập để tìm Chat ID
        console.print(f"⚠️ [bold red]Chủ Tool chưa cấu hình Token cố định![/bold red] [bold white]Bạn sẽ cần nhập Token của riêng bạn để tìm Chat ID.[/bold white]")
        token_to_use = Prompt.ask(f" ✈ [bold cyan]Nhập Telegram Bot Token để tìm Chat ID (tạm thời)[/bold cyan]").strip()
        if not token_to_use:
            console.print("[bold red]❌ Token không được để trống. Hủy bỏ.[/bold red]")
            time.sleep(2)
            return

    console.print("1. [bold yellow]CHAT VỚI BOT:[/bold yellow] Gửi bất kỳ tin nhắn nào (ví dụ: 'Xin chào') đến Bot.")
    
    try:
        # Dùng offset=-1 để chỉ lấy tin nhắn mới nhất
        url = f"https://api.telegram.org/bot{token_to_use}/getUpdates?offset=-1" 
        
        # Thử lấy tin nhắn trong 5 lần, mỗi lần cách nhau 5 giây
        for attempt in range(1, 6):
            console.print(f"⏳ [bold yellow]Đang thử tìm Chat ID (Lần {attempt}/5)... Đảm bảo bạn đã gửi tin nhắn đến bot.[/bold yellow]")
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                console.print(f"[bold red]❌ Lỗi API. Status Code: {response.status_code}. Thử lại sau 5s.[/bold red]")
                time.sleep(5)
                continue
                
            data = response.json()
            
            if data.get('ok') and data.get('result'):
                # Lấy tin nhắn mới nhất
                latest_update = data['result'][-1] 
                
                # Kiểm tra message (tin nhắn từ người dùng) hoặc channel_post
                if 'message' in latest_update:
                    chat_id = latest_update['message']['chat']['id']
                elif 'channel_post' in latest_update:
                     chat_id = latest_update['channel_post']['chat']['id']
                else:
                    console.print("[bold red]❌ Không tìm thấy tin nhắn mới trong phản hồi. Hãy gửi lại tin nhắn cho bot và thử lại.[/bold red]")
                    time.sleep(5)
                    continue
                
                console.print(f"\n🎉 [bold green]TÌM THẤY CHAT ID THÀNH CÔNG![/bold green]")
                console.print(f"   [bold magenta]Chat ID của bạn là:[/bold magenta] [bold yellow]{chat_id}[/bold yellow]")
                console.print("\n[bold white]⚠️ Hãy nhập Chat ID này vào phần cấu hình Telegram khi chạy BOT.[/bold white]")
                time.sleep(5)
                return
            
            time.sleep(5) # Đợi 5 giây trước khi thử lại

        console.print("\n[bold red]❌ KHÔNG THỂ TÌM THẤY CHAT ID sau 5 lần thử. Vui lòng kiểm tra lại:[/bold red]")
        console.print("   - Bạn đã chat với Bot chưa?")
        if 'token_to_use' not in locals():
            console.print("   - Token Bot bạn nhập có đúng không?")

    except requests.exceptions.RequestException as e:
        console.print(f"\n[bold red]❌ Lỗi kết nối hoặc timeout khi gọi API: {e}[/bold red]")
    except Exception as e:
        console.print(f"\n[bold red]❌ Lỗi không xác định: {e}[/bold red]")
    
    time.sleep(5)
    return

def get_telegram_config():
    """
    Xử lý việc nhập Telegram Chat ID, KHÔNG LƯU vào file.
    Chat ID chỉ có hiệu lực trong phiên chạy hiện tại.
    """
    global GLOBAL_TELEGRAM_CHAT_ID
    
    # 1. Kiểm tra Token đã được cấu hình chưa
    if GLOBAL_TELEGRAM_TOKEN == "YOUR_HARDCODED_TELEGRAM_BOT_TOKEN_HERE":
        console.print("\n⚠️ [bold red]Chủ Tool: Token Telegram chưa được cấu hình. Bỏ qua thông báo Telegram.[/bold red]")
        return False
        
    # Loại bỏ phần đọc/ghi từ file theo yêu cầu người dùng
    
    console.print("\n[bold yellow]════════════════════════════════════════════════[/bold yellow]")
    try:
        confirm = Confirm.ask(f" ✈ [bold yellow]Bạn có muốn nhận thông báo qua Telegram trong phiên này không? (y/n)[/bold yellow]", default=True)
    except Exception:
        confirm = input("Bạn có muốn nhận thông báo qua Telegram trong phiên này không? (y/n, mặc định: y): ").lower() != 'n'
    
    if not confirm:
        console.print(f"✔ [bold blue]Bỏ qua cấu hình Telegram cho phiên này.[/bold blue]")
        return False

    console.print("\n[bold cyan]CẤU HÌNH THÔNG BÁO TELEGRAM (KHÔNG LƯU LẠI)[/bold cyan]")
    console.print(f"ℹ️ [bold white]Bot đã được cấu hình sẵn. Bạn chỉ cần nhập [bold yellow]Chat ID[/bold yellow] của mình.[/bold white]")
    console.print(f"   [bold yellow]Chat ID:[/bold yellow] Là mã số bạn lấy được sau khi chạy chức năng [bold magenta]2. Công cụ tìm Chat ID Telegram[/bold magenta] ở Menu Chính.")
    
    while True:
        new_chat_id = Prompt.ask(f" ✈ [bold cyan]Nhập Telegram Chat ID của bạn[/bold cyan]").strip()
        if new_chat_id:
            # KHÔNG LƯU VÀO FILE THEO YÊU CẦU
            GLOBAL_TELEGRAM_CHAT_ID = new_chat_id
            break
        console.print("[bold red]Chat ID không được để trống![/bold red]")
        
    console.print(f"✔ [bold green]Đã nhập Chat ID. Thông báo sẽ được gửi trong phiên này.[/bold green]")
    time.sleep(1)
    return True

# --- Instagram Interaction Functions (Thêm logic tạm ngưng & Notification) ---

def extract_csrftoken(cookies_str):
    """Trích xuất csrftoken từ chuỗi cookies."""
    for cookie in cookies_str.split(';'):
        if 'csrftoken=' in cookie.strip():
            return cookie.split('=')[1].strip()
    return None

def get_ig_headers(cookies: str, referer: str = "https://www.instagram.com/"):
    """Tạo headers cho API Instagram. Đã cập nhật User-Agent."""
    token = extract_csrftoken(cookies)
    
    IG_HEADERS = {
        'authority': 'i.instagram.com',
        'accept': '*/*',
        'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
        'content-type': 'application/x-www-form-urlencoded',
        'cookie': cookies,
        'origin': 'https://www.instagram.com',
        'referer': referer,
        'user-agent': GLOBAL_USER_AGENT, 
        'x-csrftoken': token if token else '',
        'x-ig-app-id': '936619743392459',
        'x-instagram-ajax': '1006309104',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
    }
    return IG_HEADERS

def get_cookie_string(s: requests.Session):
    """Chuyển đối tượng CookieJar thành chuỗi cookies."""
    return "; ".join([f"{k}={v}" for k, v in s.cookies.items()])

def handle_follow_job(account_info: dict, object_id: str):
    """Thực hiện nhiệm vụ Follow và trả về (thành công/thất bại, cookies mới)."""
    cookies = account_info['cookies']
    username = account_info['username']
    headers = get_ig_headers(cookies)
    url = f"https://i.instagram.com/api/v1/web/friendships/{object_id}/follow/"
    
    session = requests.Session()
    try:
        for c in cookies.split('; '):
            if '=' in c:
                name, value = c.split('=', 1)
                session.cookies.set(name, value)
                
        response = session.post(url, headers=headers, data=None, timeout=10) 
        
        # Thêm logic tạm ngưng nếu bị block/yêu cầu đăng nhập lại
        if 'login_required' in response.text or response.status_code == 403:
             console.print(f"❌ [bold red]Follow thất bại: Tài khoản [bold cyan]{username}[/bold cyan] bị block hoặc cần đăng nhập lại. Tạm ngưng {LOCK_TIME_SECONDS/60} phút.[/bold red]")
             account_info['is_locked'] = True
             account_info['lock_until'] = time.time() + LOCK_TIME_SECONDS
             
             # 📢 THÔNG BÁO TELEGRAM: CHECKPOINT/LOGIN REQUIRED
             telegram_message = f"""
🚨 <b>CẢNH BÁO: NICK CHECKPOINT/LOGIN REQUIRED</b> 🚨
- Tài khoản: <b><code>{username}</code></b>
- Loại Job: FOLLOW
- Trạng thái: Cần xác minh/đăng nhập lại.
- Hành động: Đã tạm dừng tài khoản này ({LOCK_TIME_SECONDS // 60} phút).
"""
             send_telegram_message(telegram_message)
             return False, cookies

        try:
            response_json = response.json()
        except json.JSONDecodeError:
            console.print(f"❌ [bold red]Follow thất bại: Lỗi phản hồi không phải JSON ({response.status_code}).[/bold red]")
            return False, cookies
        
        if response_json.get('status') == 'ok':
            console.print("✅ [bold green]Follow thành công[/bold green]")
            new_cookies = get_cookie_string(session)
            return True, new_cookies
        else:
            console.print(f"❌ [bold red]Follow thất bại:[/bold red] [bold yellow]{response.text[:50]}...[/bold yellow]")
            return False, cookies

    except requests.exceptions.TooManyRedirects as e:
        # ❗ LỖI SỬA CHỮA ĐỂ KHẮC PHỤC SỰ CỐ "EXCEEDED 30 REDIRECTS"
        console.print(f"❌ [bold red]Follow thất bại: Tài khoản [bold cyan]{username}[/bold cyan] bị lỗi Redirects (>30). Cần cập nhật Cookies. Tạm ngưng {LOCK_TIME_SECONDS/60} phút.[/bold red]")
        account_info['is_locked'] = True
        account_info['lock_until'] = time.time() + LOCK_TIME_SECONDS
        
        # 📢 THÔNG BÁO TELEGRAM: REDIRECTS LOCK
        telegram_message = f"""
🚨 <b>CẢNH BÁO: LỖI REDIRECT/CẦN CẬP NHẬT COOKIES</b> 🚨
- Tài khoản: <b><code>{username}</code></b>
- Loại Job: FOLLOW
- Trạng thái: Lỗi Redirect (>30). Cần cập nhật Cookies.
- Hành động: Đã tạm dừng tài khoản này ({LOCK_TIME_SECONDS // 60} phút).
"""
        send_telegram_message(telegram_message)
        return False, cookies
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        console.print(f"[bold red]Lỗi nghiêm trọng khi Follow (Network/Unknown):[/bold red] [bold yellow]{e}[/bold yellow]")
        return False, cookies

def handle_like_job(account_info: dict, media_id: str, link: str):
    """Thực hiện nhiệm vụ Like và trả về (thành công/thất bại, cookies mới)."""
    cookies = account_info['cookies']
    username = account_info['username']
    headers = get_ig_headers(cookies, referer=link)
    headers['authority'] = 'www.instagram.com'
    headers['x-ig-app-id'] = '936619743392459'
    
    url = f"https://www.instagram.com/web/likes/{media_id}/like/"
    
    session = requests.Session()
    try:
        for c in cookies.split('; '):
            if '=' in c:
                name, value = c.split('=', 1)
                session.cookies.set(name, value)
                
        response = session.post(url, headers=headers, data=None, timeout=10) 

        # Thêm logic tạm ngưng nếu bị block/yêu cầu đăng nhập lại
        if 'login_required' in response.text or response.status_code == 403:
             console.print(f"❌ [bold red]Like thất bại: Tài khoản [bold cyan]{username}[/bold cyan] bị block hoặc cần đăng nhập lại. Tạm ngưng {LOCK_TIME_SECONDS/60} phút.[/bold red]")
             account_info['is_locked'] = True
             account_info['lock_until'] = time.time() + LOCK_TIME_SECONDS
             
             # 📢 THÔNG BÁO TELEGRAM: CHECKPOINT/LOGIN REQUIRED
             telegram_message = f"""
🚨 <b>CẢNH BÁO: NICK CHECKPOINT/LOGIN REQUIRED</b> 🚨
- Tài khoản: <b><code>{username}</code></b>
- Loại Job: LIKE
- Trạng thái: Cần xác minh/đăng nhập lại.
- Hành động: Đã tạm dừng tài khoản này ({LOCK_TIME_SECONDS // 60} phút).
"""
             send_telegram_message(telegram_message)
             return False, cookies
        
        try:
            response_json = response.json()
        except json.JSONDecodeError:
            response_json = {}
            
        if response.status_code == 200 and response_json.get('status') == 'ok':
            console.print("✅ [bold green]Like thành công[/bold green]")
            new_cookies = get_cookie_string(session)
            return True, new_cookies
        elif response.status_code == 400 and 'Sorry, this photo has been deleted' in response.text:
            console.print("❌ [bold red]PHOTO HAS BEEN DELETED[/bold red]")
            return False, cookies
        else:
            console.print(f"❌ [bold red]ERROR (Like):[/bold red] [bold yellow]Status {response.status_code}, Response: {response.text[:50]}...[/bold yellow]")
            return False, cookies

    except requests.exceptions.TooManyRedirects as e:
        # ❗ LỖI SỬA CHỮA ĐỂ KHẮC PHỤC SỰ CỐ "EXCEEDED 30 REDIRECTS"
        console.print(f"❌ [bold red]Like thất bại: Tài khoản [bold cyan]{username}[/bold cyan] bị lỗi Redirects (>30). Cần cập nhật Cookies. Tạm ngưng {LOCK_TIME_SECONDS/60} phút.[/bold red]")
        account_info['is_locked'] = True
        account_info['lock_until'] = time.time() + LOCK_TIME_SECONDS
        
        # 📢 THÔNG BÁO TELEGRAM: REDIRECTS LOCK
        telegram_message = f"""
🚨 <b>CẢNH BÁO: LỖI REDIRECT/CẦN CẬP NHẬT COOKIES</b> 🚨
- Tài khoản: <b><code>{username}</code></b>
- Loại Job: LIKE
- Trạng thái: Lỗi Redirect (>30). Cần cập nhật Cookies.
- Hành động: Đã tạm dừng tài khoản này ({LOCK_TIME_SECONDS // 60} phút).
"""
        send_telegram_message(telegram_message)
        return False, cookies
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        # Lỗi Exceeded 30 redirects sẽ nằm ở đây nếu không có khối except TooManyRedirects riêng.
        console.print(f"[bold red]CÓ LỖI XẢY RA!!! (Network/Unknown):[/bold red] [bold yellow]{e}[/bold yellow]")
        return False, cookies

# --- Main Logic ---

def dsacc(chontk_Instagram, authorization: str):
    """Hiển thị danh sách và cho phép chọn nhiều tài khoản Instagram."""
    global ACCOUNTS_LIST
    
    if chontk_Instagram.get("status") != 200:
        console.print(f"❌ [bold red]Authorization hoặc T sai, hoặc GoLike API lỗi. Vui lòng kiểm tra lại![/bold red]")
        error_detail = chontk_Instagram.get('message', 'Lỗi không xác định')
        console.print(f"[bold red]Chi tiết lỗi: {error_detail}[/bold red]")
        raw_response = chontk_Instagram.get('raw_response', None)
        if raw_response:
             console.print(f"[bold red]Raw Response API: {raw_response[:100]}...[/bold red]")
        console.print("[bold yellow]════════════════════════════════════════════════[/bold red]")
        sys.exit(1)
            
    list_all_acc = chontk_Instagram["data"]
    
    while True:
        display_banner()
        display_current_info(authorization)
        
        acc_table = Table(title="[bold green]DANH SÁCH ACC INSTAGRAM[/bold green]", border_style="bold green", show_lines=True)
        acc_table.add_column("STT", justify="center", style="bold yellow")
        acc_table.add_column("Username", style="bold white")
        acc_table.add_column("Trạng Thái", justify="center", style="bold white")

        for i, acc in enumerate(list_all_acc):
            status_text = "[bold green]Hoạt Động[/bold green]"
            if acc.get('status') != 1:
                status_text = "[bold red]Chưa Duyệt[/bold red]"
            
            acc_table.add_row(
                str(i + 1),
                acc['instagram_username'],
                status_text
            )
        
        console.print(Panel(
            acc_table, 
            border_style="green",
            title_align="center",
            box=HEAVY_EDGE
        ))
        
        selection = Prompt.ask(f" ✈ [bold cyan]Nhập STT các tài khoản muốn chạy (VD: 1,3,4) hoặc 'all'[/bold cyan]").strip().lower()
        
        selected_indices = []
        if selection == 'all':
            selected_indices = range(len(list_all_acc))
        else:
            try:
                indices = [int(i.strip()) - 1 for i in selection.split(',') if i.strip().isdigit()]
                for index in indices:
                    if 0 <= index < len(list_all_acc):
                        selected_indices.append(index)
            except:
                console.print("❌ [bold red]Lựa chọn không hợp lệ. Vui lòng nhập đúng định dạng (VD: 1,3,4 hoặc all).[/bold red]")
                time.sleep(1)
                continue
        
        if not selected_indices:
            console.print("❌ [bold red]Vui lòng chọn ít nhất một tài khoản hợp lệ.[/bold red]")
            time.sleep(1)
            continue
            
        ACCOUNTS_LIST.clear()
        
        # 2. Xử lý Cookies cho từng tài khoản đã chọn
        console.print("\n[bold yellow]════════════════════════════════════════════════[/bold yellow]")
        console.print("[bold cyan]BẮT ĐẦU CẤU HÌNH COOKIES CHO TỪNG TÀI KHOẢN...[/bold cyan]")
        
        for index in selected_indices:
            acc_info = list_all_acc[index]
            username = acc_info['instagram_username']
            golike_id = acc_info['id']
            
            cookies = get_cookies_for_account(username)
            
            if cookies:
                ACCOUNTS_LIST.append({
                    "id": golike_id,
                    "username": username,
                    "cookies": cookies,
                    "fail_count": 0,
                    "success_count": 0,
                    "is_locked": False, 
                    "lock_until": 0 
                })
                console.print(f"✔ [bold green]Đã thêm tài khoản {username} vào danh sách chạy.[/bold green]")
            else:
                console.print(f"❌ [bold red]Bỏ qua tài khoản {username} (Không có Cookies/Bị Bỏ qua).[/bold red]")
            
            time.sleep(1)
            
        if ACCOUNTS_LIST:
            console.print(f"\n[bold green]✅ Đã chọn [bold yellow]{len(ACCOUNTS_LIST)}[/bold yellow] tài khoản để chạy luân phiên.[/bold green]")
            time.sleep(2)
            break
        else:
            console.print("\n[bold red]Danh sách tài khoản chạy trống. Vui lòng chọn lại![/bold red]")
            time.sleep(2)
            
    return ACCOUNTS_LIST

def get_user_settings():
    """Nhận cài đặt từ người dùng, ưu tiên sử dụng cấu hình tự động."""
    
    current_config = load_config()
    
    if current_config:
        # FIX CĂN CHỈNH: BỎ justify="left" để rich tự căn chỉnh, dùng \n để ngắt dòng
        config_status = Text() 
        config_status.append("✅ Đã tìm thấy file config.json.\n")
        config_status.append(f" ✈ Delay (giây): {current_config['delay']}\n")
        config_status.append(f" ✈ Nhận tiền lần 2: {'Có' if current_config['lannhan_lan2'] else 'Không'}\n")
        config_status.append(f" ✈ Job Fail Limit: {current_config['doiacc_fail_limit']}\n")
        config_status.append(f" ✈ Job Success Limit: {current_config['job_success_limit']}\n")
        config_status.append(f" ✈ Tỉ lệ Job (Like/Follow): {current_config['job_ratio']}\n")
        config_status.append(f" ✈ Chế độ Job: {'Follow' if current_config['chedo_job'] == 1 else 'Like' if current_config['chedo_job'] == 2 else 'Cả Hai'} (Code: {current_config['chedo_job']})")
        
        console.print(Panel(
            config_status,
            title=trim_title_for_panel("[bold cyan]⚙️ CẤU HÌNH TỰ ĐỘNG ĐÃ LƯU ⚙️[/bold cyan]"), # SỬ DỤNG HÀM CẮT TIÊU ĐỀ
            border_style="cyan",
            box=HEAVY_EDGE,
            title_align="center"
        ))
        
        use_config = Confirm.ask(f" ✈ [bold yellow]Bạn có muốn sử dụng cấu hình này? (y/n)[/bold yellow]", default=True)
        
        if use_config:
            
            # Chuyển đổi chedo_job sang định dạng lam
            lam = []
            if current_config['chedo_job'] == 1:
                lam = ["follow"]
            elif current_config['chedo_job'] == 2:
                lam = ["like"]
            elif current_config['chedo_job'] == 12:
                lam = ["follow", "like"]
            
            # Trả về các giá trị đã load
            console.print("✔ [bold green]Sử dụng cấu hình tự động.[/bold green]")
            return (
                current_config['delay'], 
                "y" if current_config['lannhan_lan2'] else "n", 
                current_config['doiacc_fail_limit'], 
                lam, 
                current_config['job_success_limit'], 
                current_config['job_ratio']
            )
            
    # Nếu không có config, hoặc người dùng chọn không dùng config
    console.print("[bold yellow]════════════════════════════════════════════════[/bold yellow]")
    
    while True:
        try:
            delay = int(Prompt.ask(f" ✈ [bold cyan]Nhập thời gian làm job (giây) (tối thiểu 3s)[/bold cyan]", default="5").strip())
            if delay >= 3:
                break
            console.print("[bold red]Thời gian phải lớn hơn hoặc bằng 3 giây![/bold red]")
        except ValueError:
            console.print("[bold red]Sai định dạng!!! Vui lòng nhập số.[/bold red]")

    lannhan_confirm = Confirm.ask(f" ✈ [bold yellow]Nhận tiền lần 2 nếu lần 1 fail? (y/n)[/bold yellow]", default=True)
    lannhan = "y" if lannhan_confirm else "n"

    while True:
        try:
            doiacc = int(Prompt.ask(f" ✈ [bold cyan]Số job fail để chuyển sang tài khoản Instagram khác (>= 1)[/bold cyan]", default="5").strip())
            if doiacc >= 1:
                break
            console.print("[bold red]Số job fail phải là số nguyên dương (>= 1)![/bold red]")
        except ValueError:
            console.print("[bold red]Nhập vào 1 số!!![/bold red]")
            
    # --- Cài đặt Giới hạn Job Thành công ---
    while True:
        try:
            job_limit = int(Prompt.ask(f" ✈ [bold cyan]Số job thành công tối đa trước khi đổi tài khoản (>= 1)[/bold cyan]", default="10").strip())
            if job_limit >= 1:
                break
            console.print("[bold red]Giới hạn job phải là số nguyên dương (>= 1)![/bold red]")
        except ValueError:
            console.print("[bold red]Nhập vào 1 số!!![/bold red]")
    # ----------------------------------------
    
    # --- Nhập Tỉ lệ Like/Follow ---
    while True:
        job_ratio = Prompt.ask(f" ✈ [bold cyan]Nhập tỉ lệ Like,Follow (VD: 1,2 = 1 like rồi 2 follow)[/bold cyan]", default="1,1").strip()
        try:
            parts = [int(p.strip()) for p in job_ratio.split(',') if p.strip().isdigit()]
            # Kiểm tra phải có 2 phần, và tổng phải lớn hơn 0
            if len(parts) == 2 and parts[0] >= 0 and parts[1] >= 0 and (parts[0] + parts[1] > 0):
                break
            console.print("[bold red]Tỉ lệ không hợp lệ! Vui lòng nhập 2 số nguyên không âm, tổng lớn hơn 0 (VD: 1,1).[/bold red]")
        except ValueError:
            console.print("[bold red]Sai định dạng! Vui lòng nhập 2 số cách nhau bằng dấu phẩy (VD: 1,1).[/bold red]")
    
    # --- Cấu hình Nhiệm vụ (Chọn loại job) ---
    config_options = Text(justify="left")
    config_options.append(f" ✈ Nhập 1 : Chỉ nhận nhiệm vụ Follow\n")
    config_options.append(f" ✈ Nhập 2 : Chỉ nhận nhiệm vụ Like\n")
    config_options.append(f" ✈ Nhập 12 : Kết hợp cả Like và Follow theo tỉ lệ {job_ratio}\n")
    
    console.print(Panel(
        config_options,
        title=trim_title_for_panel("[bold yellow]⚙️ CẤU HÌNH NHIỆM VỤ ⚙️[/bold yellow]"),
        border_style="yellow",
        box=HEAVY_EDGE,
        title_align="center"
    ))

    while True:
        try:
            chedo = int(Prompt.ask(f" ✈ [bold cyan]Chọn lựa chọn[/bold cyan]").strip())
            if chedo in [1, 2, 12]:
                break
            else:
                console.print("[bold red]Chỉ được nhập 1, 2 hoặc 12![/bold red]")
        except ValueError:
            console.print("[bold red]Nhập vào 1 số!!![/bold red]")

    lam = []
    if chedo == 1:
        lam = ["follow"]
    elif chedo == 2:
        lam = ["like"]
    elif chedo == 12:
        lam = ["follow", "like"]
        
    # --- LƯU CẤU HÌNH MỚI ---
    new_config = {
        "delay": delay,
        "lannhan_lan2": lannhan_confirm,
        "doiacc_fail_limit": doiacc,
        "job_success_limit": job_limit,
        "job_ratio": job_ratio,
        "chedo_job": chedo
    }
    save_config(new_config)
    console.print("✔ [bold green]Đã lưu cấu hình mới vào config.json.[/bold green]")
    time.sleep(1)
    # -------------------------
        
    return delay, lannhan, doiacc, lam, job_limit, job_ratio

# --- HÀM MAIN_LOOP ĐÃ SỬA LỖI LOGIC BỎ QUA JOB KHÔNG CẦN THIẾT VÀ THÊM NOTIFICATION ---
def main_loop(accounts: list, delay: int, lannhan: str, doiacc_limit: int, lam: list, authorization: str, job_success_limit: int, job_ratio: str): 
    """Vòng lặp xử lý nhiệm vụ chính, chạy luân phiên giữa các tài khoản và loại job."""
    
    dem = 0
    tong = 0
    
    account_cycler = itertools.cycle(accounts)
    job_cycler = create_job_cycler(job_ratio, lam) 
    
    log_table = Table(
        title="[bold magenta]📜 BẢNG LOG NHIỆM VỤ 📜[/bold magenta]", 
        border_style="bold magenta",
        show_lines=True 
    )
    log_table.add_column("STT", justify="center", style="bold yellow")
    log_table.add_column("Thời gian", justify="center", style="bold white")
    log_table.add_column("Tài khoản", justify="center", style="bold cyan")
    log_table.add_column("Status", justify="center", style="bold green")
    log_table.add_column("Xu", justify="center", style="bold magenta")
    log_table.add_column("Tổng", justify="center", style="bold yellow")
    
    spinner = itertools.cycle([
        "⚡", "🚀", "💻", "🔥", "⏳",
        "🛠️", "🛰️", "🔒", "🔓", "📡",
        "🧩", "🔧", "✨", "⚙️", "🧨",
        "🪄", "👾", "🕶️", "🎯", "💣",
        "🖥️"
    ])
    colors = [
        "red", "magenta", "cyan", "green", "yellow", "blue", "white"
    ]
    
    def display_ui_and_log():
        """Hàm dùng để in lại toàn bộ UI và Log"""
        clear_screen()
        display_banner()
        display_current_info(authorization)
        
        console.print("[bold yellow]════════════════════════════════════════════════[/bold yellow]")
        
        console.print(Panel(
            log_table, 
            border_style="magenta",
            title_align="center",
            box=HEAVY_EDGE
        ))

    display_ui_and_log()
    
    while True:
        current_acc = next(account_cycler)
        account_id = current_acc['id']
        username = current_acc['username']
        current_cookies = current_acc['cookies']
        
        # 1. Check LOCK status 
        if current_acc['is_locked']:
            if time.time() < current_acc['lock_until']:
                remaining_time = int(current_acc['lock_until'] - time.time())
                console.print(f"⚠️ [bold red]Tài khoản [bold cyan]{username}[/bold cyan] đang bị tạm ngưng. Mở lại sau {remaining_time}s. Chuyển acc...[/bold red]")
                time.sleep(1)
                continue
            else:
                # Mở khóa tài khoản
                current_acc['is_locked'] = False
                current_acc['lock_until'] = 0
                console.print(f"✅ [bold green]Tài khoản [bold cyan]{username}[/bold cyan] đã hết thời gian tạm ngưng. Bắt đầu lại...[/bold green]")
                time.sleep(1)
                
        # 2. Check fail_count và chuyển tài khoản (nếu cần)
        if current_acc['fail_count'] >= doiacc_limit:
            fail_message = Text("\nJob fail của ", style="bold red")
            fail_message.append(username, style="bold cyan")
            fail_message.append(f" đã đạt giới hạn (", style="bold red")
            fail_message.append(f"{doiacc_limit}", style="bold yellow")
            fail_message.append(")!", style="bold red")
            fail_message.append(" Bỏ qua tài khoản này trong 1 lượt.", style="bold red")
            console.print(fail_message)

            current_acc['fail_count'] = 0 
            time.sleep(1)
            continue 
            
        # --- Check Job Thành công Limit ---
        if current_acc['success_count'] >= job_success_limit:
            success_message = Text("\n✔ Tài khoản ", style="bold yellow")
            success_message.append(username, style="bold cyan")
            success_message.append(" đã hoàn thành ", style="bold yellow")
            success_message.append(str(job_success_limit), style="bold green")
            success_message.append(" jobs. Đổi sang tài khoản tiếp theo.", style="bold yellow")
            console.print(success_message)
            
            # 📢 THÔNG BÁO TELEGRAM: ĐẠT GIỚI HẠN JOB THÀNH CÔNG
            telegram_limit_message = f"""
📈 <b>ĐẠT GIỚI HẠN JOB THÀNH CÔNG</b>
- Tài khoản: <code>{username}</code>
- Trạng thái: Đã hoàn thành {job_success_limit} jobs.
- Hành động: Tự động chuyển sang tài khoản tiếp theo.
"""
            send_telegram_message(telegram_limit_message)

            current_acc['success_count'] = 0 # Reset count
            time.sleep(1)
            continue
        # ----------------------------------

        # Lấy loại job mong muốn theo chu kỳ (Vẫn lấy để duy trì thứ tự luân phiên)
        desired_job_type = next(job_cycler)
        
        # 3. Get Job - Sử dụng console.status
        with console.status(f"[bold white]Đang Tìm NV [bold green]{desired_job_type}[/bold green] cho [bold cyan]{username}[/bold cyan]:>[/bold white] [bold yellow]Tổng xu: {tong}[/bold yellow]") as status:
            try:
                # Gọi API nhận job, API sẽ trả về job đầu tiên nó tìm thấy (Like hoặc Follow)
                nhanjob = safe_dict_check(nhannv(account_id, authorization), context="Get Job")
            except Exception as e:
                nhanjob = {"status": 500, "message": f"Failed to get job (exception outside of nhannv): {e}"}
            
            if nhanjob.get("critical_safe_check_fail"):
                 status.update(f"❌ [bold red]Lỗi dữ liệu nghiêm trọng cho [bold cyan]{username}[/bold cyan]. Bỏ qua.[/bold red]")
                 time.sleep(1)
                 continue
            
            job_data = nhanjob.get("data")
            if nhanjob.get("status") != 200 or not job_data:
                # 📢 THÔNG BÁO TELEGRAM: HẾT JOB
                if nhanjob.get("status") == 400:
                    status.update(f"❌ [bold red]Hết Job cho [bold cyan]{username}[/bold cyan]: [bold yellow]{nhanjob.get('detail', nhanjob.get('message', 'Lỗi không rõ'))}. Chuyển acc...[/bold yellow]")
                else:
                    status.update(f"[bold yellow]Không tìm thấy nhiệm vụ cho [bold cyan]{username}[/bold cyan]. Chuyển acc...[/bold yellow]")
                time.sleep(1)
                continue
                
            ads_id = job_data.get("id")
            link = job_data.get("link")
            object_id = job_data.get("object_id")
            loai = job_data.get("type") # Loại job mà GoLike thực sự trả về
            
            # ❗ PHẦN SỬA LỖI QUAN TRỌNG: BỎ QUA JOB KHÔNG ĐƯỢC CHỌN
            if loai not in lam:
                try:
                    baoloi(ads_id, object_id, account_id, loai, authorization)
                    status.update(f"[bold red]Đã bỏ qua job {loai} (Không nằm trong chế độ đã chọn {', '.join(lam)})! Tiếp tục tìm {desired_job_type}...[/bold red]")
                    time.sleep(1)
                    continue
                except Exception:
                    pass
            # -------------------------------------------------------------
                
            # 4. Execute Job (Follow/Like)
            status.update(f"[bold white]Đã nhận job [bold magenta]{loai}[/bold magenta] ({object_id}). Đang thực hiện bằng [bold cyan]{username}[/bold cyan]...[/bold white]")
            success = False
            new_cookies_from_job = current_cookies 
            
            if loai == "follow":
                success, new_cookies_from_job = handle_follow_job(current_acc, object_id)
            elif loai == "like":
                # ---- XỬ LÝ DỮ LIỆU JOB LIKE (ĐÃ SỬA LỖI TRÍCH XUẤT media_id) ----
                obj_data = job_data.get("object_data", {})
                
                if isinstance(obj_data, str):
                    try:
                        obj_data = json.loads(obj_data)
                    except json.JSONDecodeError:
                        console.print(f"⚠️ [bold red]Bỏ qua job like: object_data là chuỗi nhưng không phải JSON hợp lệ. object_data: {obj_data[:50]}...[/bold red]")
                        current_acc['fail_count'] += 1
                        time.sleep(1)
                        continue
                
                if not isinstance(obj_data, dict):
                    obj_data = {}

                media_id = None
                try:
                    media_id = obj_data.get("pk") or object_id
                except Exception:
                    media_id = object_id

                if media_id:
                    success, new_cookies_from_job = handle_like_job(current_acc, media_id, link)
                else:
                    console.print("❌ [bold red]Lỗi: Không tìm thấy media_id cho job like.[/bold red]")
                    success = False
            
            # CẬP NHẬT COOKIES VÀO CẤU TRÚC ACCOUNTS_LIST VÀ FILE
            if new_cookies_from_job != current_cookies:
                current_acc['cookies'] = new_cookies_from_job
                safe_file_rw(get_cookie_file_path(username), 'w', new_cookies_from_job)
                
            # If IG job failed (và không bị khóa), skip GoLike job
            if not success and not current_acc['is_locked']: 
                try:
                    baoloi(ads_id, object_id, account_id, loai, authorization)
                    status.update(f"❌ [bold red]Đã báo lỗi (Fail IG) và bỏ qua job {loai}! Tài khoản [bold cyan]{username}[/bold cyan] fail +1.[/bold red]")
                    
                    # 📢 THÔNG BÁO TELEGRAM: LỖI THỰC THI JOB
                    telegram_job_fail_message = f"""
❌ <b>LỖI THỰC THI JOB IG</b>
- Tài khoản: <code>{username}</code>
- Loại Job: {loai.upper()}
- ID Job: <code>{object_id}</code>
- Lý do: Thực hiện trên IG thất bại/Job đã bị xóa.
"""
                    send_telegram_message(telegram_job_fail_message)

                    current_acc['fail_count'] += 1
                    time.sleep(1)
                    continue
                except Exception:
                    status.update(f"❌ [bold red]Lỗi khi báo lỗi job![/bold red]")
                    current_acc['fail_count'] += 1
                    time.sleep(1)
                    continue
            
            # Nếu job thất bại do bị khóa tài khoản (checkpoint), chỉ cần continue
            if current_acc['is_locked']:
                 continue
                 
            # 5. Delay
            for i in range(delay, 0, -1):
                icon = next(spinner)
                color = colors[i % len(colors)]
                status.update(f"[bold {color}]{icon} Đang Nhận Tiền {i:02d}s còn lại...[/bold {color}]")
                time.sleep(1)
            
            # 6. Complete Job (Nhận tiền)
            ok = False
            nhantien = {}
            for lan in range(1, 3):
                if lan == 2 and lannhan == "n":
                    break
                
                status.update(f"[bold white]Đang Nhận Tiền Lần {lan}:>[/bold white]")
                try:
                    nhantien = safe_dict_check(hoanthanh(ads_id, account_id, authorization), context="Complete Job")
                except Exception as e:
                    nhantien = {"status": 500, "message": f"Lỗi khi hoàn thành job (exception): {e}"} 
                
                if nhantien.get("critical_safe_check_fail"):
                    status.update(f"❌ [bold red]Lỗi dữ liệu nghiêm trọng khi nhận tiền. Bỏ qua.[/bold red]")
                    break

                if nhantien.get("status") == 200 and nhantien.get("data"):
                    ok = True
                    dem += 1
                    tien = nhantien["data"]["prices"]
                    tong += tien
                    local_time = time.strftime("%H:%M:%S")
                    
                    log_table.add_row(
                        str(dem),
                        local_time,
                        f"[bold cyan]{username}[/bold cyan]",
                        "[bold green]SUCCESS[/bold green]", 
                        f"[bold magenta]+{tien}[/bold magenta]", 
                        f"[bold yellow]{tong}[/bold yellow]"
                    )
                    
                    # 📢 THÔNG BÁO TELEGRAM: HOÀN THÀNH JOB
                    telegram_success_message = f"""
✅ <b>HOÀN THÀNH JOB THÀNH CÔNG!</b>
- Tài khoản: <code>{username}</code>
- Loại Job: {loai.upper()}
- Tiền Nhận: <b>+{tien} Xu</b>
- Tổng Xu: <b>{tong} Xu</b>
"""
                    send_telegram_message(telegram_success_message)

                    display_ui_and_log()
                    current_acc['fail_count'] = 0 
                    current_acc['success_count'] += 1
                    break
                else:
                    if lan == 1 and lannhan == "y":
                        time.sleep(2)
                        continue
                    break 

            if not ok:
                try:
                    baoloi(ads_id, object_id, account_id, loai, authorization)
                    status.update(f"❌ [bold red]Đã bỏ qua job (Lỗi nhận tiền)! Tài khoản [bold cyan]{username}[/bold cyan] fail +1.[/bold red]")
                    
                    # 📢 THÔNG BÁO TELEGRAM: LỖI NHẬN TIỀN
                    error_detail = nhantien.get('error', nhantien.get('message', 'Lỗi không rõ'))
                    telegram_complete_fail_message = f"""
❌ <b>LỖI NHẬN TIỀN</b>
- Tài khoản: <code>{username}</code>
- Loại Job: {loai.upper()}
- ID Job: <code>{object_id}</code>
- Lý do: {error_detail}
- Hành động: Đã báo lỗi và bỏ qua job.
"""
                    send_telegram_message(telegram_complete_fail_message)

                    current_acc['fail_count'] += 1
                    time.sleep(1)
                except Exception:
                    status.update("[bold red]❌ Lỗi khi báo lỗi job![/bold red]")
                    current_acc['fail_count'] += 1
                    time.sleep(1)

# --- MENU CHÍNH ĐÃ SỬA LỖI PANEL ---

def display_main_menu_and_get_choice():
    """Hiển thị menu chính và lấy lựa chọn của người dùng."""
    console.clear()
    display_banner()
    
    # Sửa lỗi: Gộp các dòng menu vào một đối tượng Text duy nhất
    menu_text = Text()
    menu_text.append("1. Khởi động BOT GoLike IG\n", style="bold green")
    menu_text.append("2. Công cụ tìm Chat ID Telegram\n", style="bold magenta")
    menu_text.append("3. Thoát", style="bold red")

    console.print(Panel(
        menu_text, # Chỉ truyền một đối tượng nội dung
        title="[bold yellow]MENU CHÍNH[/bold yellow]", # Sử dụng tham số title cho tiêu đề
        border_style="cyan"
    ))
    return Prompt.ask("Chọn chức năng bạn muốn chạy", choices=['1', '2', '3'])

if __name__ == "__main__":
    
    # KHI CHẠY, SẼ KIỂM TRA LỖI HARDCODE TOKEN TRƯỚC
    if GLOBAL_TELEGRAM_TOKEN == "YOUR_HARDCODED_TELEGRAM_BOT_TOKEN_HERE":
        console.print("\n\n⚠️ [bold red]LỖI CẤU HÌNH NGHIÊM TRỌNG (CHỦ TOOL):[/bold red]")
        console.print("[bold yellow]Bạn chưa thay Token Bot chủ trong biến GLOBAL_TELEGRAM_TOKEN. [/bold yellow]")
        console.print("[bold yellow]Thông báo Telegram sẽ không hoạt động cho đến khi bạn sửa lỗi này.[/bold yellow]")
        time.sleep(5)
    
    while True:
        choice = display_main_menu_and_get_choice()

        if choice == '3':
            console.print("[bold red]👋 Tạm biệt. Chương trình dừng lại.[/bold red]")
            sys.exit(0)
        
        elif choice == '2':
            tool_get_chat_id()
            # Quay lại menu sau khi hoàn thành
            continue

        elif choice == '1':
            break # Thoát vòng lặp menu để bắt đầu chạy bot
    
    # BẮT ĐẦU CHẠY BOT
    try:
        clear_screen()
        
        # 1. Get User-Agent
        get_user_agent()
        
        # 2. Get Authorization
        AUTH = get_authorization()
        
        # 3. Get Telegram Config (chỉ cần Chat ID trong bộ nhớ)
        get_telegram_config()
        
        # 4. Run initial account check
        console.print("🚀 [bold green]Đăng nhập thành công! Đang vào Tool Instagram...[/bold green]")
        time.sleep(1)
        chontk_Instagram = safe_dict_check(chonacc(AUTH), context="chonacc API") 
        
        # 5. Select Account(s) and get Cookies
        ACCOUNTS = dsacc(chontk_Instagram, AUTH)
        
        if not ACCOUNTS:
            console.print("\n[bold red]Chưa có tài khoản Instagram nào được chọn hoặc có Cookies hợp lệ. Chương trình dừng lại.[/bold red]")
            sys.exit(1)

        # 6. Get User Settings (Đã tích hợp Load/Save Config)
        display_banner()
        display_current_info(AUTH)
        DELAY, LANNHAN, DOIACC_LIMIT, LAM, JOB_SUCCESS_LIMIT, JOB_RATIO = get_user_settings()

        # 7. Start Main Loop 
        main_loop(ACCOUNTS, DELAY, LANNHAN, DOIACC_LIMIT, LAM, AUTH, JOB_SUCCESS_LIMIT, JOB_RATIO)

    except KeyboardInterrupt:
        console.print("\n[bold red]👋 Chương trình đã dừng bởi người dùng.[/bold red]")
    except Exception as e:
        # --- KHỐI CODE GỬI LỖI HỆ THỐNG VÀO TELEGRAM ---
        error_text = Text("\n❌ CÓ LỖI NGHIÊM TRỌNG XẢY RA! ❌\n", style="bold red")
        escaped_error_message = str(e)
        
        error_text.append(f"Lỗi: {escaped_error_message}\n", style="red") 
        error_text.append("\nChi tiết lỗi (Traceback):", style="bold yellow")
        
        console.print(error_text)
        
        # Gửi thông báo lỗi hệ thống qua Telegram
        telegram_message = f"""
🔥 <b>LỖI HỆ THỐNG BOT NGHIÊM TRỌNG!</b> 🔥
- Bot đã dừng chạy.
- Lỗi chi tiết: <b>{escaped_error_message[:100]}...</b>
- Hành động: Vui lòng kiểm tra console để xem chi tiết lỗi.
"""
        send_telegram_message(telegram_message)

        # In Traceback ra console
        traceback_string = traceback.format_exc()
        console.print(Text(traceback_string, style="dim")) 
        
        sys.exit(1)