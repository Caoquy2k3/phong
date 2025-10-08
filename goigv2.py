import datetime
import os
import sys
import time
import json
import random
import threading
import requests
import urllib.request
from urllib.parse import urlparse, parse_qs
import socket
import os, psutil
import platform
import re # Thêm thư viện regex
import os, psutil
import platform
import re # Thêm thư viện regex

# --- Xử lý tương thích Curl Cffi ---
try:
    if 'android' in platform.system().lower() or 'termux' in platform.release().lower():
        raise ImportError("Không dùng curl_cffi trên Termux")
    from curl_cffi import requests as cffi_requests  # Thư viện Curl Cffi (cho Mode 4)
    CFFI_AVAILABLE = True
except Exception:
    import requests as cffi_requests
    CFFI_AVAILABLE = False
    
# Thư viện requests tiêu chuẩn (dùng cho API bên ngoài và fallback)
import requests as standard_requests

# --- Cấu hình Mã Màu ANSI ---
YELLOW  = "\033[33m"
BLUE    = "\033[34m"
MAGENTA = "\033[35m"
RESET   = "\033[0m"
RED     = "\033[31m"
GREEN   = "\033[32m"
CYAN    = "\033[36m"
WHITE   = "\033[37m" 
BOLD    = "\033[1m"
BRIGHT_RED     = "\033[91m"

# Regex để loại bỏ mã màu ANSI
ANSI_ESCAPE = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

# --- Hằng số File ---
AUTH_FILE = "Authorization.txt"
COOKIES_FILE = "Cookies_IG.txt"
CONFIG_FILE = "config.json" # Thêm Config file
STATE_FILE = "state.json" # Thêm State file
LOG_FILE = "log.txt" # Thêm Log file
DEFAULT_IP = "Đang kiểm tra..." 

# --- Biến toàn cục ---
HTTP_MODE_CHOICE = 4 
PUBLIC_IP = "Đang kiểm tra..." # Biến mới lưu IP Public

# --- Hằng số Banner Text ---
BANNER_TEXT = fr"""{CYAN}
    ____  __  __________  ___    _   _____   ____ _____{YELLOW}
   / __ \/ / /_  __/ __ \/   |  / | / /__ \ / __ \__  / 🔹
  / /_/ / /   / / / /_/ / /| | /  |/ /__/ // / / //_ <  {GREEN}🔹 {BOLD}{GREEN}TOOL AUTO 
 / ____/ /___/ / / _, _/ ___ |/ /|  // __// /_/ /__/ / {GREEN}🔹 Version : 2.0
/_/   /_____/_/ /_/ |_/_/  |_/_/ |_//____/\____/____/  {BLUE}GOLIKE {MAGENTA}INSTAGRAM{RESET}
{BOLD}{CYAN}Telegram: {WHITE}https://t.me/se_meo_bao_an{RESET}🔹 {BLUE}MBBANK{RESET} :{YELLOW}PLTRAN203{RESET}🔹{RESET} {GREEN}TÊN : {RESET}{BOLD}{CYAN}Phong Tus{RESET}
════════════════════════════════════════════════════════════════════════════════
{RESET}"""
# --- Hàm Xóa Màn Hình ---
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
    
def clear():
    clear_screen()

# --- Hàm Lấy Thời Gian ---
def get_current_time_str(format_str="%H:%M:%S"):
    tz = datetime.timezone(datetime.timedelta(hours=7))
    now = datetime.datetime.now(tz)
    return now.strftime(format_str)

# --- NEW: Hàm Ghi Log (Loại bỏ mã màu cho log file) ---
def write_log(message, type="INFO"):
    """Ghi thông báo vào console và log.txt, loại bỏ mã màu khi ghi file."""
    timestamp = get_current_time_str(format_str="%Y-%m-%d %H:%M:%S")
    
    # Loại bỏ mã màu ANSI cho log file
    log_message_no_color = ANSI_ESCAPE.sub('', message)
    log_entry = f"[{timestamp}] [{type}] {log_message_no_color}\n"
    
    # In ra console (giữ màu)
    print(f"{CYAN}[LOG] {message}{RESET}") 
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"{RED}[✖] Lỗi ghi log file: {e}{RESET}")

# --- Hàm Hiển Thị Banner ---
def print_animated_banner_char_by_char(text, delay=0.008):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)

def print_fast_banner(user_info=None):
    print(BANNER_TEXT)
    if user_info and isinstance(user_info, dict):
        print(f"{CYAN}👤 ID: {user_info.get('id','None')} | Tên: {user_info.get('name','None')} | 💰 Xu: {GREEN}{user_info.get('coin','None')}{RESET}\n")

def banner(user_info=None):
    clear_screen()
    print_animated_banner_char_by_char(BANNER_TEXT, delay=0.008) 
    if user_info and isinstance(user_info, dict):
        print(f"{CYAN}👤 ID: {user_info.get('id','None')} | Tên: {user_info.get('name','None')} | 💰 Xu: {GREEN}{user_info.get('coin','None')}{RESET}\n")

# --- NEW: Hàm lấy IP công cộng thực tế ---
def get_real_public_ip():
    """Lấy IP Public của máy tính bằng cách gọi API bên ngoài."""
    try:
        write_log("Đang lấy IP Public...", "SETUP")
        # Sử dụng standard_requests cho API bên ngoài
        response = standard_requests.get('https://api.ipify.org', timeout=5)
        if response.status_code == 200:
            return response.text.strip()
    except Exception as e:
        write_log(f"Không thể lấy IP Public: {e}", "ERROR")
    return "Không thể lấy IP"

