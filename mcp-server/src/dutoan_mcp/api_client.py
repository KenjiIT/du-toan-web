"""Async HTTP client wrapping the du-toan REST API."""

from __future__ import annotations

import os
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://localhost:8000/api/v1"


class DuToanClient:
    """Thin async wrapper around the du-toan FastAPI backend."""

    def __init__(self, base_url: str | None = None, timeout: float = 30.0):
        self.base_url = (base_url or os.environ.get("DUTOAN_API_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        try:
            async with self._client() as c:
                resp = await c.get(path, params=params)
                resp.raise_for_status()
                return resp.json()
        except httpx.ConnectError:
            return {"error": f"Không thể kết nối tới API tại {self.base_url}. Hãy kiểm tra server đã chạy chưa."}
        except httpx.HTTPStatusError as exc:
            return {"error": f"HTTP {exc.response.status_code}: {exc.response.text[:500]}"}
        except Exception as exc:
            return {"error": str(exc)}

    async def _post(self, path: str, json_body: dict[str, Any] | None = None) -> Any:
        try:
            async with self._client() as c:
                resp = await c.post(path, json=json_body)
                resp.raise_for_status()
                return resp.json()
        except httpx.ConnectError:
            return {"error": f"Không thể kết nối tới API tại {self.base_url}. Hãy kiểm tra server đã chạy chưa."}
        except httpx.HTTPStatusError as exc:
            return {"error": f"HTTP {exc.response.status_code}: {exc.response.text[:500]}"}
        except Exception as exc:
            return {"error": str(exc)}

    # ------------------------------------------------------------------
    # Don gia (unit prices)
    # ------------------------------------------------------------------

    async def search_don_gia(
        self,
        q: str,
        chapter: str | None = None,
        regulation_code: str | None = None,
        page: int | None = None,
        limit: int = 20,
    ) -> Any:
        params: dict[str, Any] = {"q": q, "limit": limit}
        if chapter:
            params["chapter"] = chapter
        if regulation_code:
            params["regulation_code"] = regulation_code
        if page is not None:
            params["page"] = page
        return await self._get("/don-gia", params)

    async def phan_tich_don_gia(
        self,
        mhdg: str,
        source: str | None = None,
        regulation_code: str | None = None,
    ) -> Any:
        params: dict[str, Any] = {}
        if source:
            params["source"] = source
        if regulation_code:
            params["regulation_code"] = regulation_code
        return await self._get(f"/don-gia/{mhdg}/phan-tich", params or None)

    async def compare_prices(self, mhdg: str, sources: list[str]) -> Any:
        params: dict[str, Any] = {"sources": ",".join(sources)}
        return await self._get(f"/don-gia/{mhdg}/compare", params)

    # ------------------------------------------------------------------
    # Vat tu (materials)
    # ------------------------------------------------------------------

    async def search_vat_tu(
        self,
        q: str,
        source: str | None = None,
        page: int | None = None,
        limit: int = 20,
    ) -> Any:
        params: dict[str, Any] = {"q": q, "limit": limit}
        if source:
            params["source"] = source
        if page is not None:
            params["page"] = page
        return await self._get("/vat-tu", params)

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    async def list_projects(self) -> Any:
        return await self._get("/projects")

    async def create_project(
        self,
        name: str,
        description: str | None = None,
        regulation_code: str | None = None,
        estimate_type: str | None = None,
    ) -> Any:
        body: dict[str, Any] = {"name": name}
        if description:
            body["description"] = description
        if regulation_code:
            body["regulation_code"] = regulation_code
        if estimate_type:
            body["estimate_type"] = estimate_type
        return await self._post("/projects", body)

    async def get_project_summary(self, project_id: int) -> Any:
        return await self._get(f"/projects/{project_id}")

    async def add_project_item(
        self,
        project_id: int,
        mhdg: str,
        quantity: float,
        notes: str | None = None,
    ) -> Any:
        body: dict[str, Any] = {"mhdg": mhdg, "quantity": quantity}
        if notes:
            body["notes"] = notes
        return await self._post(f"/projects/{project_id}/items", body)

    async def get_thvt(self, project_id: int) -> Any:
        return await self._get(f"/projects/{project_id}/thvt")

    # ------------------------------------------------------------------
    # CVC (transport cost)
    # ------------------------------------------------------------------

    async def calculate_cvc(
        self,
        vatlieu: str,
        culy_km: float,
        vehicle_id: int | None = None,
        klg: float | None = None,
    ) -> Any:
        body: dict[str, Any] = {"vatlieu": vatlieu, "culy_km": culy_km}
        if vehicle_id is not None:
            body["vehicle_id"] = vehicle_id
        if klg is not None:
            body["klg"] = klg
        return await self._post("/cvc/calculate", body)

    # ------------------------------------------------------------------
    # SVDT (investment rate)
    # ------------------------------------------------------------------

    async def lookup_svdt(self, q: str, nam: int | None = None) -> Any:
        params: dict[str, Any] = {"q": q}
        if nam is not None:
            params["nam"] = nam
        return await self._get("/svdt", params)

    async def calculate_svdt(self, svdt_id: int, dien_tich: float) -> Any:
        return await self._post("/svdt/calculate", {"svdt_id": svdt_id, "dien_tich": dien_tich})
