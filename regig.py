import os
import time
import threading
import subprocess
import base64
import sys
import random
import re
from datetime import datetime
from xml.dom.minidom import parse
import json
import uuid
import platform

# ========== CÀI ĐẶT MÀU RGB TOÀN CỤC ==========
class Colors:
    # Màu chính
    PRIMARY = "\033[38;2;255;100;150m"
    SECONDARY = "\033[38;2;100;200;255m"
    SUCCESS = "\033[38;2;0;255;127m"
    ERROR = "\033[38;2;255;50;50m"
    WARNING = "\033[38;2;255;200;50m"
    INFO = "\033[38;2;100;255;200m"
    DEBUG = "\033[38;2;150;150;255m"
    
    # Màu banner
    BANNER1 = "\033[38;2;153;51;255m"
    BANNER2 = "\033[38;2;170;70;255m"
    BANNER3 = "\033[38;2;190;90;255m"
    BANNER4 = "\033[38;2;210;110;240m"
    BANNER5 = "\033[38;2;230;130;220m"
    BANNER6 = "\033[38;2;240;150;200m"
    BANNER7 = "\033[38;2;200;200;255m"
    BANNER8 = "\033[38;2;150;230;255m"
    BANNER9 = "\033[38;2;120;255;230m"
    
    # Màu cho các thành phần
    DEVICE_INFO = "\033[38;2;255;200;140m"
    KEY = "\033[38;2;200;160;255m"
    VALUE = "\033[38;2;120;255;220m"
    LINE = "\033[38;2;190;235;210m"
    TITLE = "\033[38;2;255;215;0m"
    NUMBER = "\033[38;2;255;165;0m"
    EMAIL = "\033[38;2;100;200;255m"
    USERNAME = "\033[38;2;0;255;255m"
    PASSWORD = "\033[38;2;255;105;180m"
    TIME = "\033[38;2;200;200;200m"
    
    RESET = "\033[0m"
    
    @staticmethod
    def color_text(text, color):
        return f"{color}{text}{Colors.RESET}"

# Cài đặt thư viện tự động
try:
    import requests
    import numpy as np
    import cv2
except ImportError:
    print(f"{Colors.color_text('Đang cài đặt thư viện thiếu...', Colors.WARNING)}")
    os.system("pip install numpy requests opencv-python")
    import requests
    import numpy as np
    import cv2

try:
    import uiautomator2 as u2
except ImportError:
    print(f"{Colors.color_text('Đang cài đặt uiautomator2...', Colors.WARNING)}")
    os.system("pip install uiautomator2")
    import uiautomator2 as u2

# ========== BANNER VÀ MÀU RGB ==========
def banner():
    os.system('clear' if os.name == 'posix' else 'cls')

    # ===== BANNER ASCII =====
    print(f"""{Colors.BANNER1}▄▄▄█████▓ █    ██   ██████    ▄▄▄█████▓ ▒█████   ▒█████   ██▓
{Colors.BANNER2}▓  ██▒ ▓▒ ██  ▓██▒▒██    ▒    ▓  ██▒ ▓▒▒██▒  ██▒▒██▒  ██▒▓██▒
{Colors.BANNER3}▒ ▓██░ ▒░▓██  ▒██░░ ▓██▄      ▒ ▓██░ ▒░▒██░  ██▒▒██░  ██▒▒██░
{Colors.BANNER4}░ ▓██▓ ░ ▓▓█  ░██░  ▒   ██▒   ░ ▓██▓ ░ ▒██   ██░▒██   ██░▒██░
{Colors.BANNER5}  ▒██▒ ░ ▒▒█████▓ ▒██████▒▒     ▒██▒ ░ ░ ████▓▒░░ ████▓▒░░██████▒
{Colors.BANNER6}  ▒ ░░   ░▒▓▒ ▒ ▒ ▒ ▒▓▒ ▒ ░     ▒ ░░   ░ ▒░▒░▒░ ░ ▒░▒░▒░ ░ ▒░▓  ░
{Colors.BANNER7}    ░    ░░▒░ ░ ░ ░ ░▒  ░ ░       ░      ░ ▒ ▒░   ░ ▒ ▒░ ░ ░ ▒  ░
{Colors.BANNER8}  ░       ░░░ ░ ░ ░  ░  ░       ░      ░ ░ ░ ▒  ░ ░ ░ ▒    ░ ░
{Colors.BANNER9}            ░           ░                  ░ ░      ░ ░      ░  ░
{Colors.RESET}""")

    # ===== INFO =====
    print(f"{Colors.DEVICE_INFO}[</>] {Colors.KEY}ADMIN: {Colors.VALUE}NHƯ ANH ĐÃ THẤY EM   {Colors.DEVICE_INFO}Phiên Bản: {Colors.VALUE}v3.26{Colors.RESET}")
    print(f"{Colors.DEVICE_INFO}[</>] {Colors.KEY}Nhóm Telegram: {Colors.VALUE}https://t.me/se_meo_bao_an{Colors.RESET}")

    print(f"{Colors.LINE}{'─'*70}{Colors.RESET}")

    # ===== THÔNG TIN THIẾT BỊ =====
    width = 70
    print(f"{Colors.TITLE}{' THÔNG TIN THIẾT BỊ '.center(width)}{Colors.RESET}")
    print(f"{Colors.LINE}{'─'*width}{Colors.RESET}")

    print(f"{Colors.DEVICE_INFO}[</>] {Colors.KEY}Hệ điều hành: {Colors.VALUE}{platform.system()}{Colors.RESET}")

    try:
        info_ip = requests.get("http://ip-api.com/json", timeout=5)
        if info_ip.status_code == 200:
            data = info_ip.json()
            print(f"{Colors.DEVICE_INFO}[</>] {Colors.KEY}IP: {Colors.VALUE}{data.get('query')}{Colors.RESET}")
            print(f"{Colors.DEVICE_INFO}[</>] {Colors.KEY}Khu Vực: {Colors.VALUE}{data.get('regionName')}{Colors.RESET}")
            print(f"{Colors.DEVICE_INFO}[</>] {Colors.KEY}ISP: {Colors.VALUE}{data.get('isp')}{Colors.RESET}")
            print(f"{Colors.DEVICE_INFO}[</>] {Colors.KEY}Nhà Mạng: {Colors.VALUE}{data.get('org')}{Colors.RESET}")
        else:
            raise Exception()
    except KeyboardInterrupt:
        sys.exit(0)
    except:
        print(f"{Colors.DEVICE_INFO}[</>] {Colors.KEY}IP: {Colors.WARNING}Không xác định{Colors.RESET}")
        print(f"{Colors.DEVICE_INFO}[</>] {Colors.KEY}Khu Vực: {Colors.WARNING}Không xác định{Colors.RESET}")
        print(f"{Colors.DEVICE_INFO}[</>] {Colors.KEY}ISP: {Colors.WARNING}Không xác định{Colors.RESET}")
        print(f"{Colors.DEVICE_INFO}[</>] {Colors.KEY}Nhà Mạng: {Colors.WARNING}Không xác định{Colors.RESET}")

    print(f"{Colors.LINE}{'─'*70}{Colors.RESET}")
    print()