# --- Hàm chọn session kết nối (Giữ nguyên logic) ---
def get_http_session(is_ig_request=False):
    """Chọn và trả về thư viện HTTP Request dựa trên HTTP_MODE_CHOICE."""
    global HTTP_MODE_CHOICE
    
    session = None
    
    if HTTP_MODE_CHOICE == 4 and CFFI_AVAILABLE:
        try:
            session = cffi_requests.Session(impersonate="chrome120")
        except Exception:
            session = standard_requests.Session()
    else:
        session = standard_requests.Session()

    return session

# --- Hàm Xử lý File đọc/ghi nhiều dòng (Thêm xử lý file STATE/CONFIG) ---
def read_or_prompt_multi_line_file(filename, item_name):
    items = []
    
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                items = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"{RED}[✖] Không thể đọc file {filename}! Lỗi: {e}{RESET}")
            exit(1)
            
    if not items:
        # Nếu là file State hoặc Config, không cần nhập thủ công
        if filename in (STATE_FILE, CONFIG_FILE):
            return []
            
        while True:
            print(f"{WHITE}[{RED}❣{WHITE}] {CYAN}✈ {GREEN}Vui lòng nhập danh sách {item_name} (mỗi {item_name} trên một dòng). Nhập 'END' khi hoàn tất:{RESET}")
            temp_items = []
            
            while True:
                line = input(f"{WHITE}[{RED}❣{WHITE}] {CYAN}✈ {item_name} #{len(temp_items) + 1}: ").strip()
                if line.lower() == 'end':
                    break
                if line:
                    temp_items.append(line)
                
            if temp_items:
                items = temp_items
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(items) + '\n')
                    print(f"{GREEN}[✔] Đã lưu {len(items)} {item_name} vào {filename}.{RESET}")
                    break
                except Exception as e:
                    print(f"{RED}[✖] Không thể ghi vào file {filename}! Lỗi: {e}{RESET}")
                    exit(1)
            else:
                print(f"{RED}Danh sách {item_name} không được để trống!{RESET}")
                
    return items

# --- Hàm Tùy chọn (Xóa File) ---
def handle_file_choice(filename, file_type):
    if not os.path.exists(filename):
        return
        
    while True:
        print(f"{WHITE}[{RED}❣{WHITE}] {CYAN}✈ {GREEN}Nhập 1 để sử dụng {file_type} cũ ({os.path.basename(filename)}){RESET}")
        print(f"{WHITE}[{RED}❣{WHITE}] {CYAN}✈ {RED}Nhập 2 Để Xóa {file_type} Hiện Tại{RESET}")
        try:
            choice = input(f"{WHITE}[{RED}❣{WHITE}] {CYAN}✈ {GREEN}Nhập Lựa Chọn (1 hoặc 2): {RESET}").strip()
            if choice == '1':
                return
            elif choice == '2':
                try:
                    os.remove(filename)
                    print(f"{GREEN}[✔] Đã xóa {filename}!{RESET}")
                except OSError as e:
                    print(f"{RED}[✖] Không thể xóa {filename}! Lỗi: {e.strerror}{RESET}")
                if filename not in (CONFIG_FILE, STATE_FILE):
                     print(f"{YELLOW}👉 Vui lòng nhập lại thông tin {file_type}!{RESET}")
                return
            else:
                print(f"{RED}\n❌ Lựa chọn không hợp lệ! Hãy nhập lại (1 hoặc 2).{RESET}")
        except ValueError:
            print(f"{RED}Sai định dạng! Vui lòng nhập số.{RESET}")

# --- NEW: Các Hàm Xử lý CONFIG/STATE ---

def save_config(delay, lannhan, doiacc_limit, lam): 
    """Lưu cấu hình chạy vào config.json."""
    config = {
        "delay": delay,
        "lannhan": lannhan,
        "doiacc_limit": doiacc_limit,
        "lam": lam,
        "http_mode": HTTP_MODE_CHOICE
    }
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        write_log(f"Đã lưu cấu hình vào {CONFIG_FILE}.", "CONFIG")
    except Exception as e:
        write_log(f"Lỗi khi lưu cấu hình: {e}", "ERROR")

def load_config():
    """Tải cấu hình chạy từ config.json."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                write_log(f"Đã tải cấu hình từ {CONFIG_FILE}.", "CONFIG")
                return config
        except Exception as e:
            write_log(f"Lỗi khi tải cấu hình, sẽ yêu cầu nhập lại: {e}", "ERROR")
    return {}

def save_state(profiles):
    """Lưu trạng thái của các profiles vào state.json."""
    state_data = {}
    for p in profiles:
        state_data[p['username']] = {
            'success_count': p['success_count'],
            'fail_count': p['fail_count'],
            'total_earn': p['total_earn']
        }
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, indent=4)
        write_log(f"Đã lưu trạng thái của {len(profiles)} profiles vào {STATE_FILE}.", "STATE")
    except Exception as e:
        write_log(f"Lỗi khi lưu trạng thái: {e}", "ERROR")

def load_state(profiles):
    """Tải trạng thái từ state.json và áp dụng cho các profiles."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
                loaded_count = 0
                for p in profiles:
                    state = state_data.get(p['username'])
                    if state:
                        p['success_count'] = state.get('success_count', 0)
                        p['fail_count'] = state.get('fail_count', 0)
                        p['total_earn'] = state.get('total_earn', 0.0)
                        loaded_count += 1
                write_log(f"Đã tải trạng thái cho {loaded_count} profiles từ {STATE_FILE}.", "STATE")
        except Exception as e:
            write_log(f"Lỗi khi tải trạng thái: {e}. Sẽ chạy lại từ đầu.", "ERROR")
    return profiles

