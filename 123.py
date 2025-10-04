#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
# --- CẤU HÌNH ---
API_KEY         = "68b724432ecbb063ee12123a"
DESTINATION     = "https://yourdestinationlink.com/?key="
KEY_FILE        = "key_data.json"
KEY_PLAIN_FILE  = "key.txt"
AUTH_FILE       = "auth.json"
KEY_PREFIX      = "phonganh20703"
KEY_TTL         = 24 * 3600 # 24 giờ

# --- MÃ MÀU TERMINAL ---
RESET   = "\033[0m"
BLACK   = "\033[30m"
RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
BLUE    = "\033[34m"
MAGENTA = "\033[35m"
CYAN    = "\033[36m"
WHITE   = "\033[37m"
BRIGHT_BLACK   = "\033[90m"
BRIGHT_RED     = "\033[91m"
BRIGHT_GREEN   = "\033[92m"
BRIGHT_YELLOW  = "\033[93m"
BRIGHT_BLUE    = "\033[94m"
BRIGHT_MAGENTA = "\033[95m"
BRIGHT_CYAN    = "\033[96m"
BRIGHT_WHITE   = "\033[97m"
BG_BLACK   = "\033[40m"
BG_RED     = "\033[41m"
BG_GREEN   = "\033[42m"
BG_YELLOW  = "\033[43m"
BG_BLUE    = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN    = "\033[46m"
BG_WHITE   = "\033[47m"
BOLD      = "\033[1m"
DIM       = "\033[2m"
ITALIC    = "\033[3m"
UNDERLINE = "\033[4m"

# --- GLOBAL VARIABLES ---
monitor_lock = threading.Lock()
force_rekey_event = threading.Event()

# --- IP APIs ---
IP_APIS = [
    "https://ipapi.co/json/",
    "http://ip-api.com/json/", 
    "https://ipwhois.app/json/", 
    
]

# --- CÁC HÀM TIỆN ÍCH ---

def clear():
    # Đã sửa lỗi thụt lề
    os.system("cls" if os.name == "nt" else "clear")

def banner(user=None):
    clear()
    print(fr"""{CYAN}
___ __ _________ __________ ____ __        {YELLOW}🔹
/ _ \/ //_ _/ _ \/ / __ \/ __ \/ /       {GREEN}🔹
/ / // / / , / / / // / // /_/ /   {GREEN}🔹 {BOLD}{GREEN}TOOL AUTO {BLUE}GOLIKE {MAGENTA}INSTAGRAM{RESET}
//  /// //|| // \/\/___/    {CYAN}Version : 1.0{RESET}
{BOLD}{CYAN}Liên hệ: {WHITE}https://t.me/se_meo_bao_an{RESET}🔹 {BLUE}MBBANK{RESET} :{YELLOW}PPLTRAN203{RESET}🔹{RESET} {GREEN}TÊN : {RESET}{BOLD}{CYAN}PHONG TUS{RESET}
════════════════════════════════════════════════════════════════════════════════
{RESET}""")
    if user:
        print(f"{CYAN}👤 ID: {user.get('id','None')} | Tên: {user.get('name','None')} | 💰 Xu: {GREEN}{user.get('coin','None')}{RESET}\n")

def ping_test(host="8.8.8.8", port=53, timeout=3):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

def generate_key():
    n = random.randint(1, 7)
    suffix = ''.join(random.choices("0123456789", k=n))
    return f"{KEY_PREFIX}_{suffix}"

def create_short_link(api_key, url):
    try:
        # Sử dụng requests thay vì urllib.request cho API bên ngoài
        r = requests.get(f"https://link4m.co/api-shorten/v2?api={api_key}&url={url}", timeout=8)
        if r.status_code == 200:
            j = r.json()
            return j.get("shortenedUrl") or url
    except Exception:
        pass
    # Trả về url gốc nếu API thất bại
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/"

