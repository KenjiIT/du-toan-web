# Kết nối MCP Server — Dự Toán Web

MCP server cho phép agent (Claude, Codex, v.v.) tra cứu đơn giá, lập dự toán, tính chi phí vận chuyển... thông qua giao thức MCP (Model Context Protocol).

## Kiến trúc

```
Agent (Claude Code / Claude Desktop / Codex)
  │
  │  MCP stdio
  ▼
dutoan-mcp (Python, chạy local)
  │
  │  HTTP → localhost:8000
  ▼
Backend FastAPI (chạy trong Electron app hoặc dev server)
  │
  ▼
SQLite (dutoan.db)
```

MCP server **không truy cập trực tiếp database** — nó gọi REST API của backend. Nên backend phải đang chạy (mở app Dự Toán Web, hoặc chạy dev server).

## Cài đặt

### Bước 1: Cài MCP server

```powershell
cd du-toan-web/mcp-server
pip install -e .
```

Hoặc cài từ GitHub:
```powershell
pip install git+https://github.com/KenjiIT/du-toan-web.git#subdirectory=mcp-server
```

### Bước 2: Kiểm tra server chạy được

```powershell
dutoan-mcp
```

Server sẽ chờ input qua stdin (giao thức MCP stdio). Nhấn Ctrl+C để thoát.

### Bước 3: Đảm bảo backend đang chạy

Mở app Dự Toán Web (Electron), hoặc chạy backend thủ công:
```powershell
cd du-toan-web/backend
pip install fastapi uvicorn sqlalchemy openpyxl reportlab bcrypt PyJWT python-multipart
uvicorn app.main:app --port 8000
```

Kiểm tra: truy cập http://localhost:8000/docs — phải thấy Swagger UI.

## Cấu hình cho từng client

### Claude Code (claude CLI / Claude Code desktop)

Thêm vào file `claude_desktop_config.json` hoặc `.mcp.json` trong thư mục dự án:

```json
{
  "mcpServers": {
    "dutoan": {
      "command": "dutoan-mcp",
      "env": {
        "DUTOAN_API_URL": "http://localhost:8000/api/v1"
      }
    }
  }
}
```

Nếu `dutoan-mcp` không nằm trong PATH, dùng đường dẫn đầy đủ:
```json
{
  "mcpServers": {
    "dutoan": {
      "command": "python",
      "args": ["-m", "dutoan_mcp.server"],
      "env": {
        "DUTOAN_API_URL": "http://localhost:8000/api/v1"
      }
    }
  }
}
```

### Claude Desktop

Vào Settings → Developer → Edit Config, thêm:
```json
{
  "mcpServers": {
    "dutoan": {
      "command": "dutoan-mcp",
      "env": {
        "DUTOAN_API_URL": "http://localhost:8000/api/v1"
      }
    }
  }
}
```

### Codex

Thêm vào `.codex/agents.json` hoặc cấu hình MCP tương tự Claude Code.

## Biến môi trường

| Biến | Mặc định | Mô tả |
|------|----------|-------|
| `DUTOAN_API_URL` | `http://localhost:8000/api/v1` | URL của backend API |

## Danh sách tools

| Tool | Mô tả |
|------|-------|
| `search_don_gia` | Tra cứu đơn giá theo mã hoặc tên công việc |
| `phan_tich_don_gia` | Phân tích chi tiết VLC/NC/MTC cho một mã hiệu |
| `create_project` | Tạo dự án dự toán mới |
| `add_project_item` | Thêm công việc vào dự án (mã hiệu + khối lượng) |
| `get_project_summary` | Xem tổng hợp chi phí dự án (T/C/TL/G/GTGT/GXD) |
| `list_projects` | Liệt kê tất cả dự án đã tạo |
| `get_thvt` | Bảng tổng hợp vật tư - nhân công - máy của dự án |
| `search_vat_tu` | Tra cứu giá vật tư xây dựng |
| `calculate_cvc` | Tính chi phí vận chuyển vật liệu theo cự ly |
| `lookup_svdt` | Tra suất vốn đầu tư theo loại công trình |
| `calculate_svdt` | Tính ước tính chi phí từ suất vốn đầu tư |
| `compare_prices` | So sánh đơn giá giữa các tỉnh/thành phố |

## Ví dụ sử dụng (cho agent)

### Tra đơn giá đào đất

```
→ search_don_gia(q="đào đất")
← [{ mhdg: "AB.11111", tcv: "Đào đất bằng thủ công...", dvt: "m3", ... }]
```

### Phân tích chi tiết

```
→ phan_tich_don_gia(mhdg="AB.11111")
← { vat_lieu: [...], nhan_cong: [...], may: [...], tong: { vlc: 0, nc: 235962, mtc: 0 } }
```

### Lập dự toán

```
→ create_project(name="Nhà ở 3 tầng", regulation_code="TT12")
← { id: 1, name: "Nhà ở 3 tầng", ... }

→ add_project_item(project_id=1, mhdg="AB.11111", quantity=150)
← { id: 1, mhdg: "AB.11111", quantity: 150, thanh_tien: 35394300 }

→ get_project_summary(project_id=1)
← { T: 35394300, C: ..., TL: ..., G: ..., gtgt: ..., gxd: ... }
```

## Xử lý sự cố

| Vấn đề | Giải pháp |
|--------|-----------|
| `Không thể kết nối tới API` | Backend chưa chạy. Mở app Dự Toán Web hoặc chạy `uvicorn app.main:app --port 8000` |
| `ModuleNotFoundError: dutoan_mcp` | Chưa cài MCP server. Chạy `pip install -e .` trong `mcp-server/` |
| `Tool không trả kết quả` | Kiểm tra database có dữ liệu chưa — cần chạy migration từ bộ GXD (xem SETUP.md) |
| Agent không thấy tools | Kiểm tra cấu hình MCP đúng chưa, và `dutoan-mcp` chạy được trong terminal |
