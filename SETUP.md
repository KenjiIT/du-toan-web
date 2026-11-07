# Hướng dẫn cài đặt Dự Toán Web

## Yêu cầu hệ thống

- Windows 10/11 (64-bit)
- Dung lượng đĩa trống: ~300 MB
- Bộ dữ liệu đơn giá GXD (thư mục `Dulieu`, ~160 MB các file .mdb) — bắt buộc để có dữ liệu tra cứu

## Cách 1: Cài bản Installer (khuyến nghị)

1. Vào trang Release: https://github.com/KenjiIT/du-toan-web/releases/latest
2. Tải file **Du Toan Web Setup x.x.x.exe**
3. Chạy file, chọn thư mục cài đặt, nhấn Install
4. Shortcut "Dự Toán Web" sẽ xuất hiện trên Desktop và Start Menu
5. Khi có bản mới, app sẽ tự thông báo và hỏi cập nhật

## Cách 2: Bản Portable (không cần cài)

1. Tải file **DuToanWeb-Portable-x.x.x.exe** từ trang Release
2. Chạy trực tiếp — không cần cài đặt
3. Lưu ý: bản portable không hỗ trợ auto-update, cần tải bản mới thủ công

## Thiết lập dữ liệu (bắt buộc cho lần đầu)

App cần file `dutoan.db` chứa dữ liệu đơn giá, định mức, giá vật tư... File này được tạo từ bộ dữ liệu GXD bằng script migration.

### Bước 1: Chuẩn bị dữ liệu GXD

Đặt thư mục `Dulieu` (chứa các file .mdb từ GXD) vào một vị trí trên máy. Ví dụ:
```
C:\Users\<tên>\Downloads\Dulieu\
├── Data.mdb          (dữ liệu chính: đơn giá, định mức, vật tư)
├── Nhancong.mdb      (bảng nhân công)
├── CVC.mdb           (chi phí vận chuyển)
├── GNC\*.mdb         (giá nhân công theo vùng)
├── GCM\*.mdb         (giá ca máy theo vùng)
└── GVT\*.csv         (giá vật tư theo kỳ)
```

### Bước 2: Cài Python (chỉ cần cho migration)

Tải và cài Python 3.12+ từ https://www.python.org/downloads/
Khi cài, nhớ tick "Add Python to PATH".

### Bước 3: Chạy migration

```powershell
# Clone source code (hoặc tải zip từ GitHub)
git clone https://github.com/KenjiIT/du-toan-web.git
cd du-toan-web

# Cài thư viện cần thiết
pip install pyodbc sqlalchemy

# Chạy migration — thay đường dẫn Dulieu cho đúng
set DUTOAN_MDB_DIR=C:\Users\<tên>\Downloads\Dulieu
python backend/scripts/migrate_mdb.py
```

Script sẽ đọc tất cả file .mdb và tạo ra `backend/data/dutoan.db` (~106 MB).

### Bước 4: Chép database vào app

**Bản Installer:**
```powershell
# Mặc định app cài ở:
copy backend\data\dutoan.db "%LOCALAPPDATA%\Programs\du-toan-desktop\resources\backend\data\dutoan.db"
```

**Bản Portable:**
App portable tạo thư mục tạm khi chạy. Đặt file `dutoan.db` vào cùng thư mục chứa file .exe, trong `resources\backend\data\`.

### Bước 5: Khởi động app

Mở Dự Toán Web từ shortcut hoặc chạy file portable. App sẽ:
- Khởi động backend (FastAPI) trên port 8000
- Khởi động frontend trên port 3000
- Mở cửa sổ ứng dụng

## Hành vi ứng dụng

- **Nút X (đóng)**: App ẩn xuống system tray (không thoát)
- **Thoát thật**: Click phải icon tray → "Thoát", hoặc File → Thoát (Ctrl+Q)
- **Mở lại**: Click đúp icon tray, hoặc click phải → "Mở lại"
- **Chạy nhiều lần**: App chỉ cho phép 1 instance, mở lần 2 sẽ focus vào cửa sổ đang có
- **Auto-update** (bản Installer): Khi khởi động, app kiểm tra GitHub Releases. Có bản mới sẽ hỏi tải + cài tự động

## Xử lý sự cố

| Vấn đề | Giải pháp |
|--------|-----------|
| App khởi động nhưng trắng trang | Kiểm tra port 3000 và 8000 có bị chiếm không (`netstat -ano \| findstr :8000`) |
| Không có dữ liệu đơn giá | Chưa chạy migration hoặc chưa chép `dutoan.db` vào đúng chỗ |
| Lỗi "Không tìm thấy Python" khi migration | Cài Python 3.12+ và thêm vào PATH |
| Lỗi "pyodbc" khi migration | Cài Microsoft Access Database Engine: https://www.microsoft.com/en-us/download/details.aspx?id=54920 |
| Windows SmartScreen cảnh báo | App chưa có chữ ký số. Nhấn "More info" → "Run anyway" |
| Auto-update không hoạt động | Chỉ bản Installer mới hỗ trợ. Bản Portable phải tải thủ công |

## Cho agent/developer

### Build từ source

```powershell
# Clone
git clone https://github.com/KenjiIT/du-toan-web.git
cd du-toan-web

# Frontend
cd frontend && npm install && cd ..

# Backend (dev)
cd backend && pip install -r requirements.txt && cd ..

# Chạy dev mode
cd electron && npm install && npm start
```

### Build .exe (local)

```powershell
cd electron
node scripts/package.js
# Output: electron/release/*.exe
```

### Release bản mới

```powershell
# 1. Sửa version trong electron/package.json
# 2. Commit và push
git add -A && git commit -m "release: vX.Y.Z"
git push origin master

# 3. Tag và push tag — GitHub Actions tự build + tạo Release
git tag vX.Y.Z
git push origin vX.Y.Z
```

CI workflow sẽ:
- Build Next.js frontend (static export)
- Bundle Python 3.12 embeddable + backend dependencies
- Tạo portable .exe và NSIS installer
- Upload vào GitHub Release kèm `latest.yml` cho auto-updater
