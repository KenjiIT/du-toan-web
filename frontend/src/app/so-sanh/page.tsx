"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { compareDonGia, compareVatTu, getCompareSources } from "@/lib/api";
import type { DonGiaCompareResult, VatTuCompareResult } from "@/lib/types";
import { formatVND } from "@/lib/formatters";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type SearchMode = "don-gia" | "vat-tu";

export default function SoSanhPage() {
  const [mode, setMode] = useState<SearchMode>("don-gia");
  const [searchCode, setSearchCode] = useState("");
  const [selectedSources, setSelectedSources] = useState<Set<string>>(new Set());
  const [searchTrigger, setSearchTrigger] = useState<{
    mode: SearchMode;
    code: string;
    sources: string[];
  } | null>(null);

  const { data: sources } = useQuery({
    queryKey: ["compare-sources"],
    queryFn: getCompareSources,
  });

  const {
    data: donGiaResult,
    isLoading: donGiaLoading,
    error: donGiaError,
  } = useQuery({
    queryKey: ["compare-don-gia", searchTrigger?.code, searchTrigger?.sources],
    queryFn: () => compareDonGia(searchTrigger!.code, searchTrigger!.sources),
    enabled: searchTrigger?.mode === "don-gia" && !!searchTrigger?.code,
  });

  const {
    data: vatTuResult,
    isLoading: vatTuLoading,
    error: vatTuError,
  } = useQuery({
    queryKey: ["compare-vat-tu", searchTrigger?.code, searchTrigger?.sources],
    queryFn: () => compareVatTu(searchTrigger!.code, searchTrigger!.sources),
    enabled: searchTrigger?.mode === "vat-tu" && !!searchTrigger?.code,
  });

  const isLoading = donGiaLoading || vatTuLoading;
  const error = donGiaError || vatTuError;

  const toggleSource = (source: string) => {
    setSelectedSources((prev) => {
      const next = new Set(prev);
      if (next.has(source)) next.delete(source);
      else next.add(source);
      return next;
    });
  };

  const selectAllSources = () => {
    if (sources) {
      setSelectedSources(new Set(sources));
    }
  };

  const handleSearch = () => {
    if (!searchCode.trim()) return;
    const srcList = selectedSources.size > 0 ? Array.from(selectedSources) : (sources || []);
    setSearchTrigger({ mode, code: searchCode.trim(), sources: srcList });
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">So sánh giá</h1>

      <Card className="p-6">
        <div className="space-y-4">
          {/* Mode selection */}
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium">Loại tra cứu:</span>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="mode"
                checked={mode === "don-gia"}
                onChange={() => setMode("don-gia")}
                className="accent-primary"
              />
              <span className="text-sm">Đơn giá (mã hiệu đơn giá)</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="mode"
                checked={mode === "vat-tu"}
                onChange={() => setMode("vat-tu")}
                className="accent-primary"
              />
              <span className="text-sm">Vật tư (mã số vật tư)</span>
            </label>
          </div>

          {/* Search input */}
          <div className="flex gap-2">
            <Input
              placeholder={mode === "don-gia" ? "Nhập mã hiệu đơn giá (vd: AF.11111)" : "Nhập mã số vật tư (vd: V0101)"}
              value={searchCode}
              onChange={(e) => setSearchCode(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") handleSearch(); }}
              className="max-w-md"
            />
            <Button onClick={handleSearch} disabled={isLoading || !searchCode.trim()}>
              {isLoading ? "Đang tìm..." : "So sánh"}
            </Button>
          </div>

          {/* Source checkboxes */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm font-medium">Nguồn giá:</span>
              <Button variant="outline" size="sm" onClick={selectAllSources}>
                Chọn tất cả
              </Button>
              <Button variant="outline" size="sm" onClick={() => setSelectedSources(new Set())}>
                Bỏ chọn
              </Button>
            </div>
            <div className="flex flex-wrap gap-3">
              {sources?.map((src) => (
                <label key={src} className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedSources.has(src)}
                    onChange={() => toggleSource(src)}
                    className="accent-primary"
                  />
                  <span className="text-sm">{src}</span>
                </label>
              ))}
              {!sources && (
                <span className="text-sm text-muted-foreground">Đang tải nguồn giá...</span>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* Error */}
      {error && (
        <Card className="p-4 border-red-200 bg-red-50">
          <p className="text-sm text-red-600">
            Lỗi: {error instanceof Error ? error.message : "Không tìm thấy dữ liệu"}
          </p>
        </Card>
      )}

      {/* Don Gia results */}
      {donGiaResult && searchTrigger?.mode === "don-gia" && (
        <DonGiaCompareTable result={donGiaResult} />
      )}

      {/* Vat Tu results */}
      {vatTuResult && searchTrigger?.mode === "vat-tu" && (
        <VatTuCompareTable result={vatTuResult} />
      )}
    </div>
  );
}

function DonGiaCompareTable({ result }: { result: DonGiaCompareResult }) {
  const comparisons = result.comparisons;
  if (comparisons.length === 0) {
    return (
      <Card className="p-4">
        <p className="text-muted-foreground">Không tìm thấy dữ liệu so sánh.</p>
      </Card>
    );
  }

  const totals = comparisons.map((c) => c.total);
  const minTotal = Math.min(...totals);
  const maxTotal = Math.max(...totals);
  const hasRange = minTotal !== maxTotal;

  return (
    <Card className="overflow-hidden">
      <div className="p-4 border-b">
        <h2 className="font-semibold text-lg">
          {result.mhdg} - {result.tcv}
        </h2>
        <p className="text-sm text-muted-foreground">
          Đơn vị: {result.dvt}
        </p>
      </div>
      <div className="overflow-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nguồn giá</TableHead>
              <TableHead className="text-right">VLC</TableHead>
              <TableHead className="text-right">NC</TableHead>
              <TableHead className="text-right">MTC</TableHead>
              <TableHead className="text-right">Tổng</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {comparisons.map((c) => {
              const isMin = hasRange && c.total === minTotal;
              const isMax = hasRange && c.total === maxTotal;
              return (
                <TableRow
                  key={c.source}
                  className={
                    isMin
                      ? "bg-green-50"
                      : isMax
                        ? "bg-red-50"
                        : ""
                  }
                >
                  <TableCell className="font-medium">
                    {c.source}
                    {isMin && <span className="ml-2 text-xs text-green-700 font-semibold">Thấp nhất</span>}
                    {isMax && <span className="ml-2 text-xs text-red-700 font-semibold">Cao nhất</span>}
                  </TableCell>
                  <TableCell className="text-right">{formatVND(c.vlc)}</TableCell>
                  <TableCell className="text-right">{formatVND(c.nc)}</TableCell>
                  <TableCell className="text-right">{formatVND(c.mtc)}</TableCell>
                  <TableCell className={`text-right font-semibold ${isMin ? "text-green-700" : isMax ? "text-red-700" : ""}`}>
                    {formatVND(c.total)}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </Card>
  );
}

function VatTuCompareTable({ result }: { result: VatTuCompareResult }) {
  const comparisons = result.comparisons;
  if (comparisons.length === 0) {
    return (
      <Card className="p-4">
        <p className="text-muted-foreground">Không tìm thấy dữ liệu so sánh.</p>
      </Card>
    );
  }

  const prices = comparisons.map((c) => c.gia_goc);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const hasRange = minPrice !== maxPrice;

  return (
    <Card className="overflow-hidden">
      <div className="p-4 border-b">
        <h2 className="font-semibold text-lg">
          {result.msvt} - {result.tvt}
        </h2>
        <p className="text-sm text-muted-foreground">
          Đơn vị: {result.dvt}
        </p>
      </div>
      <div className="overflow-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nguồn giá</TableHead>
              <TableHead className="text-right">Giá gốc</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {comparisons.map((c) => {
              const isMin = hasRange && c.gia_goc === minPrice;
              const isMax = hasRange && c.gia_goc === maxPrice;
              return (
                <TableRow
                  key={c.source}
                  className={
                    isMin
                      ? "bg-green-50"
                      : isMax
                        ? "bg-red-50"
                        : ""
                  }
                >
                  <TableCell className="font-medium">
                    {c.source}
                    {isMin && <span className="ml-2 text-xs text-green-700 font-semibold">Thấp nhất</span>}
                    {isMax && <span className="ml-2 text-xs text-red-700 font-semibold">Cao nhất</span>}
                  </TableCell>
                  <TableCell className={`text-right font-semibold ${isMin ? "text-green-700" : isMax ? "text-red-700" : ""}`}>
                    {formatVND(c.gia_goc)}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </Card>
  );
}