# --- Các Hàm Xử lý API (Sử dụng session động) ---

def get_golike_headers(author_token):
    return {
        'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8',
        'Referer': 'https://app.golike.net/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'T': 'VFZSak1FMTZZM3BOZWtFd1RtYzlQUT09',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
        "Authorization": author_token,
        'Content-Type': 'application/json;charset=utf-8'
    }

# Sử dụng logic retry cho Golike API để tăng ổn định
def call_golike_api(url, method, author_token, params=None, json_data=None):
    golike_headers = get_golike_headers(author_token)
    session = get_http_session(is_ig_request=False) 
    
    for attempt in range(1, 4): # Thử lại tối đa 3 lần
        try:
            if method == 'GET':
                response = session.get(url, headers=golike_headers, params=params, timeout=10)
            else:
                response = session.post(url, headers=golike_headers, json=json_data, timeout=15)
            
            if response.status_code == 429:
                write_log(f"API Golike báo Quá tải (429). Đang chờ 30s... (Lần {attempt})", "WARNING")
                time.sleep(30)
                continue
            
            if not response.text:
                return {"status": 500, "message": "Phản hồi rỗng (Lỗi kết nối?)"}
                 
            try:
                data = response.json()
                if data.get("status") != 200 and "rate limit" in data.get("message", "").lower():
                     write_log(f"Golike báo Rate Limit. Đang chờ 30s... (Lần {attempt})", "WARNING")
                     time.sleep(30)
                     continue
                return data
            except json.JSONDecodeError:
                if response.text.startswith('<!DOCTYPE html>'):
                     write_log("Bị chặn bởi Golike/Firewall (Phản hồi là HTML)", "ERROR")
                     return {"status": 500, "message": "Bị chặn bởi Golike/Firewall."}
                return {"status": 500, "message": f"Lỗi Decode JSON API."}
                
        except standard_requests.exceptions.RequestException as e:
            write_log(f"Lỗi kết nối API: {e}. Thử lại sau 10s... (Lần {attempt})", "WARNING")
            time.sleep(10)
        except Exception as e:
            return {"status": 500, "message": f"Lỗi chung khi gọi API: {e}"}
            
    return {"status": 500, "message": "Thất bại sau nhiều lần thử gọi API."}


def chonacc(author_token):
    return call_golike_api('https://gateway.golike.net/api/instagram-account', 'GET', author_token)

def nhannv(account_id, author_token):
    params = {'instagram_account_id': account_id, 'data': 'null'}
    return call_golike_api('https://gateway.golike.net/api/advertising/publishers/instagram/jobs', 'GET', author_token, params=params)

def hoanthanh(ads_id, account_id, author_token):
    json_data = {
        'instagram_users_advertising_id': ads_id,
        'instagram_account_id': account_id,
        'async': True,
        'data': None
    }
    return call_golike_api('https://gateway.golike.net/api/advertising/publishers/instagram/complete-jobs', 'POST', author_token, json_data=json_data)

def baoloi(ads_id, object_id, account_id, loai, author_token):
    session = get_http_session(is_ig_request=False)
    golike_headers = get_golike_headers(author_token)
    try:
        # Báo lỗi
        url_report = 'https://gateway.golike.net/api/report/send'
        json_data_report = {
            'description': 'Tôi đã làm Job này rồi',
            'users_advertising_id': ads_id,
            'type': 'ads',
            'provider': 'instagram',
            'fb_id': account_id,
            'error_type': 6
        }
        session.post(url_report, headers=golike_headers, json=json_data_report, timeout=5)
        
        # Skip job
        url_skip = 'https://gateway.golike.net/api/advertising/publishers/instagram/skip-jobs'
        json_data_skip = {
            'ads_id': ads_id,
            'object_id': object_id,
            'account_id': account_id,
            'type': loai
        }
        session.post(url_skip, headers=golike_headers, json=json_data_skip, timeout=5)
    except standard_requests.exceptions.RequestException:
        write_log(f"Lỗi kết nối khi gửi báo lỗi/skip job {ads_id}.", "WARNING")
    except Exception:
        pass
    return None

# --- Các Hàm Tương tác với Instagram ---
def get_ig_headers(cookies, link=None):
    """Xây dựng headers cho các request Instagram, trích xuất CSRF token từ cookies."""
    token = None
    if 'csrftoken' in cookies:
        for cookie in cookies.split(';'):
            if 'csrftoken=' in cookie:
                token = cookie.split('csrftoken=')[1].split(';')[0].strip()
                break

    headers = {
        'Accept': '*/*',
        'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': cookies,
        'Origin': 'https://www.instagram.com',
        'Referer': link if link else 'https://www.instagram.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
        'X-Asbd-Id': '198387',
        'X-Csrftoken': token if token else '',
        'X-Ig-App-Id': '936619743392459',
        'X-Ig-Www-Claim': 'hmac.AR1UYU8O8XCMl4jZdv4YxiRUxEIymCA_4stpgFmc092K1Kb2',
        'X-Instagram-Ajax': '1006309104',
    }
    return headers

def handle_follow_job(cookies, object_id):
    """Thực hiện hành động Follow trên Instagram. Trả về True/False/"400"."""
    session = get_http_session(is_ig_request=True) 
    url = f"https://i.instagram.com/api/v1/web/friendships/{object_id}/follow/"
    headers = get_ig_headers(cookies, link=f'https://www.instagram.com/web/friendships/{object_id}/follow/')
    
    try:
        response = session.post(url, headers=headers, timeout=10)
        
        if response.status_code == 400:
            return "400" 
        
        response.raise_for_status() 
        
        response_data = response.json()
        if response_data.get('status') == 'ok' or response_data.get('following') is True:
            return True
        else:
            return False

    except standard_requests.exceptions.HTTPError:
        return False
        
    except standard_requests.exceptions.RequestException:
        return False
        
    except json.JSONDecodeError:
         return False
         
    except Exception:
        return False

