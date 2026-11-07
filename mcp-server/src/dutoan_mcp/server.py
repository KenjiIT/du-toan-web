"""MCP server cho phần mềm dự toán xây dựng."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .api_client import DuToanClient

server = Server("dutoan-mcp")
client = DuToanClient()


def _text(data: Any) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


# ======================================================================
# Tool definitions
# ======================================================================

TOOLS: list[Tool] = [
    Tool(
        name="search_don_gia",
        description="Tra cứu đơn giá xây dựng theo mã hoặc tên công việc. Trả về danh sách công việc với mã hiệu, tên, đơn vị tính và chi phí VLC/NC/MTC.",
        inputSchema={
            "type": "object",
            "properties": {
                "q": {"type": "string", "description": "Từ khóa tìm kiếm (mã hiệu đơn giá hoặc tên công việc)"},
                "chapter": {"type": "string", "description": "Lọc theo chương (ví dụ: 'AF' cho công tác đất)"},
                "regulation_code": {"type": "string", "description": "Mã thông tư/nghị định áp dụng"},
                "page": {"type": "integer", "description": "Số trang (phân trang)"},
                "limit": {"type": "integer", "description": "Số kết quả mỗi trang (mặc định 20)", "default": 20},
            },
            "required": ["q"],
        },
    ),
    Tool(
        name="phan_tich_don_gia",
        description="Phân tích chi tiết đơn giá cho một mã hiệu công việc. Trả về bảng phân tích VLC (vật liệu), NC (nhân công), MTC (máy thi công) với định mức và đơn giá từng thành phần.",
        inputSchema={
            "type": "object",
            "properties": {
                "mhdg": {"type": "string", "description": "Mã hiệu đơn giá (ví dụ: 'AF.11110')"},
                "source": {"type": "string", "description": "Nguồn đơn giá (ví dụ: tên tỉnh/thành phố)"},
                "regulation_code": {"type": "string", "description": "Mã thông tư/nghị định áp dụng"},
            },
            "required": ["mhdg"],
        },
    ),
    Tool(
        name="create_project",
        description="Tạo dự án dự toán mới. Sau khi tạo, có thể thêm công việc vào dự án bằng tool add_project_item.",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Tên dự án"},
                "description": {"type": "string", "description": "Mô tả dự án"},
                "regulation_code": {"type": "string", "description": "Mã thông tư/nghị định áp dụng"},
                "estimate_type": {
                    "type": "string",
                    "enum": ["new", "repair"],
                    "description": "Loại dự toán: 'new' (xây mới) hoặc 'repair' (sửa chữa)",
                },
            },
            "required": ["name"],
        },
    ),
    Tool(
        name="add_project_item",
        description="Thêm một công việc (hạng mục) vào dự án dự toán. Cần có mã hiệu đơn giá và khối lượng. Hệ thống tự tính thành tiền.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "integer", "description": "ID của dự án"},
                "mhdg": {"type": "string", "description": "Mã hiệu đơn giá của công việc"},
                "quantity": {"type": "number", "description": "Khối lượng công việc"},
                "notes": {"type": "string", "description": "Ghi chú cho hạng mục"},
            },
            "required": ["project_id", "mhdg", "quantity"],
        },
    ),
    Tool(
        name="get_project_summary",
        description="Xem tổng hợp chi phí dự án, bao gồm: chi phí vật liệu (VLC), nhân công (NC), máy thi công (MTC), chi phí trực tiếp (T), chi phí chung (C), thu nhập chịu thuế tính trước (TL), giá trị dự toán (G), thuế GTGT, giá trị dự toán sau thuế (GXD).",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "integer", "description": "ID của dự án"},
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="search_vat_tu",
        description="Tra cứu giá vật tư, vật liệu xây dựng theo tên hoặc mã. Trả về danh sách vật tư với mã số, tên, đơn vị tính và giá gốc.",
        inputSchema={
            "type": "object",
            "properties": {
                "q": {"type": "string", "description": "Từ khóa tìm kiếm (mã số hoặc tên vật tư)"},
                "source": {"type": "string", "description": "Nguồn giá vật tư (ví dụ: tên tỉnh/thành phố)"},
                "page": {"type": "integer", "description": "Số trang (phân trang)"},
                "limit": {"type": "integer", "description": "Số kết quả mỗi trang (mặc định 20)", "default": 20},
            },
            "required": ["q"],
        },
    ),
    Tool(
        name="calculate_cvc",
        description="Tính chi phí vận chuyển vật liệu xây dựng theo cự ly. Nhập tên vật liệu và khoảng cách (km) để tính cước vận chuyển.",
        inputSchema={
            "type": "object",
            "properties": {
                "vatlieu": {"type": "string", "description": "Tên hoặc loại vật liệu cần vận chuyển"},
                "culy_km": {"type": "number", "description": "Cự ly vận chuyển (km)"},
                "vehicle_id": {"type": "integer", "description": "ID phương tiện vận chuyển (nếu muốn chỉ định)"},
                "klg": {"type": "number", "description": "Khối lượng vận chuyển"},
            },
            "required": ["vatlieu", "culy_km"],
        },
    ),
    Tool(
        name="lookup_svdt",
        description="Tra cứu suất vốn đầu tư xây dựng theo loại công trình. Dùng để ước tính sơ bộ chi phí đầu tư theo diện tích hoặc công suất.",
        inputSchema={
            "type": "object",
            "properties": {
                "q": {"type": "string", "description": "Loại công trình cần tra (ví dụ: 'nhà ở', 'trường học')"},
                "nam": {"type": "integer", "description": "Năm áp dụng suất vốn đầu tư"},
            },
            "required": ["q"],
        },
    ),
    Tool(
        name="calculate_svdt",
        description="Tính chi phí ước tính từ suất vốn đầu tư. Cần có ID suất vốn (từ lookup_svdt) và diện tích/công suất công trình.",
        inputSchema={
            "type": "object",
            "properties": {
                "svdt_id": {"type": "integer", "description": "ID suất vốn đầu tư (lấy từ kết quả lookup_svdt)"},
                "dien_tich": {"type": "number", "description": "Diện tích hoặc công suất công trình"},
            },
            "required": ["svdt_id", "dien_tich"],
        },
    ),
    Tool(
        name="compare_prices",
        description="So sánh đơn giá của một mã hiệu công việc giữa các nguồn (tỉnh/thành phố) khác nhau.",
        inputSchema={
            "type": "object",
            "properties": {
                "mhdg": {"type": "string", "description": "Mã hiệu đơn giá cần so sánh"},
                "sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Danh sách nguồn đơn giá để so sánh (ví dụ: ['HCM', 'HN', 'DN'])",
                },
            },
            "required": ["mhdg", "sources"],
        },
    ),
    Tool(
        name="get_thvt",
        description="Lấy bảng tổng hợp vật tư, nhân công, máy thi công của dự án. Tổng hợp tất cả tài nguyên cần thiết với số lượng và thành tiền.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "integer", "description": "ID của dự án"},
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="list_projects",
        description="Liệt kê tất cả dự án dự toán đã tạo, với thông tin cơ bản (ID, tên, ngày tạo).",
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
]


@server.list_tools()
async def list_tools() -> list[Tool]:
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    match name:
        case "search_don_gia":
            result = await client.search_don_gia(**arguments)
        case "phan_tich_don_gia":
            result = await client.phan_tich_don_gia(**arguments)
        case "create_project":
            result = await client.create_project(**arguments)
        case "add_project_item":
            result = await client.add_project_item(**arguments)
        case "get_project_summary":
            result = await client.get_project_summary(**arguments)
        case "search_vat_tu":
            result = await client.search_vat_tu(**arguments)
        case "calculate_cvc":
            result = await client.calculate_cvc(**arguments)
        case "lookup_svdt":
            result = await client.lookup_svdt(**arguments)
        case "calculate_svdt":
            result = await client.calculate_svdt(**arguments)
        case "compare_prices":
            result = await client.compare_prices(**arguments)
        case "get_thvt":
            result = await client.get_thvt(**arguments)
        case "list_projects":
            result = await client.list_projects()
        case _:
            result = {"error": f"Tool '{name}' không tồn tại"}
    return _text(result)


def main():
    async def _run():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    asyncio.run(_run())


if __name__ == "__main__":
    main()