def extract_key_from_input(raw_input):
    s = (raw_input or "").strip()
    if not s:
        return s

    # Trường hợp 1: Chuỗi chứa 'key='
    if "key=" in s:
        try:
            parsed = urlparse(s)
            q = parse_qs(parsed.query)
            if "key" in q and q["key"]:
                return q["key"][0]
            # Fallback cho link không chuẩn
            return s.split("key=")[-1].split("&")[0]
        except Exception:
            return s.split("key=")[-1].split("&")[0]
            
    # Trường hợp 2: Là một URL cần theo dõi redirect (link rút gọn)
    if s.startswith("http://") or s.startswith("https://"):
        try:
            r = requests.get(s, timeout=8, allow_redirects=True)
            final = r.url
            if "key=" in final:
                parsed = urlparse(final)
                q = parse_qs(parsed.query)
                if "key" in q and q["key"]:
                    return q["key"][0]
                return final.split("key=")[-1].split("&")[0]
        except Exception:
            pass
    
    # Trường hợp 3: Chuỗi đã là key
    if s.startswith(KEY_PREFIX + "_"):
        return s
        
    return s # Trả về nguyên chuỗi nếu không tìm thấy gì hợp lệ

# --- QUẢN LÝ KEY FILE ---

def save_plain_key(key):
    try:
        with open(KEY_PLAIN_FILE, "w", encoding="utf-8") as f:
            f.write(key)
    except Exception:
        pass

def load_plain_key():
    try:
        if os.path.exists(KEY_PLAIN_FILE):
            with open(KEY_PLAIN_FILE, "r", encoding="utf-8") as f:
                k = f.read().strip()
                return k if k else None
    except Exception:
        pass
    return None

