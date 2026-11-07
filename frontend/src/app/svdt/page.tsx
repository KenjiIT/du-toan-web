"use client";

import { useCallback, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { searchSvdt, calculateSvdt, importSvdtCsv } from "@/lib/api";
import { formatVND } from "@/lib/formatters";
import type { SuatVonDauTu, SvdtCalculateResult } from "@/lib/types";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export default function SVDTPage() {
  const [searchText, setSearchText] = useState("");
  const [q, setQ] = useState("");
  const [namFilter, setNamFilter] = useState("");
  const [qdFilter, setQdFilter] = useState("");
  const [page, setPage] = useState(1);
  const limit = 20;

  const [selectedRow, setSelectedRow] = useState<SuatVonDauTu | null>(null);
  const [dienTich, setDienTich] = useState("");
  const [calculating, setCalculating] = useState(false);
  const [calcResult, setCalcResult] = useState<SvdtCalculateResult | null>(
    null,
  );
  const [calcError, setCalcError] = useState("");

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [importing, setImporting] = useState(false);
  const [importMsg, setImportMsg] = useState("");
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["svdt", q, namFilter, qdFilter, page],
    queryFn: () =>
      searchSvdt({
        q: q || undefined,
        nam: namFilter ? Number(namFilter) : undefined,
        quyet_dinh: qdFilter || undefined,
        page,
        limit,
      }),
  });

  const handleSearch = useCallback(() => {
    setQ(searchText);
    setPage(1);
  }, [searchText]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") handleSearch();
    },
    [handleSearch],
  );

  const handleCalculate = useCallback(async () => {
    if (!selectedRow || !dienTich) return;
    const dt = parseFloat(dienTich);
    if (isNaN(dt) || dt <= 0) {
      setCalcError("Vui lòng nhập diện tích/số lượng hợp lệ.");
      return;
    }
    setCalculating(true);
    setCalcError("");
    setCalcResult(null);
    try {
      const result = await calculateSvdt({
        svdt_id: selectedRow.id,
        dien_tich: dt,
      });
      setCalcResult(result);
    } catch (err) {
      setCalcError(
        err instanceof Error ? err.message : "Lỗi không xác định",
      );
    } finally {
      setCalculating(false);
    }
  }, [selectedRow, dienTich]);

  const handleImport = useCallback(async () => {
    const file = fileInputRef.current?.files?.[0];
    if (!file) return;
    setImporting(true);
    setImportMsg("");
    try {
      const result = await importSvdtCsv(file);
      let msg = `Nhập xong: ${result.created} bản ghi mới`;
      if (result.errors && result.errors.length > 0) {
        msg += ` (${result.errors.length} lỗi)`;
      }
      setImportMsg(msg);
      queryClient.invalidateQueries({ queryKey: ["svdt"] });
    } catch (err) {
      setImportMsg(
        `Lỗi: ${err instanceof Error ? err.message : "Không xác định"}`,
      );
    } finally {
      setImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }, [queryClient]);

  const handleRowClick = useCallback((item: SuatVonDauTu) => {
    setSelectedRow(item);
    setCalcResult(null);
    setCalcError("");
  }, []);

  const totalPages = data ? Math.ceil(data.total / data.limit) : 0;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Suất vốn đầu tư (SVDT)</h1>

      {/* Search + filters + import */}
      <div className="flex flex-wrap items-end gap-3">
        <div className="space-y-1">
          <label className="text-sm text-muted-foreground">Tìm kiếm</label>
          <Input
            placeholder="Loại công trình..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-64"
          />
        </div>
        <div className="space-y-1">
          <label className="text-sm text-muted-foreground">Năm</label>
          <Input
            type="number"
            placeholder="VD: 2023"
            value={namFilter}
            onChange={(e) => setNamFilter(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-28"
          />
        </div>
        <div className="space-y-1">
          <label className="text-sm text-muted-foreground">Quyết định</label>
          <Input
            placeholder="VD: 610/QĐ-BXD"
            value={qdFilter}
            onChange={(e) => setQdFilter(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-44"
          />
        </div>
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
            <Badge
              variant={importMsg.startsWith("Lỗi") ? "destructive" : "secondary"}
            >
              {importMsg}
            </Badge>
          )}
        </div>
      </div>

      {/* Data table */}
      {isLoading ? (
        <div className="text-center py-8 text-muted-foreground">
          Đang tải...
        </div>
      ) : error ? (
        <div className="text-center py-8 text-destructive">
          Lỗi kết nối API. Hãy đảm bảo backend đang chạy tại localhost:8000.
        </div>
      ) : data && data.items.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          Không tìm thấy dữ liệu suất vốn đầu tư nào.
        </div>
      ) : data ? (
        <>
          <div className="text-sm text-muted-foreground">
            {data.total.toLocaleString("vi-VN")} kết quả
            {selectedRow && (
              <span className="ml-3">
                Đã chọn:{" "}
                <span className="font-medium text-foreground">
                  {selectedRow.loai_cong_trinh}
                </span>
              </span>
            )}
          </div>
          <div className="border rounded-md">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Loại công trình</TableHead>
                  <TableHead className="w-[80px]">Đơn vị</TableHead>
                  <TableHead className="w-[140px] text-right">
                    Suất vốn
                  </TableHead>
                  <TableHead className="w-[130px] text-right">
                    Trong đó XD
                  </TableHead>
                  <TableHead className="w-[130px] text-right">
                    Trong đó TB
                  </TableHead>
                  <TableHead className="w-[70px] text-center">Năm</TableHead>
                  <TableHead className="w-[140px]">Quyết định</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.items.map((item) => (
                  <TableRow
                    key={item.id}
                    className={`cursor-pointer hover:bg-accent ${
                      selectedRow?.id === item.id
                        ? "bg-accent border-l-2 border-l-primary"
                        : ""
                    }`}
                    onClick={() => handleRowClick(item)}
                  >
                    <TableCell className="max-w-[300px]">
                      {item.loai_cong_trinh}
                    </TableCell>
                    <TableCell>{item.don_vi || "-"}</TableCell>
                    <TableCell className="text-right font-medium">
                      {formatVND(item.suat_von)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatVND(item.trong_do_xd)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatVND(item.trong_do_tb)}
                    </TableCell>
                    <TableCell className="text-center">
                      {item.nam || "-"}
                    </TableCell>
                    <TableCell>
                      {item.quyet_dinh ? (
                        <Badge variant="secondary">{item.quyet_dinh}</Badge>
                      ) : (
                        "-"
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
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

      {/* Calculator */}
      {selectedRow && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Ước tính chi phí theo suất vốn đầu tư
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-sm text-muted-foreground">
              Công trình:{" "}
              <span className="font-medium text-foreground">
                {selectedRow.loai_cong_trinh}
              </span>
              {" - "}Suất vốn:{" "}
              <span className="font-medium text-foreground">
                {formatVND(selectedRow.suat_von)}
              </span>
              {selectedRow.don_vi && ` / ${selectedRow.don_vi}`}
            </div>

            <div className="flex items-end gap-3">
              <div className="space-y-1">
                <label className="text-sm text-muted-foreground">
                  Diện tích / Số lượng
                  {selectedRow.don_vi && ` (${selectedRow.don_vi})`}
                </label>
                <Input
                  type="number"
                  placeholder="Nhập diện tích hoặc số lượng..."
                  value={dienTich}
                  onChange={(e) => setDienTich(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleCalculate();
                  }}
                  className="w-64"
                />
              </div>
              <Button onClick={handleCalculate} disabled={calculating}>
                {calculating ? "Đang tính..." : "Tính"}
              </Button>
            </div>

            {calcError && (
              <div className="text-sm text-destructive">{calcError}</div>
            )}

            {calcResult && (
              <Card className="bg-muted/30">
                <CardContent className="pt-4 space-y-3">
                  <div className="text-lg font-semibold">
                    Tổng ước tính:{" "}
                    {calcResult.tong_uoc_tinh.toLocaleString("vi-VN")} đồng
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">
                        Suất vốn x Diện tích:
                      </span>
                      <div className="font-medium">
                        {formatVND(calcResult.suat_von)} x{" "}
                        {calcResult.dien_tich.toLocaleString("vi-VN")}
                      </div>
                    </div>
                    <div>
                      <span className="text-muted-foreground">
                        Ước tính xây dựng:
                      </span>
                      <div className="font-medium">
                        {calcResult.uoc_tinh_xd.toLocaleString("vi-VN")} đồng
                      </div>
                    </div>
                    <div>
                      <span className="text-muted-foreground">
                        Ước tính thiết bị:
                      </span>
                      <div className="font-medium">
                        {calcResult.uoc_tinh_tb.toLocaleString("vi-VN")} đồng
                      </div>
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Công trình: {calcResult.loai_cong_trinh}
                    {calcResult.don_vi && ` | Đơn vị: ${calcResult.don_vi}`}
                  </div>
                </CardContent>
              </Card>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
