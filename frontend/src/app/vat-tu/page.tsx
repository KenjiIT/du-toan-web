"use client";

import { useCallback, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { searchVatTu, updateVatTuPrice, importVatTuCsv } from "@/lib/api";
import { formatVND } from "@/lib/formatters";
import type { VatTu } from "@/lib/types";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export default function VatTuPage() {
  const [q, setQ] = useState("");
  const [searchText, setSearchText] = useState("");
  const [page, setPage] = useState(1);
  const limit = 20;
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [importing, setImporting] = useState(false);
  const [importMsg, setImportMsg] = useState("");
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["vat-tu", q, page],
    queryFn: () => searchVatTu({ q: q || undefined, page, limit }),
  });

  const handleSearch = useCallback(() => {
    setQ(searchText);
    setPage(1);
  }, [searchText]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") {
        handleSearch();
      }
    },
    [handleSearch],
  );

  const handleImport = useCallback(async () => {
    const file = fileInputRef.current?.files?.[0];
    if (!file) return;
    setImporting(true);
    setImportMsg("");
    try {
      const result = await importVatTuCsv(file);
      setImportMsg(`Nhập xong: ${result.created} mới, ${result.updated} cập nhật`);
      queryClient.invalidateQueries({ queryKey: ["vat-tu"] });
    } catch (err) {
      setImportMsg(`Lỗi: ${err instanceof Error ? err.message : "Không xác định"}`);
    } finally {
      setImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }, [queryClient]);

  const totalPages = data ? Math.ceil(data.total / data.limit) : 0;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Quản lý giá vật tư</h1>

      {/* Search + Import bar */}
      <div className="flex items-center gap-3 mb-4">
        <Input
          placeholder="Tìm theo mã hoặc tên vật tư..."
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          onKeyDown={handleKeyDown}
          className="max-w-md"
        />
        <Button onClick={handleSearch}>Tìm kiếm</Button>

        <div className="ml-auto flex items-center gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={handleImport}
          />
          <Button
            variant="outline"
            onClick={() => fileInputRef.current?.click()}
            disabled={importing}
          >
            {importing ? "Đang nhập..." : "Nhập CSV"}
          </Button>
          {importMsg && (
            <Badge variant={importMsg.startsWith("Lỗi") ? "destructive" : "secondary"}>
              {importMsg}
            </Badge>
          )}
        </div>
      </div>

      {/* Results */}
      {isLoading ? (
        <div className="text-center py-8 text-muted-foreground">Đang tải...</div>
      ) : error ? (
        <div className="text-center py-8 text-destructive">
          Lỗi kết nối API. Hãy đảm bảo backend đang chạy tại localhost:8000.
        </div>
      ) : data && data.items.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          Không tìm thấy vật tư nào.
        </div>
      ) : data ? (
        <>
          <div className="text-sm text-muted-foreground mb-2">
            {data.total.toLocaleString("vi-VN")} kết quả
          </div>
          <div className="border rounded-md">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[140px]">Mã VT</TableHead>
                  <TableHead>Tên vật tư</TableHead>
                  <TableHead className="w-[80px]">ĐVT</TableHead>
                  <TableHead className="w-[160px] text-right">Giá gốc</TableHead>
                  <TableHead className="w-[100px]">Nguồn</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.items.map((item) => (
                  <VatTuRow key={item.id} item={item} />
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <div className="text-sm text-muted-foreground">
                Trang {page} / {totalPages}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                >
                  Trước
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                >
                  Sau
                </Button>
              </div>
            </div>
          )}
        </>
      ) : null}
    </div>
  );
}

function VatTuRow({ item }: { item: VatTu }) {
  const [editing, setEditing] = useState(false);
  const [price, setPrice] = useState(String(item.gia_goc || 0));
  const [saving, setSaving] = useState(false);
  const queryClient = useQueryClient();

  const handleSave = useCallback(async () => {
    const newPrice = parseFloat(price);
    if (isNaN(newPrice) || newPrice === item.gia_goc) {
      setEditing(false);
      setPrice(String(item.gia_goc || 0));
      return;
    }
    setSaving(true);
    try {
      await updateVatTuPrice(item.id, newPrice);
      queryClient.invalidateQueries({ queryKey: ["vat-tu"] });
    } catch {
      setPrice(String(item.gia_goc || 0));
    } finally {
      setSaving(false);
      setEditing(false);
    }
  }, [price, item.id, item.gia_goc, queryClient]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") handleSave();
      if (e.key === "Escape") {
        setEditing(false);
        setPrice(String(item.gia_goc || 0));
      }
    },
    [handleSave, item.gia_goc],
  );

  return (
    <TableRow>
      <TableCell className="font-mono text-sm">{item.msvt}</TableCell>
      <TableCell>{item.tvt || "-"}</TableCell>
      <TableCell>{item.dvt || "-"}</TableCell>
      <TableCell className="text-right">
        {editing ? (
          <Input
            type="number"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            onBlur={handleSave}
            onKeyDown={handleKeyDown}
            disabled={saving}
            className="w-[140px] ml-auto text-right"
            autoFocus
          />
        ) : (
          <button
            onClick={() => setEditing(true)}
            className="hover:bg-accent px-2 py-1 rounded cursor-pointer text-right w-full"
            title="Nhấn để sửa giá"
          >
            {formatVND(item.gia_goc)}
          </button>
        )}
      </TableCell>
      <TableCell>
        {item.source ? (
          <Badge variant="secondary">{item.source}</Badge>
        ) : (
          "-"
        )}
      </TableCell>
    </TableRow>
  );
}