def save_key_to_file(key, ip, country=None, org=None, asn=None):
    data = {"key": key, "timestamp": time.time(), "ip": ip, "country": country, "org": org, "asn": asn}
    try:
        with open(KEY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass
    save_plain_key(key)

def load_key_file():
    if not os.path.exists(KEY_FILE):
        return None
    try:
        with open(KEY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Chuyển đổi tên key cũ nếu cần
            if "ts" in data and "timestamp" not in data:
                data["timestamp"] = data.pop("ts")
            return data
    except Exception:
        return None

def delete_key_file():
    try:
        if os.path.exists(KEY_FILE):
            os.remove(KEY_FILE)
    except Exception:
        pass
    try:
        if os.path.exists(KEY_PLAIN_FILE):
            os.remove(KEY_PLAIN_FILE)
    except Exception:
        pass

def remaining_human(seconds):
    if seconds <= 0:
        return "0h 0m"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}h {minutes}m"

def is_vpn_like(org, asn=None):
    if not org and not asn:
        return False
    org_lower = (org or "").lower()
    keywords = ["vpn", "proxy", "hosting", "digitalocean", "amazon", "google", "microsoft",
                "azure", "linode", "ovh", "hetzner", "cloud", "datacenter", "warp", "vps", "serverplan"]
    for kw in keywords:
        if kw in org_lower:
            return True
    return False

# --- KIỂM TRA IP / VPN ---

def safe_get(d, *keys):
    for k in keys:
        if isinstance(d, dict) and k in d and d[k] is not None:
            return d[k]
    return None

def normalize_ip_data(data: dict, source: str):
    # Xử lý timezone
    tz_raw = safe_get(data, "timezone") or safe_get(data, "time_zone") or safe_get(data, "timeZone")
    tz_id = None; tz_abbr = None; tz_time = None; tz_name = None; tz_offset = None; tz_dst = None
    if isinstance(tz_raw, dict):
        tz_id   = tz_raw.get("id") or tz_raw.get("timezone")
        tz_abbr = tz_raw.get("abbreviation")
        tz_time = tz_raw.get("current_time") or tz_raw.get("currentLocalTime") or tz_raw.get("datetime")
        tz_name = tz_raw.get("name")
        tz_offset = tz_raw.get("offset")
        tz_dst = tz_raw.get("in_daylight_saving")
    else:
        tz_id = tz_raw

    # Lấy các trường thông tin IP
    ip = safe_get(data, "ip") or safe_get(data, "query") or safe_get(data, "IPv4") or safe_get(data, "address")  
    country = safe_get(data, "country") or safe_get(data, "country_name")  
    country_code = safe_get(data, "countryCode") or safe_get(data, "country_code")  
    region = safe_get(data, "region") or safe_get(data, "regionName") or safe_get(data, "state") or safe_get(data, "region_name")  
    city = safe_get(data, "city")  
    org = safe_get(data, "org") or safe_get(data, "isp") or safe_get(data, "organization")  
    asn = safe_get(data, "asn") or safe_get(data, "as") or safe_get(data, "asname")  
    lat = safe_get(data, "lat") or safe_get(data, "latitude")  
    lon = safe_get(data, "lon") or safe_get(data, "longitude")  
    proxy = safe_get(data, "proxy") or safe_get(data, "is_proxy")  
    vpn = safe_get(data, "vpn")  
    
    info = {  
        "source": source,  
        "ip": ip,  
        "country": country,  
        "countryCode": country_code,  
        "region": region,  
        "city": city,  
        "org": org,  
        "asn": asn,  
        "lat": lat,  
        "lon": lon,  
        "proxy": proxy,  
        "vpn": vpn,  
        "timezone_id": tz_id,  
        "timezone_abbr": tz_abbr,  
        "timezone_time": tz_time,  
        "timezone_name": tz_name,  
        "timezone_offset": tz_offset,  
        "timezone_dst": tz_dst,  
    }  
    
    # Lấy các trường dữ liệu còn lại
    used_keys = set(["ip","query","IPv4","address","country","country_name","countryCode","country_code",  
                      "region","regionName","state","region_name","city","org","isp","asn","as","latitude","longitude",  
                      "proxy","is_proxy","vpn","timezone","time_zone","timeZone"])  
    extra = {}  
    if isinstance(data, dict):  
        for k, v in data.items():  
            if k not in used_keys and k != "extra":  
                extra[k] = v  
    info["extra"] = extra  
    return info

def get_ip_info():
    apis = list(IP_APIS)
    random.shuffle(apis)
    last_err = None
    for url in apis:
        try:
            headers = {"User-Agent": "ToolAuto/IPChecker/1.0"}
            r = requests.get(url, timeout=7, headers=headers)
            
            # Xử lý trường hợp không phải JSON chuẩn
            try:
                data = r.json()
            except json.JSONDecodeError:
                text = r.text.strip()
                if text.startswith("{") or text.startswith("["):
                    # Thử lại parse nếu nó trông giống JSON
                    try:
                        data = json.loads(text)
                    except Exception:
                        data = {"raw": text}
                elif "=" in text and "ip" in text:
                    # Xử lý định dạng key=value&key=value (ví dụ: ifconfig.me)
                    try:
                        kv = dict([part.split("=",1) for part in text.split("&") if "=" in part])
                        data = kv
                    except Exception:
                        data = {"raw": text}
                else:
                    data = {"raw": text}
                    
            info = normalize_ip_data(data, url)
            if info.get("ip"):
                return info
            else:
                last_err = ("no-ip", url, data)
        except Exception as e:
            last_err = (str(e), url)
            continue
            
    return {"ip": None, "country": None, "countryCode": None, "region": None, "city": None,
            "timezone_id": None, "timezone_abbr": None, "timezone_time": None,
            "org": None, "asn": None, "lat": None, "lon": None,
            "proxy": None, "vpn": None, "source": "All failed", "extra": {}}

def check_vpn():
    # code tự check vpn ở đây
    # giả sử nó trả về True/False
    is_vpn = True   # hoặc False
    
    if is_vpn:
        return "ON"
    else:
        return "OFF"

def check_proxy():
    # tương tự cho proxy
    is_proxy = False
    return "ON" if is_proxy else "OFF"
            

def get_color(value: str) -> str:
    if not value:
        return WHITE
    v = str(value).lower()
    if "vnpt" in v: return CYAN
    if "viettel" in v: return GREEN
    if "fpt" in v: return YELLOW
    if "mobi" in v: return MAGENTA
    if "vpn" in v or "proxy" in v or "hosting" in v or "cloud" in v: return RED
    if "vietnam" in v or v == "vn": return GREEN
    if "united states" in v or v == "us": return CYAN
    if "japan" in v or v == "jp": return MAGENTA
    return WHITE

def pretty_print_ip(info: dict):
    ip = info.get("ip") or "N/A"
    country = info.get("country") or "None"
    ccode = info.get("countryCode") or "N/A"
    region = info.get("region") or "N/A"
    city = info.get("city") or "N/A"
    org = info.get("org") or "N/A"
    asn = info.get("asn") or "N/A"
    lat = info.get("lat")
    lon = info.get("lon")

    # Kiểm tra proxy và vpn  
    proxy = info.get("proxy") or "None"
    vpn = info.get("vpn") or "None"  

    tz_id = info.get("timezone_id") or "N/A"  
    tz_abbr = info.get("timezone_abbr") or ""  
    tz_time = info.get("timezone_time") or "N/A"  
    tz_name = info.get("timezone_name") or ""  
    tz_offset = info.get("timezone_offset")  
    tz_dst = info.get("timezone_dst")  
  
    # In ra thông tin IP, Proxy, VPN  
    print(f"{CYAN}📡 Nguồn API   : {info.get('source')}{RESET}")  
    print(f"{YELLOW}🌐 IP hiện tại : {get_color(ip)}{ip}{RESET}  {YELLOW}📌 Quốc gia : {get_color(country)}{country} ({ccode}){RESET}")  
    print(f"{YELLOW}🏢 Nhà mạng    : {get_color(org)}{org}{RESET}  {YELLOW}🔹 AS : {get_color(asn)}{asn}{RESET}")  
    print(f"{YELLOW}🏙️ Thành phố   : {CYAN}{city}{RESET}  {YELLOW}🗺️ Vùng : {CYAN}{region}{RESET}")  
  
    tz_line = f"{tz_id}"  
    if tz_abbr:  
        tz_line += f" ({tz_abbr})"  
    print(f"{CYAN}⏰ Múi giờ     : {tz_line}{RESET}")  
  
    if tz_time != "N/A":  
        print(f"{CYAN}   🕒 Giờ hiện tại : {tz_time}{RESET}")  
    if tz_name:  
        print(f"{CYAN}   📛 Tên TZ     : {tz_name}{RESET}")  
    if tz_offset is not None:  
        print(f"{CYAN}⏰ Offset      : {tz_offset}{RESET}")  
    if tz_dst is not None:  
        print(f"{CYAN}🌙 DST         : {tz_dst}{RESET}")  
    if lat is not None or lon is not None:  
        print(f"{MAGENTA}📍 Tọa độ      : {lat}, {lon}{RESET}")  
        

    
print()

# --- QUẢN LÝ AUTH (GOLIKE) ---

def save_auth(token, t_val):
    try:
        with open(AUTH_FILE, "w", encoding="utf-8") as f:
            json.dump({"token": token, "t": t_val}, f, indent=2)
    except Exception:
        pass

def load_auth():
    if not os.path.exists(AUTH_FILE):
        return None
    try:
        with open(AUTH_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def make_headers(token, device="android", t=None):
    if device == "ios":
        ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)"
    else:
        ua = "Mozilla/5.0 (Linux; Android 10; SM-G970F)"
    
    h = {"authorization": f"Bearer {token}", "user-agent": ua, "accept": "application/json"}
    if t:
        h["t"] = t
    return h

def get_user_info_api(token, t=None):
    try:
        # Sử dụng requests để dễ quản lý timeout và lỗi hơn
        r = requests.get("https://gateway.golike.net/api/users/me", headers=make_headers(token, "android", t), timeout=10)
        r.raise_for_status() # Raise exception for bad status codes (4xx or 5xx)
        return r.json().get("data", {})
    except Exception:
        return {}

def acc_instagram_api(token, t=None):
    try:
        # Sử dụng requests
        r = requests.get("https://gateway.golike.net/api/instagram-account", headers=make_headers(token, "android", t), timeout=10)
        r.raise_for_status()
        return r.json().get("data", [])
    except Exception:
        return []

def do_job_for_account(account, token, t=None):
    # Đây là hàm placeholder cho logic chạy job thực tế
    print(f"{CYAN}➡ Bắt đầu lấy job cho account {account.get('instagram_username')} (ID: {account.get('id')})...{RESET}")
    time.sleep(1)
    print(f"{GREEN}✅ Hoàn tất job cho {account.get('instagram_username')}{RESET}\n")

# --- XÁC THỰC KEY & MONITOR IP ---

def require_link_and_key():
    banner()
    ip_info = get_ip_info()
    
    if ip_info:
        pretty_print_ip(ip_info)
        cur_ip = ip_info.get("ip")
        cur_country = ip_info.get("country")
        cur_country_code = ip_info.get("countryCode")
        cur_city = ip_info.get("city")
        cur_org = ip_info.get("org")
        cur_as = ip_info.get("asn")
        
        saved = load_key_file()
        
        # --- KIỂM TRA KEY CŨ ---
        if saved:
            saved_key = saved.get("key")
            saved_ts = saved.get("timestamp", 0) or 0
            saved_ip = saved.get("ip")
            
            remain = KEY_TTL - (time.time() - saved_ts)
            ip_changed = (saved_ip and cur_ip and saved_ip != cur_ip)
            vpn_now = is_vpn_like(cur_org, cur_as)
            
            if saved_key and remain > 0 and not ip_changed and saved_ip == cur_ip and not vpn_now:
                # Key hợp lệ: Bắt đầu monitor và return True
                print(f"{GREEN}✅ KEY hợp lệ, còn {remaining_human(remain)}{RESET}\n")
                threading.Thread(target=monitor_ip, args=(saved_ip, saved.get("org"), saved.get("asn")), daemon=True).start()
                return True
            else:
                # Key không hợp lệ: Xóa và in ra lý do
                reasons = []
                if remain <= 0:
                    reasons.append("KEY hết hạn")
                if ip_changed:
                    reasons.append(f"Đổi IP ({saved_ip} → {cur_ip})")
                if vpn_now:
                    reasons.append(f"Phát hiện VPN/Hosting ({cur_org})")
                
                if reasons:
                    print(f"{RED}⚠️ {', '.join(reasons)} → KEY cũ đã bị xoá!{RESET}\n")
                delete_key_file()
                
        # --- KIỂM TRA KEY LƯU TRONG KEY_PLAIN_FILE ---
        plain = load_plain_key()
        if plain and cur_ip:
            # Nếu có KEY trong file plain, nạp và lưu lại với IP hiện tại (coi như mới nhập)
            save_key_to_file(plain, cur_ip, cur_country, cur_org, cur_as)
            print(f"{GREEN}✅ Đã nạp KEY từ {KEY_PLAIN_FILE} và lưu (24h){RESET}\n")
            threading.Thread(target=monitor_ip, args=(cur_ip, cur_org, cur_as), daemon=True).start()
            return True
        elif plain and not cur_ip:
             print(f"{YELLOW}⚠️ Không thể lấy IP hiện tại. Không thể dùng {KEY_PLAIN_FILE} lúc này.{RESET}\n")

    # --- YÊU CẦU NHẬP KEY MỚI ---
    
    # 1. Tạo key ngẫu nhiên và link rút gọn
    new_key = generate_key()
    full_url = DESTINATION + new_key
    short_url = create_short_link(API_KEY, full_url)
    
    print(f"{CYAN}🔗 Vui lòng vượt link để tiếp tục...{RESET}")
    print(f"{YELLOW}👉 Vượt Link Để Sử Dụng: {CYAN}{short_url}{RESET}")
    print(f"{YELLOW}   (Mở link, nhận KEY, paste vào đây){RESET}\n")
    
    gen_ip = cur_ip # IP trước khi nhập key
    gen_org = cur_org
    gen_as = cur_as
    
    raw = input(f"{YELLOW}🔑 Nhập KEY  (nhập key hoặc Nhập Cả Link): {RESET}").strip()
    if not raw:
        print(f"{RED}✖ Bạn chưa nhập gì. Hủy.{RESET}\n")
        return False
        
    key_input = extract_key_from_input(raw)
    
    # 2. Kiểm tra lại IP sau khi nhập key
    ip_check = get_ip_info()
    after_ip = ip_check.get("ip")
    after_org = ip_check.get("org")
    after_as = ip_check.get("asn")
    country_after = ip_check.get("country")
    
    # 3. Kiểm tra điều kiện
    
    # Điều kiện A: Đổi IP
    if gen_ip and after_ip and gen_ip != after_ip:
        print(f"\n{RED}⚠️ Đổi IP trong lúc nhập KEY ({gen_ip} → {after_ip}) — KHÔNG chấp nhận!{RESET}\n")
        return False
        
    # Điều kiện B: Phát hiện VPN/Hosting
    if is_vpn_like(after_org, after_as):
        print(f"\n{RED}⚠️ Phát hiện VPN/Hosting/Proxy ({after_org}) — KHÔNG chấp nhận!{RESET}\n")
        return False
        
    # Điều kiện C: KEY khớp KEY tự sinh
    if key_input == new_key:
        save_key_to_file(key_input, after_ip or gen_ip, country_after, after_org, after_as)
        print(f"\n{GREEN}✅ KEY hợp lệ — tiếp tục (24h hiệu lực){RESET}\n")
        threading.Thread(target=monitor_ip, args=(after_ip or gen_ip, after_org, after_as), daemon=True).start()
        return True
        
    # Điều kiện D: KEY không khớp nhưng có định dạng KEY
    elif key_input and key_input.startswith(KEY_PREFIX + "_"):
        if after_ip and gen_ip and after_ip == gen_ip:
            confirm = input(f"{YELLOW}⚠️ KEY không khớp key tự sinh. Bạn muốn lưu key này (y/N)? {RESET}").strip().lower()
            if confirm == "y":
                save_key_to_file(key_input, after_ip or gen_ip, country_after, after_org, after_as)
                print(f"\n{GREEN}✅ KEY đã lưu — tiếp tục (24h){RESET}\n")
                threading.Thread(target=monitor_ip, args=(after_ip or gen_ip, after_org, after_as), daemon=True).start()
                return True
            else:
                print(f"{RED}✖ Không lưu key. Vui lòng vượt link đúng key.{RESET}\n")
                return False
        else:
            print(f"{RED}✖ IP không khớp khi cấp key ({gen_ip} ≠ {after_ip}).{RESET}\n")
            return False
            
    # Điều kiện E: KEY sai
    else:
        print(f"\n{RED}✖ KEY sai (ko hợp lệ). Vui lòng vượt link lại.{RESET}\n")
        return False

def monitor_ip(original_ip, original_org, original_as):
    global monitor_lock
    while True:
        try:
            time.sleep(3)
            now = get_ip_info()
            ip_now = now.get("ip")
            org_now = now.get("org")
            asn_now = now.get("asn")
            
            if not ip_now:
                continue
                
            with monitor_lock:
                # 1. Kiểm tra đổi IP
                if original_ip and ip_now != original_ip:
                    print(f"\n{RED}⚠️ Phát hiện đổi IP ({original_ip} → {ip_now}) — KEY sẽ bị xoá!{RESET}", flush=True)
                    delete_key_file()
                    force_rekey_event.set()
                    # Cập nhật để tránh lặp lại cảnh báo liên tục
                    original_ip = ip_now 
                    original_org = org_now
                    original_as = asn_now
                    continue
                    
                # 2. Kiểm tra VPN
                if is_vpn_like(org_now, asn_now):
                    print(f"\n{RED}❌ Phát hiện VPN/Hosting/Proxy ({org_now}) — KEY sẽ bị xoá!{RESET}", flush=True)
                    delete_key_file()
                    force_rekey_event.set()
                    # Cập nhật để tránh lặp lại cảnh báo liên tục
                    original_ip = ip_now
                    original_org = org_now
                    original_as = asn_now
                    continue
        except Exception:
            time.sleep(2)
            continue

# --- HÀM CHÍNH (UI) ---

def UI():
    # --- Vòng lặp lấy KEY ---
    while True:
        ok = require_link_and_key()
        if ok:
            break
        
        ans = input(f"{YELLOW}Bạn có muốn thử lấy KEY lại không? (Y/n): {RESET}").strip().lower()
        if ans == "n":
            print(f"{RED}✖ Thoát do chưa có KEY hợp lệ.{RESET}")
            return
            
    # --- Đăng nhập GoLike ---
    saved_auth = load_auth()
    token = None
    t_val = None
    
    if saved_auth:
        token = saved_auth.get("token")
        t_val = saved_auth.get("t")
        
        if token and t_val:
            use_old = input(f"{YELLOW}👉 Đã có authorization cũ, dùng lại không? (Y/N): {RESET}").strip().lower()
            if use_old == "y":
                test_user = get_user_info_api(token, t_val)
                if test_user:
                    print(f"{GREEN}✅ Đăng nhập thành công!{RESET}\n")
                else:
                    print(f"{RED}⚠️ Token cũ đã hết hạn/không hợp lệ.{RESET}")
                    token = None
                    t_val = None

    if not token:
        token = input(f"{YELLOW}👉 Nhập authorization: {RESET}").strip().replace("Bearer ", "")
        t_val = input(f"{YELLOW}👉 Nhập T (Phải Nhập T mới sài dc): {RESET}").strip() or None
        
        if not token or not t_val:
            print(f"{RED}⚠️ Authorization hoặc T không được bỏ trống. Hủy.{RESET}")
            return
            
        user_check = get_user_info_api(token, t_val)
        if not user_check:
            print(f"{RED}⚠️ Token hoặc T không hợp lệ!{RESET}")
            return
            
        save_choice = input(f"{YELLOW}👉 Lưu auth cho lần sau? (Y/N): {RESET}").strip().lower()
        if save_choice == "y":
            save_auth(token, t_val)
        print(f"{GREEN}✅ Đăng nhập thành công!{RESET}\n")

    user = get_user_info_api(token, t_val)
    if not user:
        print(f"{RED}⚠️ Không thể lấy thông tin người dùng. Thoát.{RESET}")
        return

    # --- Vòng lặp Menu chính ---
    while True:
        # Kiểm tra sự kiện yêu cầu KEY lại từ Monitor IP
        if force_rekey_event.is_set():
            print(f"\n{RED}⚠️ Monitor: KEY đã bị xóa do đổi IP/Phát hiện VPN. Vui lòng vượt link để lấy lại KEY!{RESET}\n")
            force_rekey_event.clear()
            
            # Bắt buộc lấy KEY lại
            while True:
                ok = require_link_and_key()
                if ok:
                    break
                ans = input(f"{YELLOW}Bạn có muốn thử lấy KEY lại không? (Y/n): {RESET}").strip().lower()
                if ans == "n":
                    print(f"{RED}✖ Thoát do chưa có KEY hợp lệ.{RESET}")
                    return
        
        banner(user)
        print(f"""
{YELLOW}====== MENU ======{RESET}
{GREEN}1{RESET} - Xem danh sách Instagram đã liên kết và chạy job
{GREEN}0{RESET} - Thoát
""")
        ch = input(f"{YELLOW}👉 Nhập lựa chọn: {RESET}").strip()
        
        if ch == "1":
            accs = acc_instagram_api(token, t_val)
            if accs:
                print(f"{CYAN}📌 Danh sách Instagram account đã liên kết:{RESET}")
                for i, a in enumerate(accs, 1):
                    uid = a.get("id")
                    uname = a.get("instagram_username")
                    print(f"{GREEN}{i}{RESET} | ID: {uid} | User: {CYAN}{uname}{RESET}")
                    
                choice = input(f"{YELLOW}👉 Nhập số account muốn chọn (vd: 1,3,5 hoặc all): {RESET}").strip()
                selected = []
                
                if choice.lower() == "all":
                    selected = accs
                else:
                    try:
                        idxs = [int(x) for x in choice.split(",")]
                        selected = [accs[i-1] for i in idxs if 0 < i <= len(accs)]
                    except Exception:
                        print(f"{RED}⚠️ Lựa chọn không hợp lệ!{RESET}")
                        
                if selected:
                    print(f"{CYAN}➡ Đã chọn {len(selected)} account. Bắt đầu job...{RESET}")
                    for acc in selected:
                        do_job_for_account(acc, token, t_val)
                else:
                    print(f"{RED}⚠️ Không có account nào được chọn!{RESET}")
            else:
                print(f"{RED}⚠️ Chưa liên kết Instagram nào.{RESET}")
            
            input(f"\n{YELLOW}👉 Enter để quay lại menu...{RESET}")
            
        elif ch == "0":
            print(f"{CYAN}👋 Tạm biệt!{RESET}")
            sys.exit(0)
            
        else:
            print(f"{RED}⚠️ Lựa chọn không hợp lệ!{RESET}")
            time.sleep(1)

# --- KHỞI CHẠY CHƯƠNG TRÌNH ---
if __name__ == "__main__":
    # Đã sửa lỗi thiếu gạch dưới và lỗi thụt lề
    try:
        # Kiểm tra biến KEY_PREFIX đã được định nghĩa chưa (đã định nghĩa ở trên)
        KEY_PREFIX
    except NameError:
        KEY_PREFIX = "phonganh20703" # Fallback nếu chưa định nghĩa

    if not ping_test():
        print(f"{RED}⚠️ Không có Internet!{RESET}")
        sys.exit(1)
        
    UI()