def handle_like_job(cookies, media_id, link):
    """Thực hiện hành động Like trên Instagram. Trả về True, False, hoặc "400"."""
    session = get_http_session(is_ig_request=True) 
    url = f"https://www.instagram.com/web/likes/{media_id}/like/"
    headers = get_ig_headers(cookies, link=link)
    
    try:
        response = session.post(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            if '"status":"ok"' in response.text:
                return True
            else:
                return False
        elif response.status_code == 400: 
            if 'Sorry, this photo has been deleted' in response.text:
                return False 
            else:
                return "400" 
        else:
            return False

    except standard_requests.exceptions.RequestException:
        return False
        
    except json.JSONDecodeError:
         return False
         
    except Exception:
        return False

# --- Hàm Cấu Hình Multi-Account ---

def dsacc_by_auth(chontk_Instagram_data):
    if not isinstance(chontk_Instagram_data, dict) or chontk_Instagram_data.get("status") != 200:
        error_message = chontk_Instagram_data.get("message", "Authorization sai hoặc chưa liên kết tài khoản Instagram!")
        return None, f"\n{WHITE}[{RED}❣{WHITE}] {CYAN}✈ {RED}{error_message}{RESET}"
                
    account_list = chontk_Instagram_data.get("data", [])
    if not account_list:
        return None, f"\n{WHITE}[{RED}❣{WHITE}] {CYAN}✈ {RED}Không tìm thấy tài khoản Instagram nào được liên kết với Authorization này!{RESET}"

    output = []
    output.append(f"{'═'*50}")
    output.append(f"{WHITE}[{RED}❣{WHITE}]{YELLOW} Danh sách acc Instagram liên kết: ")
    output.append(f"{'═'*50}")
            
    for i, acc in enumerate(account_list):
        output.append(f"{CYAN}[{i + 1}]{CYAN} ✈ {WHITE}Username{GREEN}㊪ :{YELLOW} {acc['instagram_username']} {WHITE}|{RED}㊪ :{GREEN} ID: {acc['id']}")
            
    output.append(f"{'═'*50}")
    return account_list, "\n".join(output)

def setup_working_profiles(auth_tokens, cookies_list):
    working_profiles = []
    num_profiles = min(len(auth_tokens), len(cookies_list))
    
    if num_profiles == 0:
        print(f"{RED}Không tìm thấy cặp Authorization và Cookies hợp lệ nào để chạy!{RESET}")
        return []
    
    print(f"\n{GREEN}✅ Đã ghép cặp {num_profiles} Authorization và Cookies.{RESET}")
    time.sleep(1)

    for i in range(num_profiles):
        auth_token = auth_tokens[i]
        cookies = cookies_list[i]
        
        clear()
        print_fast_banner() 
        print(f"{CYAN}--- CẤU HÌNH PROFILE {i + 1}/{num_profiles} ---{RESET}")
        print(f"{CYAN}🔑 Authorization: {auth_token[:10]}...{RESET}")
        print(f"{CYAN}🍪 Cookies IG: {cookies[:15]}...{RESET}") 
        
        chontk_Instagram = chonacc(auth_token)
        account_list, display_text = dsacc_by_auth(chontk_Instagram)
        
        print(display_text)
        
        if not account_list:
            write_log(f"Profile {i+1}: Bỏ qua do không lấy được danh sách acc Golike.", "WARNING")
            print(f"{RED}🚫 Bỏ qua Profile {i + 1}. Vui lòng kiểm tra lại Authorization/kết nối.{RESET}")
            time.sleep(3)
            continue
            
        max_index = len(account_list)

        account_id = None
        current_username = None
        
        while True:
            try:
                choice_index_str = input(f"{WHITE}[{RED}❣{WHITE}] {CYAN}✈ {GREEN}Nhập {RED}SỐ THỨ TỰ (1-{max_index}) {GREEN}của Acc IG {YELLOW}KHỚP VỚI COOKIES{GREEN} này: {RESET}").strip()
                
                if not choice_index_str.isdigit():
                    print(f"{RED}Vui lòng nhập số thứ tự (1 đến {max_index}).{RESET}")
                    continue
                    
                choice_index = int(choice_index_str)
                
                if 1 <= choice_index <= max_index:
                    selected_acc = account_list[choice_index - 1]
                    account_id = selected_acc["id"]
                    current_username = selected_acc["instagram_username"]
                    print(f"{GREEN}✔ Đã chọn tài khoản: {current_username}{RESET}")
                    break
                else:
                    print(f"{WHITE}[{RED}❣{WHITE}] {CYAN}✈ {RED}Số thứ tự phải nằm trong khoảng từ 1 đến {max_index}!{RESET}")

            except Exception:
                print(f"{RED}Lỗi nhập liệu! Vui lòng nhập lại.{RESET}")
                pass
                
        working_profiles.append({
            'index': i + 1,
            'auth_token': auth_token,
            'cookies': cookies,
            'account_id': account_id,
            'username': current_username,
            'fail_count': 0,
            'success_count': 0,
            'total_earn': 0.0, 
            'last_run': get_current_time_str(), 
            'status': f"{YELLOW}Đang chờ...{RESET}",
            'last_job': "N/A"
        })
        time.sleep(1)

    return working_profiles

# --- HÀM VẼ BẢNG (Cập nhật hiển thị IP Public) ---
def draw_table(profiles, current_profile_index, global_fail_limit):
    
    global PUBLIC_IP 

    # 1. Cấu hình cột và tiêu đề
    COLUMNS = [
        ("STT", 5),
        ("USERNAME", 18),
        ("TRẠNG THÁI", 10),
        ("LAST RUN", 10),
        ("SUCCESS", 10),
        ("FAIL", 10),
        ("MESSAGE", 30),
    ]
    
    COL_WIDTHS = [c[1] for c in COLUMNS]
    TOTAL_WIDTH = sum(COL_WIDTHS) + len(COLUMNS) + 1 

    SEPARATOR_LINE = f"{MAGENTA}{'═' * TOTAL_WIDTH}{RESET}"
    HEADER_FORMAT = f"{CYAN}|{{:^{COL_WIDTHS[0]}}}| {{:^{COL_WIDTHS[1]}}}| {{:^{COL_WIDTHS[2]}}}| {{:^{COL_WIDTHS[3]}}}| {{:^{COL_WIDTHS[4]}}}| {{:^{COL_WIDTHS[5]}}}| {{:^{COL_WIDTHS[6]}}}|{RESET}"
    ROW_FORMAT = f"|{{:^{COL_WIDTHS[0]}}}| {{:<{COL_WIDTHS[1]}}}| {{:^{COL_WIDTHS[2]}}}| {{:^{COL_WIDTHS[3]}}}| {{:^{COL_WIDTHS[4]}}}| {{:^{COL_WIDTHS[5]}}}| {{:<{COL_WIDTHS[6]}}}|"
    
    clear() 
    print_fast_banner() 
    
    total_earn_all = sum(p['total_earn'] for p in profiles)
    print(f"{CYAN}--- THÔNG TIN CHUNG ---{RESET}")
    print(f"{WHITE}🏠 IP Public: {PUBLIC_IP} | {GREEN}Tổng ACC: {len(profiles)} | 💰 TỔNG XU: {YELLOW}{total_earn_all:.0f}{RESET} xu | {RED}Giới hạn Fail: {global_fail_limit}{RESET}") 
    print(SEPARATOR_LINE)
    print(HEADER_FORMAT.format(*[c[0] for c in COLUMNS]))
    print(SEPARATOR_LINE)
    
    # 2. Vẽ từng hàng
    for i, profile in enumerate(profiles):
        
        display_username = profile['username'][:COL_WIDTHS[1]]
        
        status_color = YELLOW
        if "RUNNING" in profile['status'] or "SUCCESS" in profile['status']:
            status_color = GREEN
        elif "FAIL" in profile['status'] or "LỖI" in profile['status'] or "IDLE" in profile['status']:
            status_color = RED
            
        # Loại bỏ mã màu ANSI trong status để tính chiều dài
        status_display_raw = ANSI_ESCAPE.sub('', profile['status']).strip()
        status_display = f"{status_color}{status_display_raw[:COL_WIDTHS[2]]}{RESET}"
        
        message_display = profile['last_job'][:COL_WIDTHS[6]] 
        
        success_display = f"{GREEN}{profile['success_count']}{RESET}"
        fail_display = f"{RED}{profile['fail_count']}/{global_fail_limit}{RESET}"
        
        stt_display = f"{profile['index']}"
        if i == current_profile_index:
             stt_display = f"{BOLD}{BRIGHT_RED}>>>{profile['index']}{RESET}"

        row_content = ROW_FORMAT.format(
            stt_display,
            display_username,
            status_display,
            profile['last_run'],
            success_display,
            fail_display,
            message_display
        )
        
        print(row_content)
        print(SEPARATOR_LINE)
        
    sys.stdout.flush()

# --- Logic Chính ---

def main():
    global current_profile_index
    global HTTP_MODE_CHOICE
    global PUBLIC_IP 
    
    current_profile_index = 0

    # 0. Lấy IP Public và Log
    PUBLIC_IP = get_real_public_ip()
    
    # 1. Cấu hình ban đầu & Nhập liệu
    clear_screen()
    banner() 
    
    print(f"{WHITE}[{RED}❣{WHITE}]{WHITE} Địa chỉ Ip{GREEN}  : {GREEN}☞{RED}♔ {GREEN}{PUBLIC_IP}{RED}♔ {WHITE}☜")
    print("════════════════════════════════════════════════")
    
    # AUTH
    handle_file_choice(AUTH_FILE, "Authorization")
    auth_tokens = read_or_prompt_multi_line_file(AUTH_FILE, "Authorization")

    clear()
    banner()
    print(f"{WHITE}[{RED}❣{WHITE}]{WHITE} Địa chỉ Ip{GREEN}  : {GREEN}☞{RED}♔ {GREEN}{PUBLIC_IP}{RED}♔ {WHITE}☜")
    print("════════════════════════════════════════════════")
    
    # COOKIES
    handle_file_choice(COOKIES_FILE, "Cookies")
    cookies_list = read_or_prompt_multi_line_file(COOKIES_FILE, "Cookie")
    
    # Tải cấu hình cũ
    config = load_config()

    # Hàm nhập liệu chung
    def input_setting(key, default_value, prompt, cast_type=int, validation=None):
        value = config.get(key, default_value)
        while True:
            try:
                user_input = input(f"{WHITE}[{RED}❣{WHITE}] {CYAN}✈ {GREEN}{prompt} {YELLOW}({value} nếu Enter): {RESET}").strip() or str(value)
                
                if cast_type == bool: # Xử lý boolean/y/n
                     if user_input.lower() in ('y', 'n'):
                         return user_input.lower()
                
                value = cast_type(user_input)
                
                if validation is None or validation(value):
                    return value
                else:
                    print(f"{RED}Giá trị không hợp lệ. Vui lòng nhập lại.{RESET}")
            except ValueError:
                print(f"{WHITE}[{RED}❣{WHITE}] {CYAN}✈ {RED}Sai định dạng!!! Vui lòng nhập số.{RESET}")

    # Cấu hình HTTP Mode
    # Tải HTTP Mode từ config nếu có
    if config.get("http_mode") is not None:
         HTTP_MODE_CHOICE = config["http_mode"]
         print(f"{GREEN}[✔] Đã tải HTTP Mode cũ: {HTTP_MODE_CHOICE}{RESET}")
         
    def choose_http_mode_v2():
        global HTTP_MODE_CHOICE
        while True:
            choice_type = input(f"{WHITE}[{RED}?{WHITE}] {CYAN}HTTP Mode hiện tại: {HTTP_MODE_CHOICE}. Nhập 1 để sử dụng Mode cũ, Nhập 2 để Chọn Mode Mới: {RESET}").strip()
            
            if choice_type == '1':
                return
            
            if choice_type == '2':
                # Giữ nguyên logic chọn mode mới
                clear()
                print_fast_banner() 
                # ... (Hiển thị bảng chọn mode, lược bỏ để giữ code gọn)
                
                print(f"{BOLD}{WHITE}STT | MODE            | INFO                                     {RESET}")
                print("═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════")
                print(f"4   | {GREEN}Curl Cffi{RESET}       | Tối ưu cho Windows (Bypass tốt nhất - Recommended){RESET}")
                print(f"0   | {YELLOW}requests{RESET}        | Thư viện requests (Mặc định, dễ bị chặn)                                  ")
                print("═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════")
                
                while True:
                    try:
                        new_mode = input(f"{WHITE}[{RED}?{WHITE}] {CYAN}Nhập số tương ứng với mode (4 hoặc 0): {RESET}").strip()
                        if new_mode.isdigit():
                            mode_int = int(new_mode)
                            if mode_int in (0, 4):
                                HTTP_MODE_CHOICE = mode_int
                                print(f"{GREEN}✔ Đã chọn HTTP Mode mới: {HTTP_MODE_CHOICE}{RESET}")
                                return
                            else:
                                print(f"{RED}Lựa chọn không hợp lệ. Vui lòng nhập 0 hoặc 4.{RESET}")
                        else:
                            print(f"{RED}Lựa chọn không hợp lệ. Vui lòng nhập số.{RESET}")
                    except ValueError:
                        print(f"{RED}Lỗi nhập liệu! Vui lòng nhập số.{RESET}")
            else:
                print(f"{RED}Lựa chọn không hợp lệ. Vui lòng nhập 1 hoặc 2.{RESET}")

    choose_http_mode_v2()

    if len(auth_tokens) != len(cookies_list):
        # ... (logic cảnh báo)
        pass


    working_profiles = setup_working_profiles(auth_tokens, cookies_list)
    working_profiles = load_state(working_profiles) # Tải state vào profiles
    
    if not working_profiles:
        write_log("Không có tài khoản nào được cấu hình thành công. Đã thoát.", "CRITICAL")
        print(f"{RED}Không có tài khoản nào được cấu hình thành công. Đã thoát.{RESET}")
        exit(1)
        
    clear()
    print_fast_banner() 

    # 2. Nhận các cấu hình chạy còn lại (dùng giá trị từ config hoặc nhập lại)
    delay = input_setting('delay', 0, "Nhập thời gian làm job (giây)", cast_type=int, validation=lambda x: x >= 0)
    lannhan = input_setting('lannhan', 'n', "Nhận tiền lần 2 nếu lần 1 fail? (y/n)", cast_type=bool, validation=lambda x: x in ('y', 'n'))
    doiacc_limit = input_setting('doiacc_limit', 3, "Số job fail liên tiếp để CHUYỂN ACC TIẾP THEO (>=1)", cast_type=int, validation=lambda x: x >= 1)
    
    # Chế độ làm
    lam = config.get('lam', [])
    if not lam:
        while True:
            # ... (logic chọn chế độ làm)
            print(f"{'═'*50}")
            print(f"{WHITE}[{RED}❣{WHITE}] {CYAN}✈ {GREEN}Nhập 1 : {YELLOW}Chỉ nhận nhiệm vụ Follow")
            print(f"{WHITE}[{RED}❣{WHITE}] {CYAN}✈ {GREEN}Nhập 2 : {YELLOW}Chỉ nhận nhiệm vụ like")
            print(f"{WHITE}[{RED}❣{WHITE}] {CYAN}✈ {GREEN}Nhập 12 : {YELLOW}Kết hợp cả Like và Follow")
            print(f"{'═'*50}")
            
            try:
                chedo = input(f"{WHITE}[{RED}❣{WHITE}] {CYAN}✈ {BLUE}Chọn lựa chọn: {RESET}").strip()
                if chedo in ("1", "2", "12"):
                    if chedo == "1": lam = ["follow"]
                    elif chedo == "2": lam = ["like"]
                    elif chedo == "12": lam = ["follow", "like"]
                    break
                else:
                    print(f"{WHITE}[{RED}❣{WHITE}] {CYAN}✈ {RED}Chỉ được nhập 1, 2 hoặc 12!{RESET}")
            except ValueError:
                print(f"{WHITE}[{RED}❣{WHITE}] {CYAN}✈ {RED}Nhập vào 1 số!!!{RESET}")
    else:
        print(f"{GREEN}[✔] Đã tải Chế độ làm cũ: {', '.join(lam).upper()}{RESET}")

    # Lưu cấu hình sau khi hoàn tất nhập
    save_config(delay, lannhan, doiacc_limit, lam) 

    # 3. Vòng lặp chạy chính 
    current_profile_index = 0
    num_profiles = len(working_profiles)
    
    try: 
        while True:
            # ... (Logic chạy job tương tự như trước)
            current_profile = working_profiles[current_profile_index]
            auth_token = current_profile['auth_token']
            cookies = current_profile['cookies']
            account_id = current_profile['account_id']
            current_username = current_profile['username']
            
            # 1. Kiểm tra Giới hạn Fail
            if current_profile['fail_count'] >= doiacc_limit:
                current_profile['status'] = f"{RED}FAIL (Limit){RESET}"
                current_profile['last_job'] = "Fail liên tiếp. Chuyển acc..."
                draw_table(working_profiles, current_profile_index, doiacc_limit)
                write_log(f"ACC {current_username}: Đạt giới hạn fail ({current_profile['fail_count']}/{doiacc_limit}). Tự động chuyển acc.", "WARNING")
                time.sleep(3)
                current_profile['fail_count'] = 0
                current_profile_index = (current_profile_index + 1) % num_profiles
                save_state(working_profiles) 
                continue 

            current_profile['status'] = f"{GREEN}RUNNING (Tìm job){RESET}"
            current_profile['last_job'] = "Đang tìm nhiệm vụ..."
            draw_table(working_profiles, current_profile_index, doiacc_limit)
            write_log(f"ACC {current_username}: Bắt đầu tìm nhiệm vụ. (Tổng Xu: {current_profile['total_earn']:.0f})", "INFO")

            # 2. Tìm Nhiệm vụ
            job_found = False
            nhanjob = None
            
            for _ in range(3): 
                nhanjob = nhannv(account_id, auth_token)
                
                if not isinstance(nhanjob, dict) or nhanjob.get("status") != 200:
                    current_profile['fail_count'] += 1
                    current_profile['status'] = f"{RED}LỖI API{RESET}"
                    current_profile['last_job'] = nhanjob.get('message', 'Không rõ')[:30]
                    draw_table(working_profiles, current_profile_index, doiacc_limit)
                    write_log(f"ACC {current_username}: Lỗi API Golike khi nhận job. Message: {current_profile['last_job']}", "ERROR")
                    time.sleep(3)
                    break 
                
                if nhanjob.get("data"):
                     job_found = True
                     break
                else:
                    current_profile['status'] = f"{YELLOW}IDLE (Hết job){RESET}"
                    current_profile['last_job'] = "Hết nhiệm vụ. Chờ 10s"
                    draw_table(working_profiles, current_profile_index, doiacc_limit)
                    write_log(f"ACC {current_username}: Hết nhiệm vụ. Chuyển acc sau 10s.", "INFO")
                    time.sleep(10)
                    current_profile_index = (current_profile_index + 1) % num_profiles
                    break 

            if not job_found:
                 # Chuyển acc nếu hết job hoặc lỗi API sau 3 lần retry
                 if current_profile_index != (current_profile_index + 1) % num_profiles:
                     current_profile_index = (current_profile_index + 1) % num_profiles
                     continue
                 else:
                     # Chỉ có 1 acc, vẫn tiếp tục vòng lặp tìm job
                     time.sleep(5)
                     continue


            # 3. Thực hiện Job và Nhận tiền (Sử dụng logic cũ)
            job_data = nhanjob["data"]
            ads_id = job_data["id"]
            link = job_data["link"]
            object_id = job_data["object_id"]
            loai = job_data["type"]
            job_xu_raw = job_data.get("expected_money", 0) 
            job_xu = float(job_xu_raw) if isinstance(job_xu_raw, (int, float, str)) and str(job_xu_raw).replace('.', '', 1).isdigit() else 0.0

            current_profile['status'] = f"{CYAN}RUNNING ({loai}){RESET}"
            current_profile['last_job'] = f"Đang thực hiện {loai} ({job_xu:.0f} xu)..."
            draw_table(working_profiles, current_profile_index, doiacc_limit)
            
            if loai not in lam:
                baoloi(ads_id, object_id, account_id, loai, auth_token)
                current_profile['last_job'] = f"Bỏ qua {loai} (Không chọn)"
                draw_table(working_profiles, current_profile_index, doiacc_limit)
                time.sleep(1)
                continue

            # Thực hiện Job IG
            job_result = False
            if loai == "follow":
                job_result = handle_follow_job(cookies, object_id)
            elif loai == "like":
                # ... (logic lấy media_id)
                 object_data = job_data.get("object_data", {})
                 media_id = None
                 if isinstance(object_data, dict):
                    media_id = object_data.get("pk")
                 elif isinstance(object_data, str) and object_data.isdigit():
                    media_id = object_data
                 
                 if media_id:
                      job_result = handle_like_job(cookies, media_id, link)
                 else:
                      job_result = False
            
            success = job_result is True

            if not success:
                current_profile['fail_count'] += 1
                current_profile['last_run'] = get_current_time_str()
                baoloi(ads_id, object_id, account_id, loai, auth_token)
                
                fail_type = "IG"
                if job_result == "400":
                    fail_type = "400 (Cookies Die/Checkpoint)"
                    write_log(f"ACC {current_username}: Thất bại {loai}. Mã 400 IG. Cookies Die?", "CRITICAL")
                else:
                     write_log(f"ACC {current_username}: Thất bại {loai} ({fail_type}).", "ERROR")
                
                current_profile['status'] = f"{RED}FAIL ({fail_type}){RESET}"
                current_profile['last_job'] = f"Thất bại {loai}. Fail: {current_profile['fail_count']}/{doiacc_limit}"
                draw_table(working_profiles, current_profile_index, doiacc_limit)
                
                sleep_time = 5 if job_result == "400" else 3 
                time.sleep(sleep_time)
                save_state(working_profiles) 
                continue
            
            # Nếu thành công
            current_profile['fail_count'] = 0
            
            # Delay LÀM JOB
            current_profile['last_job'] = f"Chờ DELAY {delay}s để nhận Xu..." 
            draw_table(working_profiles, current_profile_index, doiacc_limit)
            
            start_delay_time = time.time()
            while (time.time() - start_delay_time) < delay:
                remaining_time = int(delay - (time.time() - start_delay_time))
                print(f"{CYAN}--- ACC {current_username} DELAY: {YELLOW}{remaining_time}s{CYAN} ---{RESET}", end='\r') 
                time.sleep(1)
            print(" " * 60, end='\r') 

            # Nhận Tiền
            ok = False
            max_check = 2 if lannhan == "y" else 1 
            
            for checklan in range(1, max_check + 1):
                current_profile['status'] = f"{YELLOW}NHẬN XU (Lần {checklan}){RESET}"
                current_profile['last_job'] = f"Đang gửi yêu cầu nhận tiền {loai}..."
                draw_table(working_profiles, current_profile_index, doiacc_limit)

                nhantien = hoanthanh(ads_id, account_id, auth_token)
                
                if not isinstance(nhantien, dict) or nhantien.get('status') != 200:
                    time.sleep(1)
                    continue
                    
                ok = True
                current_profile['success_count'] += 1
                
                xu_nhan_raw = nhantien.get('data', {}).get('xu', 0)
                xu_nhan_value = float(xu_nhan_raw) if isinstance(xu_nhan_raw, (int, float, str)) and str(xu_nhan_raw).replace('.', '', 1).isdigit() else 0.0
                    
                if xu_nhan_value > 0:
                    current_profile['total_earn'] += xu_nhan_value
                
                current_profile['last_run'] = get_current_time_str()
                current_profile['status'] = f"{GREEN}SUCCESS{RESET}"
                current_profile['last_job'] = f"✔ Nhận {xu_nhan_raw} xu! (Tổng: {current_profile['total_earn']:.0f})"
                
                # FIX: VẼ LẠI BẢNG VÀ IN THÔNG BÁO XÁC NHẬN RÕ RÀNG TRƯỚC KHI SLEEP 4 GIÂY
                draw_table(working_profiles, current_profile_index, doiacc_limit) 
                
                print(f"{GREEN}[✔] ACC {current_username}: Nhận thành công {xu_nhan_raw} xu! (Tổng: {current_profile['total_earn']:.0f}){RESET}")
                
                write_log(f"ACC {current_username}: Hoàn thành {loai} - Nhận {xu_nhan_raw} xu. Tổng: {current_profile['total_earn']:.0f} xu.", "SUCCESS")
                time.sleep(4) # Giữ màn hình ổn định 4 giây
                save_state(working_profiles) 
                break 

            if not ok:
                current_profile['fail_count'] += 1 
                current_profile['last_run'] = get_current_time_str()
                current_profile['status'] = f"{RED}FAIL (XU){RESET}"
                baoloi(ads_id, object_id, account_id, loai, auth_token) 
                current_profile['last_job'] = "Nhận tiền FAIL. Báo lỗi"
                draw_table(working_profiles, current_profile_index, doiacc_limit)
                write_log(f"ACC {current_username}: Thất bại nhận tiền job {ads_id}. Đã báo lỗi.", "ERROR")
                time.sleep(2)
                save_state(working_profiles) 
                continue
            
            # Chuyển acc tiếp theo
            current_profile_index = (current_profile_index + 1) % num_profiles
                
        
    except KeyboardInterrupt:
        # Xử lý khi dừng
        total_earn_final = sum(p['total_earn'] for p in working_profiles)
        print(f"\n{'═'*70}")
        print(f"{YELLOW}[!] Chương trình đã dừng bởi người dùng. Tổng Xu Kiếm Được: {GREEN}{total_earn_final:.0f}{RESET} xu")
        print(f"{'═'*70}")
        
        save_state(working_profiles) # Lưu trạng thái cuối cùng
        write_log(f"Chương trình dừng. Tổng Xu Kiếm Được: {total_earn_final:.0f} xu.", "EXIT")
        
    except Exception as e:
        write_log(f"LỖI NGHIÊM TRỌNG (Hệ thống): {e}", "CRITICAL")
        if working_profiles:
            current_profile = working_profiles[current_profile_index]
            current_profile['status'] = f"{RED}LỖI HỆ THỐNG{RESET}"
            current_profile['last_job'] = f"Lỗi: {str(e)[:20]}. Chuyển acc..."
            draw_table(working_profiles, current_profile_index, doiacc_limit)
            save_state(working_profiles)
        print(f"\n{RED}LỖI NGHIÊM TRỌNG (Hệ thống): {e}{RESET}")
        
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n{RED}LỖI KHỞI ĐỘNG CHƯƠNG TRÌNH: {e}{RESET}")
        # ... (các hàm và logic kết thúc tại đây)
# ...

# --- HÀM KHỞI ĐỘNG CỦA MODULE (BẮT BUỘC CHO TOOL MENU) ---

def run():
    """
    Điểm khởi động chính, được gọi bởi tool menu.
    Gọi hàm main() chứa toàn bộ logic chạy.
    """
    main()

# Đảm bảo lệnh chạy khi file được gọi trực tiếp
if __name__ == '__main__':
    run()
