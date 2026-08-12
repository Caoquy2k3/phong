# GoLike Tool (CLI)

CLI đơn giản để tương tác với GoLike Gateway (`https://gateway.golike.net`). Hỗ trợ đăng nhập, xem thông tin tài khoản, liệt kê tài khoản Instagram và chạy job minh hoạ.

## Cài đặt

```bash
pip install -r requirements.txt
```

## Sử dụng nhanh

- Đăng nhập và lưu `auth.json`:

```bash
python golike_cli.py login
# hoặc truyền sẵn:
python golike_cli.py --device android login --token "<Bearer hoặc token>" --t "<T>"
```

- Xem thông tin người dùng (dùng `auth.json` nếu có):

```bash
python golike_cli.py me
```

- Liệt kê tài khoản Instagram đã liên kết:

```bash
python golike_cli.py ig-accounts
```

- Chạy job Instagram (demo/placeholder):

```bash
python golike_cli.py run-ig
```

- Đăng xuất (xoá `auth.json`):

```bash
python golike_cli.py logout
```

## Ghi chú
- Công cụ sử dụng các endpoint công khai từ `gateway.golike.net`.
- Trường `T` bắt buộc phải hợp lệ cùng với Authorization token.
- Mặc định User-Agent giả lập thiết bị Android, có thể đổi sang iOS bằng `--device ios`.