# ========== HÀM LƯU TÀI KHOẢN ==========
def save_account(serial, email, password, username, full_name, mode="auto"):
    """
    Lưu thông tin tài khoản vào file trong folder Instagram_reg
    Định dạng: email|password|username
    """
    folder_name = "Instagram_reg"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"{Colors.color_text(f'Đã tạo folder: {folder_name}', Colors.SUCCESS)}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{folder_name}/account_{serial.replace(':', '_').replace('.', '_')}_{timestamp}.txt"
    
    content = f"""========================================
THÔNG TIN TÀI KHOẢN INSTAGRAM
========================================
Ngày tạo: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Thiết bị: {serial}
Chế độ: {mode}
----------------------------------------
Email:    {email}
Password: {password}
Username: {username}
Họ tên:   {full_name}
----------------------------------------
Định dạng nhanh: {email}|{password}|{username}
========================================
"""
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"{Colors.color_text(f'[{serial}] Đã lưu tài khoản vào: {filename}', Colors.SUCCESS)}")
        
        summary_file = f"{folder_name}/ALL_ACCOUNTS.txt"
        with open(summary_file, 'a', encoding='utf-8') as f:
            f.write(f"{email}|{password}|{username}|{full_name}|{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        print(f"{Colors.color_text(f'[{serial}] Đã thêm vào file tổng hợp: {summary_file}', Colors.SUCCESS)}")
        
        return filename
    except Exception as e:
        print(f"{Colors.color_text(f'[{serial}] Lỗi khi lưu file: {e}', Colors.ERROR)}")
        return None

# 1. Tích hợp API Mail.tm
class MailService:
    def __init__(self):
        self.base_url = "https://api.mail.tm"
        self.token = None
        self.email_address = None
        self.account_id = None
        self.domain = None
    
    def get_domain(self):
        """Lấy domain còn hoạt động từ API."""
        try:
            response = requests.get(f"{self.base_url}/domains", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('hydra:totalItems', 0) > 0:
                    self.domain = data['hydra:member'][0]['domain']
                    return self.domain
        except Exception:
            pass
        return None

    def create_account(self, address=None):
        """Tạo tài khoản email mới ngẫu nhiên hoặc theo username được cung cấp."""
        if not self.domain:
            self.get_domain()
            if not self.domain:
                raise Exception("Không thể lấy domain từ Mail.tm")

        if address:
            account_name = address
        else:
            account_name = f"user_{uuid.uuid4().hex[:8]}"
            
        password = "TempPass123!"

        payload = {
            "address": f"{account_name}@{self.domain}",
            "password": password
        }

        try:
            response = requests.post(f"{self.base_url}/accounts", json=payload, timeout=10)
            if response.status_code == 201:
                account_data = response.json()
                self.account_id = account_data['id']
                self.email_address = account_data['address']
                print(f"{Colors.color_text(f'Đã tạo tài khoản email: {self.email_address}', Colors.SUCCESS)}")
                return self.email_address
        except Exception:
            pass
        return None

    def authenticate(self, email=None, password="TempPass123!"):
        """Đăng nhập để lấy token. Hỗ trợ email tùy chỉnh."""
        if email:
            self.email_address = email
            
        if not self.email_address:
            raise Exception("Chưa có địa chỉ email. Vui lòng tạo tài khoản trước.")

        payload = {
            "address": self.email_address,
            "password": password
        }

        try:
            response = requests.post(f"{self.base_url}/token", json=payload, timeout=10)
            if response.status_code == 200:
                auth_data = response.json()
                self.token = auth_data['token']
                print(f"{Colors.color_text(f'Đăng nhập vào mailbox thành công: {self.email_address}', Colors.SUCCESS)}")
                return True
        except Exception:
            pass
        return False

    def get_otp_code(self, timeout=120):
        """Lấy mã OTP từ email Instagram."""
        if not self.token:
            return None

        headers = {"Authorization": f"Bearer {self.token}"}
        start_time = time.time()
        last_message_id = None
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/messages", headers=headers, timeout=10)
                if response.status_code == 200:
                    messages_data = response.json()
                    messages = messages_data.get('hydra:member', [])

                    for msg in messages:
                        subject = msg.get('subject', '')
                        from_addr = msg.get('from', {}).get('address', '')
                        
                        if ('Instagram' in subject or 
                            'Instagram' in from_addr or
                            'security' in subject.lower() or
                            'confirm' in subject.lower() or
                            'code' in subject.lower()):
                            
                            if msg.get('id') != last_message_id:
                                last_message_id = msg['id']
                                
                                detail_response = requests.get(f"{self.base_url}/messages/{msg['id']}", headers=headers, timeout=10)
                                if detail_response.status_code == 200:
                                    email_detail = detail_response.json()
                                    body_text = email_detail.get('text', '')
                                    if not body_text and email_detail.get('html'):
                                        body_text = re.sub('<[^<]+?>', '', email_detail['html'][0] if isinstance(email_detail['html'], list) else email_detail['html'])
                                    
                                    otp_match = re.search(r'\b(\d{6})\b', body_text)
                                    if otp_match:
                                        return otp_match.group(1)

            except Exception:
                pass

            time.sleep(5)

        return None

# 2. Cơ sở dữ liệu Tên người dùng
class VietnameseNameGenerator:
    def __init__(self):
        self.FIRST_NAMES = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"]
        self.MIDDLE_NAMES = ["Văn", "Thị", "Minh", "Hoàng", "Anh", "Bảo", "Gia", "Khánh", "Ngọc", "Phương", "Quốc", "Thanh", "Thùy", "Xuân"]
        self.LAST_NAMES_MALE = ["An", "Bình", "Cường", "Dũng", "Đạt", "Đức", "Hải", "Hiếu", "Hùng", "Huy", "Khoa", "Lâm", "Long", "Minh", "Nam", "Phúc", "Quân", "Quang", "Sơn", "Thành", "Thắng", "Tuấn", "Việt", "Vinh"]
        self.LAST_NAMES_FEMALE = ["Anh", "Bích", "Chi", "Diệp", "Dung", "Giang", "Hà", "Hạnh", "Hiền", "Hoa", "Huyền", "Lan", "Linh", "Ly", "Mai", "My", "Nga", "Ngân", "Nhi", "Nhung", "Oanh", "Phương", "Quỳnh", "Thảo", "Trang", "Trinh", "Vân", "Vy"]
    
    def generate_name(self):
        first = random.choice(self.FIRST_NAMES)
        middle = random.choice(self.MIDDLE_NAMES)
        gender = random.choice(['male', 'female'])
        if gender == 'male':
            last = random.choice(self.LAST_NAMES_MALE)
        else:
            last = random.choice(self.LAST_NAMES_FEMALE)

        full_name = f"{first} {middle} {last}".strip()
        username = self.create_username(full_name)
        return full_name, username

    def create_username(self, full_name):
        cleaned_name = re.sub(r'[^a-zA-Z\s]', '', full_name.lower()).replace(' ', '')
        suffix = random.randint(10, 9999)
        username = f"{cleaned_name}_{suffix}"
        return username

# 3. Cơ chế tạo Mật khẩu Bảo mật & Ngẫu nhiên
def generate_secure_password():
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    return "".join(random.choice(chars) for _ in range(random.randint(10, 14)))

# ========== HÀM NHẬP OTP THỦ CÔNG (CHỜ NGƯỜI DÙNG) ==========
def wait_for_manual_otp(serial, email_address, timeout=300):
    """Chờ người dùng nhập OTP thủ công từ bàn phím."""
    print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
    print(f"{Colors.color_text(f'[{serial}]  ĐANG CHỜ NHẬP OTP THỦ CÔNG', Colors.WARNING)}")
    print(f"{Colors.color_text('─'*70, Colors.LINE)}")
    print(f"{Colors.KEY} Email đăng ký: {Colors.EMAIL}{email_address}{Colors.RESET}")
    print(f"{Colors.INFO} Vui lòng kiểm tra email và nhập mã OTP bên dưới{Colors.RESET}")
    print(f"{Colors.INFO} Thời gian chờ tối đa: {timeout} giây{Colors.RESET}")
    print(f"{Colors.color_text('─'*70, Colors.LINE)}")
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            remaining = timeout - int(time.time() - start_time)
            if remaining % 30 == 0 and remaining > 0:
                print(f"{Colors.color_text(f' Còn {remaining}s để nhập OTP...', Colors.INFO)}")
            
            otp_input = input(f"\n{Colors.KEY}>> Nhập mã OTP (6 số) hoặc 'q' để thoát: {Colors.RESET}").strip()
            
            if otp_input.lower() == 'q':
                return None
            
            if otp_input.isdigit() and len(otp_input) == 6:
                print(f"\n{Colors.color_text(f' [{serial}] Đã nhận OTP: {otp_input}', Colors.SUCCESS)}")
                return otp_input
            else:
                print(f"{Colors.color_text(f' OTP không hợp lệ! Cần 6 chữ số.', Colors.ERROR)}")
                
        except (EOFError, KeyboardInterrupt):
            return None
    
    return None

# Hàm chạy lệnh ADB an toàn
def run_adb_command(serial, command, timeout=10):
    """Chạy lệnh ADB an toàn với subprocess"""
    try:
        full_cmd = f"adb -s {serial} {command}"
        result = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except Exception:
        return -1, "", "Error"

# ========== MODULE ROM DETECTOR ==========
class ROMDetector:
    def __init__(self, serial):
        self.serial = serial
        self.manufacturer = ""
        self.brand = ""
        self.display_id = ""
        self.detect()

    def _getprop(self, prop):
        try:
            res = subprocess.run(
                f"adb -s {self.serial} shell getprop {prop}",
                shell=True, capture_output=True, text=True, timeout=5
            )
            return res.stdout.strip().lower()
        except Exception:
            return ""

    def detect(self):
        self.manufacturer = self._getprop("ro.product.manufacturer")
        self.brand = self._getprop("ro.product.brand")
        self.display_id = self._getprop("ro.build.display.id")
        
        if not self.manufacturer:
            self.manufacturer = self.brand

    def is_match(self, *keywords):
        combined = f"{self.manufacturer} {self.brand} {self.display_id}"
        return any(kw.lower() in combined for kw in keywords)

    @property
    def is_xiaomi(self):
        return self.is_match("xiaomi", "redmi", "poco", "miui", "hyperos")

    @property
    def is_samsung(self):
        return self.is_match("samsung", "one ui")

    @property
    def is_oppo(self):
        return self.is_match("oppo", "realme", "coloros")

    @property
    def is_vivo(self):
        return self.is_match("vivo", "funtouch", "originos")

    @property
    def is_huawei(self):
        return self.is_match("huawei", "honor", "emui", "magicos")

    @property
    def is_oneplus(self):
        return self.is_match("oneplus", "oxygenos", "hydrogenos")

    @property
    def is_nubia(self):
        return self.is_match("nubia", "redmagic")

    @property
    def is_google(self):
        return self.is_match("google", "pixel")

    @property
    def is_asus(self):
        return self.is_match("asus", "zenfone", "rog")

# ========== MODULE APP CLEANER (UI-BASED) ==========
class AppCleaner:
    def __init__(self, d, serial):
        self.d = d
        self.serial = serial
        self.rom = ROMDetector(serial)

    def clear_instagram_data(self):
        print(f"{Colors.color_text(f'[{self.serial}] ========== UI-BASED CLEAR DATA ==========', Colors.TITLE)}")
        
        print(f"{Colors.color_text(f'[{self.serial}] Force stopping Instagram...', Colors.INFO)}")
        self.d.app_stop("com.instagram.android")
        time.sleep(1.5)

        if not self._goto_app_info("com.instagram.android"):
            self._open_settings_and_search("Instagram")
        
        time.sleep(2.5)

        if not self._find_and_click_storage():
            return False
        
        time.sleep(2)

        if not self._find_and_click_clear_data():
            return False

        self._handle_confirm_popup()
        
        time.sleep(1.5)
        return True

    def _goto_app_info(self, package_name):
        try:
            cmd = f"adb -s {self.serial} shell am start -a android.settings.APPLICATION_DETAILS_SETTINGS -d package:{package_name}"
            subprocess.run(cmd, shell=True, timeout=8)
            return True
        except Exception:
            return False

    def _open_settings_and_search(self, app_name):
        try:
            self.d.press("home")
            time.sleep(0.5)
            self.d.app_start("com.android.settings")
            time.sleep(2)

            search_clicked = False
            for sel in [
                {"resourceId": "com.android.settings:id/search_action_bar"},
                {"descriptionMatches": r"(?i).*search.*|.*tìm.*"},
                {"resourceIdMatches": r".*search.*"},
            ]:
                try:
                    elem = self.d(**sel)
                    if elem.exists(timeout=2):
                        elem.click()
                        search_clicked = True
                        break
                except:
                    continue
            
            if not search_clicked:
                self.d.click(0.9, 0.05)
            
            time.sleep(1)
            self.d.send_keys(app_name)
            time.sleep(2)

            for sel in [
                {"textContains": "Instagram"},
                {"descriptionContains": "Instagram"},
                {"textContains": "instagram"},
            ]:
                try:
                    elem = self.d(**sel)
                    if elem.exists(timeout=2):
                        elem.click()
                        time.sleep(2)
                        return
                except:
                    continue
        except Exception:
            pass

    def _find_and_click_storage(self):
        selectors = [
            {"textMatches": r"(?i).*(storage|dung lượng|bộ nhớ|storage & cache).*"},
            {"descriptionMatches": r"(?i).*(storage|dung lượng|bộ nhớ).*"},
            {"resourceIdMatches": r".*storage.*|.*storage_settings.*"},
        ]
        
        self._scroll_down()

        for sel in selectors:
            try:
                elem = self.d(**sel)
                if elem.exists(timeout=3):
                    elem.click()
                    return True
            except:
                continue

        if self.rom.is_xiaomi:
            self._click_relative(0.5, 0.55)
        elif self.rom.is_samsung:
            self._click_relative(0.5, 0.65)
        else:
            self._click_relative(0.5, 0.6)
        return True

    def _find_and_click_clear_data(self):
        selectors = [
            {"textMatches": r"(?i).*(clear data|clear storage|xóa dữ liệu|xóa bộ nhớ).*"},
            {"descriptionMatches": r"(?i).*(clear|delete|xóa).*(data|storage|dữ liệu|bộ nhớ).*"},
            {"resourceIdMatches": r".*clear.*data.*|.*clear_data.*"},
        ]
        
        self._scroll_down()

        for sel in selectors:
            try:
                elem = self.d(**sel)
                if elem.exists(timeout=3):
                    elem.click()
                    return True
            except:
                continue

        try:
            if self.d(descriptionMatches=r"(?i).*clear.*|.*delete.*|.*xóa.*").exists(timeout=2):
                self.d(descriptionMatches=r"(?i).*clear.*|.*delete.*|.*xóa.*").click()
                return True
        except:
            pass

        self._click_relative(0.5, 0.75)
        return True

    def _handle_confirm_popup(self):
        time.sleep(1.5)
        ok_selectors = [
            {"textMatches": r"(?i)^(ok|yes|delete|xóa|clear|đồng ý|xác nhận)$"},
            {"resourceId": "android:id/button1"},
            {"resourceIdMatches": r".*ok_button|.*confirm_button|.*button1.*"},
            {"text": "OK"},
            {"text": "DELETE"},
            {"text": "XÓA"},
        ]
        
        for sel in ok_selectors:
            try:
                elem = self.d(**sel)
                if elem.exists(timeout=2):
                    elem.click()
                    return
            except:
                continue
        
        self.d.press("enter")

    def _scroll_down(self):
        try:
            size = self.d.window_size()
            self.d.swipe(
                size[0] * 0.5, size[1] * 0.8,
                size[0] * 0.5, size[1] * 0.3,
                duration=0.3
            )
            time.sleep(1)
        except:
            pass

    def _click_relative(self, x_percent, y_percent):
        try:
            size = self.d.window_size()
            x = int(size[0] * x_percent)
            y = int(size[1] * y_percent)
            self.d.click(x, y)
        except:
            pass

# Class Auto
class Auto:
    def __init__(self, handle):
        self.handle = handle
    
    def screen_capture(self):
        pipe = subprocess.Popen(
            f'adb -s {self.handle} exec-out screencap -p',
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            shell=True
        )
        image_bytes = pipe.stdout.read()
        image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        return image

    def changeProxy(self, ip):
        run_adb_command(self.handle, f'shell settings put global http_proxy {ip}')

    def remProxy(self):
        run_adb_command(self.handle, 'shell settings put global http_proxy :0')

    def click(self, x, y):
        run_adb_command(self.handle, f'shell input tap {x} {y}')

    def swipe(self, x1, y1, x2, y2):
        run_adb_command(self.handle, f'shell input touchscreen swipe {x1} {y1} {x2} {y2} 1000')

    def Back(self):
        run_adb_command(self.handle, 'shell input keyevent 3')

    def DeleteCache(self, package):
        run_adb_command(self.handle, f'shell pm clear {package}')

    def off(self, package):
        run_adb_command(self.handle, f'shell am force-stop {package}')

    def InputText(self, text=None, VN=None):
        if text is None and VN is not None:
            text = str(base64.b64encode(VN.encode('utf-8')))[2:-1]
            run_adb_command(self.handle, 'shell ime set com.android.adbkeyboard/.AdbIME')
            run_adb_command(self.handle, f'shell am broadcast -a ADB_INPUT_B64 --es msg {text}')
            return
        safe_text = text.replace("'", "\\'").replace('"', '\\"')
        run_adb_command(self.handle, f"shell input text '{safe_text}'")

    def showDevice(self, width: int, height: int, x: int, y: int, title: str):
        subprocess.Popen(
            f'scrcpy -s {self.handle} --window-title "{title}" --window-x {x} --window-y {y} --window-width {width} --window-height {height}',
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            shell=True
        )


def ensure_atx_agent_health(d, serial):
    try:
        d.healthcheck()
    except:
        try:
            d = u2.connect(serial)
            d.healthcheck()
        except:
            pass

def skip_avatar_screen(d, serial, auto_obj):
    print(f"{Colors.color_text(f'[{serial}] Đang bỏ qua màn hình thêm ảnh đại diện...', Colors.INFO)}")
    time.sleep(5)
    
    skip_selectors = [
        lambda: d(textMatches=r"(?i)Bỏ qua|Skip|Not now|Để sau").click_exists(timeout=5),
        lambda: d(descriptionMatches=r"(?i).*skip.*|.*bỏ qua.*|.*not now.*").click_exists(timeout=5),
        lambda: d(resourceId="com.instagram.android:id/skip_button").click_exists(timeout=5),
    ]
    
    for selector in skip_selectors:
        try:
            if selector():
                time.sleep(2)
                return True
        except:
            continue
    
    auto_obj.Back()
    time.sleep(3)
    
    try:
        if d(textMatches=r"(?i)Thêm ảnh|Add photo").exists(timeout=2):
            auto_obj.Back()
            time.sleep(2)
    except:
        pass
    
    try:
        window_size = d.window_size()
        auto_obj.click(int(window_size[0] * 0.95), int(window_size[1] * 0.05))
        time.sleep(2)
    except:
        pass
    
    try:
        if d(textMatches=r"(?i)Tiếp|Next|Skip|Bỏ qua").exists(timeout=3):
            d(textMatches=r"(?i)Tiếp|Next|Skip|Bỏ qua").click()
            time.sleep(2)
    except:
        pass
    
    return True


def GetDevices():
    try:
        output = subprocess.check_output("adb devices", shell=True).decode('utf-8')
        lines = output.strip().splitlines()
        devices = []
        for line in lines[1:]:
            if "\tdevice" in line:
                device_serial = line.split("\t")[0]
                devices.append(device_serial)
        return devices
    except Exception:
        return []

def select_devices():
    devices = GetDevices()
    if not devices:
        print(f"{Colors.color_text('Không tìm thấy thiết bị nào đang kết nối!', Colors.ERROR)}")
        return []
    print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
    print(f"{Colors.color_text(' DANH SÁCH THIẾT BỊ ĐÃ KẾT NỐI    '.center(50), Colors.TITLE)}")
    print(f"{Colors.color_text('─'*70, Colors.LINE)}")
    for i, dev in enumerate(devices):
        print(f"{Colors.NUMBER}{i + 1}. {Colors.VALUE}{dev}{Colors.RESET}")
    print(f"{Colors.NUMBER}{len(devices) + 1}. {Colors.VALUE}Chạy tất cả thiết bị{Colors.RESET}")
    print(f"{Colors.color_text('─'*70, Colors.LINE)}")
    while True:
        try:
            choice = input(f"{Colors.KEY}Nhập lựa chọn (ví dụ: 1): {Colors.RESET}")
            choice = int(choice)
            if 1 <= choice <= len(devices):
                return [devices[choice-1]]
            elif choice == len(devices) + 1:
                return devices
            else:
                print(f"{Colors.color_text('Lựa chọn không hợp lệ.', Colors.ERROR)}")
        except ValueError:
            print(f"{Colors.color_text('Vui lòng nhập số.', Colors.ERROR)}")

# ========== MENU CHỌN CHẾ ĐỘ ==========
def select_mode():
    print(f"{Colors.NUMBER}1. {Colors.VALUE}TỰ ĐỘNG HOÀN TOÀN  \033[97m[ Dùng email Mail.tm tự tạo ]{Colors.RESET}")
    print(f"{Colors.NUMBER}2. {Colors.VALUE}NHẬP TAY EMAIL & OTP \033[97m[ Dùng email của bạn ]{Colors.RESET}")
    print(f"{Colors.color_text('─'*70, Colors.LINE)}")
    
    while True:
        try:
            choice = input(f"{Colors.KEY}Nhập lựa chọn \033[97m[ 1 hoặc 2 ]: {Colors.RESET}").strip()
            if choice == "1":
                return "auto"
            elif choice == "2":
                return "manual"
            else:
                print(f"{Colors.color_text('Vui lòng nhập 1 hoặc 2!', Colors.ERROR)}")
        except:
            print(f"{Colors.color_text('Vui lòng nhập số!', Colors.ERROR)}")

# ========== HÀM NHẬP SỐ LƯỢNG TÀI KHOẢN ==========
def select_account_count():
    print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
    print(f"{Colors.color_text(' NHẬP SỐ LƯỢNG TÀI KHOẢN CẦN TẠO '.center(50), Colors.TITLE)}")
    print(f"{Colors.color_text('─'*70, Colors.LINE)}")
    print(f"{Colors.INFO} Mỗi thiết bị sẽ tạo số lượng tài khoản này \033[97m[ Mặc định: 1, Tối đa: 10 ]{Colors.RESET}")
    print(f"{Colors.color_text('─'*70, Colors.LINE)}")
    
    while True:
        try:
            count_input = input(f"{Colors.KEY}Nhập số lượng tài khoản \033[97m[ 1-10 ]: {Colors.RESET}").strip()
            if not count_input:
                return 1
            
            count = int(count_input)
            if 1 <= count <= 10:
                return count
            else:
                print(f"{Colors.color_text('Vui lòng nhập số từ 1 đến 10!', Colors.ERROR)}")
        except ValueError:
            print(f"{Colors.color_text('Vui lòng nhập số hợp lệ!', Colors.ERROR)}")

# ========== Class Thread chạy Automation ==========
class starts(threading.Thread):
    def __init__(self, device, mode, manual_email=None, manual_password=None, account_count=1):
        super().__init__()
        self.device = device
        self.mode = mode
        self.manual_email = manual_email
        self.manual_password = manual_password
        self.account_count = account_count
    
    def run(self):
        device = self.device
        mode = self.mode
        account_count = self.account_count

        def create_one_account(serial, account_index):
            print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
            print(f"{Colors.color_text(f'[{serial}]  BẮT ĐẦU TẠO TÀI KHOẢN THỨ {account_index}', Colors.TITLE)}")
            print(f"{Colors.color_text('─'*70, Colors.LINE)}")
            
            try:
                d = u2.connect(serial)
                ensure_atx_agent_health(d, serial)
                 
                auto_obj = Auto(serial)

                cleaner = AppCleaner(d, serial)
                cleaner.clear_instagram_data()
                
                time.sleep(random.uniform(2.0, 3.0))

                d.app_start("com.instagram.android", stop=True)
                time.sleep(random.uniform(3.5, 5.5))
                
                welcome_btns = [r"(?i)Bắt đầu", r"(?i)Get Started", r"(?i)Tiếp tục", r"(?i)Continue"]
                for pattern in welcome_btns:
                    if d(textMatches=pattern).exists(timeout=2):
                        d(textMatches=pattern).click()
                        time.sleep(2)
                        break
                
                if d(resourceId="com.google.android.gms:id/cancel").exists(timeout=2):
                    time.sleep(random.uniform(3, 5.0))
                    d(resourceId="com.google.android.gms:id/cancel").click()
                time.sleep(random.uniform(0.5, 3.0))
                
                mail_service = MailService()
                
                if mode == "auto":
                    name_gen = VietnameseNameGenerator()
                    full_name, username = name_gen.generate_name()
                    if account_index > 1:
                        username = f"{username}_{account_index}"
                    
                    new_email = mail_service.create_account(address=username)
                    if not new_email:
                        return None
                    mail_service.authenticate()
                    used_email = new_email
                    
                else:
                    used_email = self.manual_email
                    if account_index > 1 and "+" in used_email:
                        base_email = used_email.split('+')[0]
                        domain = used_email.split('@')[1]
                        used_email = f"{base_email}+{account_index}@{domain}"
                    elif account_index > 1 and "mail.tm" in used_email:
                        base_email = used_email.split('@')[0]
                        domain = used_email.split('@')[1]
                        used_email = f"{base_email}+{account_index}@{domain}"
                    
                    name_gen = VietnameseNameGenerator()
                    full_name, username = name_gen.generate_name()
                    if account_index > 1:
                        username = f"{username}_{account_index}"
                    
                    if "@" in self.manual_email and "mail.tm" in self.manual_email.lower():
                        mail_service.authenticate(email=self.manual_email, password=self.manual_password or "TempPass123!")

                if d(text="Tạo tài khoản mới").exists(timeout=10):
                    d(text="Tạo tài khoản mới").click()
                time.sleep(random.uniform(1.5, 2.5))

                d(descriptionMatches=r"(?i).*email.*|.*Email.*").click(timeout=10)
                time.sleep(random.uniform(1.2, 2.5))

                email_field = d(descriptionMatches=r"(?i)Email.*|.*email.*|.*địa chỉ.*")
                if email_field.exists(timeout=5):
                    email_field.click()
                else:
                    d(className="android.widget.EditText").click()
                time.sleep(1)
                
                if d(resourceId="android:id/autofill_dialog_no").exists(timeout=2):
                    d(resourceId="android:id/autofill_dialog_no").click()
                
                if d(className="android.widget.EditText").exists(timeout=5):
                    d(className="android.widget.EditText").set_text(used_email)
                    time.sleep(1)
                
                if d(resourceId="com.google.android.gms:id/cancel").exists(timeout=2):
                    d(resourceId="com.google.android.gms:id/cancel").click()
                
                d(text="Tiếp").click(timeout=5)
                time.sleep(random.uniform(1.5, 2.8))

                otp_code = None
                
                if mode == "auto":
                    otp_code = mail_service.get_otp_code(timeout=120)
                    
                    if not otp_code:
                        otp_code = wait_for_manual_otp(serial, used_email, timeout=300)
                    
                else:
                    if mail_service.token:
                        otp_code = mail_service.get_otp_code(timeout=60)
                        
                        if not otp_code:
                            otp_code = wait_for_manual_otp(serial, used_email, timeout=300)
                    else:
                        otp_code = wait_for_manual_otp(serial, used_email, timeout=300)
                
                if not otp_code:
                    return None
                
                if not otp_code.isdigit() or len(otp_code) != 6:
                    otp_code = wait_for_manual_otp(serial, used_email, timeout=120)
                    if not otp_code:
                        return None
                
                time.sleep(2)
                
                d.click(0.15, 0.3)
                time.sleep(1.5)
                
                for digit in otp_code:
                    run_adb_command(serial, f'shell input text {digit}')
                    time.sleep(0.3)
                
                time.sleep(1)
                
                d(textMatches=r"(?i)Tiếp|Next").click()
                time.sleep(3)
                
                if d(resourceId="com.google.android.gms:id/cancel").exists(timeout=2):
                    d(resourceId="com.google.android.gms:id/cancel").click()
                
                run_adb_command(serial, 'shell am force-stop com.github.uiautomator')
                time.sleep(2)
                
                secure_pass = generate_secure_password()
                pwd_field = d(descriptionMatches=r"(?i)Mật khẩu.*")
                if pwd_field.wait(timeout=10):
                    pwd_field.click()
                    time.sleep(2)
                    d.send_keys(secure_pass)
                    time.sleep(1.5)
                    d(text="Tiếp").click()
                
                time.sleep(4)
                
                if d(resourceId="android:id/button2").exists():
                    d(resourceId="android:id/button2").click()
                
                for _ in range(2):
                    if d(text="Tiếp").wait(timeout=5):
                        d(text="Tiếp").click()
                        time.sleep(2)

                age_field = d(description="Tuổi,")
                if age_field.wait(timeout=5):
                    age_field.click()
                    time.sleep(1)
                    d.send_keys(str(random.randint(20, 40)))
                    time.sleep(1)
                    d(text="Tiếp").click()
                    time.sleep(2)
                    if d(text="OK").exists():
                        d(text="OK").click()

                time.sleep(3)
                full_name_field = d(descriptionMatches=r"(?i)Tên đầy đủ.*")
                if full_name_field.wait(timeout=15):
                    full_name_field.click()
                    time.sleep(2.5)
                    d.clear_text()
                    time.sleep(0.5)
                    d.send_keys(full_name)
                    time.sleep(2)
                    d(text="Tiếp").click()
                else:
                    d.click(0.5, 0.28)
                    time.sleep(1)
                    d.send_keys(full_name)

                time.sleep(3)
                user_field = d(descriptionMatches=r"(?i)Tên người dùng.*")
                if user_field.wait(timeout=10):
                    user_field.click()
                    time.sleep(2)
                    d.clear_text()
                    time.sleep(1)
                    d.send_keys(username)
                    time.sleep(2)
                    d(text="Tiếp").click()
                
                size = d.window_size()
                d.swipe(0.5 * size[0], 0.7 * size[1], 0.5 * size[0], 0.3 * size[1])

                btn_agree = d(text="Tôi đồng ý")
                if btn_agree.wait(timeout=20):
                    btn_agree.click()
                    time.sleep(5)
                
                skip_avatar_screen(d, serial, auto_obj)
                
                print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
                print(f"{Colors.color_text(f'[{serial}]  HOÀN TẤT TÀI KHOẢN THỨ {account_index}!', Colors.SUCCESS)}")
                print(f"{Colors.KEY}Email:    {Colors.EMAIL}{used_email}{Colors.RESET}")
                print(f"{Colors.KEY}Password: {Colors.PASSWORD}{secure_pass}{Colors.RESET}")
                print(f"{Colors.KEY}Username: {Colors.USERNAME}{username}{Colors.RESET}")
                print(f"{Colors.KEY}Họ tên:   {Colors.VALUE}{full_name}{Colors.RESET}")
                print(f"{Colors.color_text('─'*70, Colors.LINE)}\n")
                
                save_account(serial, used_email, secure_pass, username, full_name, mode)
                
                return {
                    "email": used_email,
                    "password": secure_pass,
                    "username": username,
                    "full_name": full_name,
                    "account_index": account_index
                }
                
            except Exception:
                return None
        
        successful_accounts = []
        
        for i in range(1, account_count + 1):
            print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
            print(f"{Colors.color_text(f' [{device}] TIẾN HÀNH TẠO TÀI KHOẢN {i}/{account_count}', Colors.TITLE)}")
            print(f"{Colors.color_text('─'*70, Colors.LINE)}")
            
            result = create_one_account(device, i)
            
            if result:
                successful_accounts.append(result)
            
            if i < account_count:
                wait_time = random.uniform(30, 60)
                print(f"{Colors.color_text(f'[{device}] Nghỉ {wait_time:.1f} giây trước khi tạo tài khoản tiếp theo...', Colors.INFO)}")
                time.sleep(wait_time)
        
        print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
        print(f"{Colors.color_text(f'[{device}]  TỔNG KẾT TẠO TÀI KHOẢN', Colors.TITLE)}")
        print(f"{Colors.color_text('─'*70, Colors.LINE)}")
        print(f"{Colors.KEY}   Thiết bị: {Colors.VALUE}{device}{Colors.RESET}")
        print(f"{Colors.KEY}   Chế độ: {Colors.VALUE}{mode}{Colors.RESET}")
        print(f"{Colors.KEY}   Số lượng yêu cầu: {Colors.NUMBER}{account_count}{Colors.RESET}")
        print(f"{Colors.KEY}   Số lượng thành công: {Colors.SUCCESS}{len(successful_accounts)}{Colors.RESET}")
        print(f"{Colors.KEY}   Số lượng thất bại: {Colors.ERROR}{account_count - len(successful_accounts)}{Colors.RESET}")
        
        if successful_accounts:
            print(f"\n{Colors.KEY}    DANH SÁCH TÀI KHOẢN ĐÃ TẠO:{Colors.RESET}")
            for acc in successful_accounts:
                print(f"      {Colors.NUMBER}{acc['account_index']}. {Colors.EMAIL}{acc['email']} {Colors.KEY}| {Colors.USERNAME}{acc['username']}{Colors.RESET}")


# ========== MAIN PROGRAM ==========
if __name__ == "__main__":
    banner()
   
    mode = select_mode()
    
    manual_email = None
    manual_password = None
    
    if mode == "manual":
        print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
        print(f"{Colors.color_text(' NHẬP THÔNG TIN EMAIL '.center(50), Colors.TITLE)}")
        print(f"{Colors.color_text('─'*70, Colors.LINE)}")
        manual_email = input(f"{Colors.KEY}Nhập địa chỉ email \033[97m[ nhập email tùy chọn ] : {Colors.RESET}").strip()
        
        if not manual_email or "@" not in manual_email:
            print(f"{Colors.color_text('Email không hợp lệ!', Colors.ERROR)}")
            sys.exit(1)
        
        if "mail.tm" in manual_email.lower():
            manual_password = input(f"{Colors.KEY}Nhập mật khẩu email (Enter để dùng mặc định): {Colors.RESET}").strip()
            if not manual_password:
                manual_password = "TempPass123!"
        
        print(f"{Colors.color_text('─'*70, Colors.LINE)}")
    
    account_count = select_account_count()
    selected_devices = select_devices()
    
    if selected_devices:
        threads = []
        for serial in selected_devices:
            t = starts(serial, mode, manual_email, manual_password, account_count)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        
        print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
        print(f"{Colors.color_text('  HOÀN THÀNH TẤT CẢ!  '.center(50), Colors.SUCCESS)}")
        print(f"{Colors.color_text(f' Tài khoản đã được lưu trong folder: Instagram_reg/ '.center(50), Colors.INFO)}")
        print(f"{Colors.color_text('─'*70, Colors.LINE)}")