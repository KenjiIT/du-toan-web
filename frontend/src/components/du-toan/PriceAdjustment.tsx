"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getPriceAdjustment, getPriceAdjustmentSources } from "@/lib/api";
import type { BuGiaResponse, BuGiaItemDetail } from "@/lib/types";
import { formatVND, formatNumber } from "@/lib/formatters";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface PriceAdjustmentProps {
  projectId: number;
}

export function PriceAdjustment({ projectId }: PriceAdjustmentProps) {
  const [sourceMarket, setSourceMarket] = useState<string>("");
  const [enabled, setEnabled] = useState(false);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  const { data: sources, isLoading: loadingSources } = useQuery({
    queryKey: ["bu-gia-sources", projectId],
    queryFn: () => getPriceAdjustmentSources(projectId),
  });

  const {
    data: result,
    isLoading: loadingResult,
    isFetching,
  } = useQuery({
    queryKey: ["bu-gia", projectId, sourceMarket],
    queryFn: () => getPriceAdjustment(projectId, sourceMarket),
    enabled: enabled && !!sourceMarket,
  });

  const toggleItem = (mhdg: string) => {
    setExpandedItems((prev) => {
      const next = new Set(prev);
      if (next.has(mhdg)) next.delete(mhdg);
      else next.add(mhdg);
      return next;
    });
  };

  const handleCalculate = () => {
    if (sourceMarket) {
      setEnabled(true);
    }
  };

  // Set default source when sources load
  if (sources && sources.length > 0 && !sourceMarket) {
    setSourceMarket(sources[0]);
  }

  return (
    <Card className="p-4">
      <h3 className="text-lg font-semibold mb-4">
        {`Bù giá vật tư`}
      </h3>
      <div className="flex items-center gap-3 mb-4">
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground whitespace-nowrap">
            {`Nguồn giá thị trường:`}
          </span>
          <Select
            value={sourceMarket}
            onValueChange={(v) => {
              setSourceMarket(v ?? "");
              setEnabled(false);
            }}
          >
            <SelectTrigger className="w-[200px]">
              <SelectValue
                placeholder={
                  loadingSources
                    ? `Đang tải...`
                    : `Chọn nguồn giá`
                }
              />
            </SelectTrigger>
            <SelectContent>
              {sources?.map((s) => (
                <SelectItem key={s} value={s}>
                  {s}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Button
          onClick={handleCalculate}
          disabled={!sourceMarket || isFetching}
        >
          {isFetching
            ? `Đang tính...`
            : `Tính bù giá`}
        </Button>
      </div>

      {loadingResult && (
        <p className="text-muted-foreground text-sm">
          {`Đang tính toán bù giá...`}
        </p>
      )}

      {result && (
        <div className="space-y-4">
          {/* Summary table */}
          <div className="overflow-auto border rounded-md">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10">STT</TableHead>
                  <TableHead className="w-24">{`Mã VT`}</TableHead>
                  <TableHead>{`Tên vật tư`}</TableHead>
                  <TableHead className="w-16">{`ĐVT`}</TableHead>
                  <TableHead className="w-28 text-right">{`Tổng HP`}</TableHead>
                  <TableHead className="w-28 text-right">{`Giá ĐM`}</TableHead>
                  <TableHead className="w-28 text-right">{`Giá TT`}</TableHead>
                  <TableHead className="w-28 text-right">
                    {`Chênh lệch/đv`}
                  </TableHead>
                  <TableHead className="w-32 text-right">
                    {`Thành tiền CL`}
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {result.materials.map((mat, idx) => (
                  <TableRow key={mat.msvt}>
                    <TableCell className="text-center">{idx + 1}</TableCell>
                    <TableCell className="font-mono text-xs">
                      {mat.msvt}
                    </TableCell>
                    <TableCell className="max-w-xs truncate">
                      {mat.tvt}
                    </TableCell>
                    <TableCell>{mat.dvt}</TableCell>
                    <TableCell className="text-right">
                      {formatNumber(mat.total_hao_phi, 4)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatVND(mat.gia_dm)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatVND(mat.gia_tt)}
                    </TableCell>
                    <TableCell
                      className={`text-right font-medium ${
                        mat.chenh_lech_dv > 0
                          ? "text-red-600"
                          : mat.chenh_lech_dv < 0
                            ? "text-green-600"
                            : ""
                      }`}
                    >
                      {formatVND(mat.chenh_lech_dv)}
                    </TableCell>
                    <TableCell
                      className={`text-right font-medium ${
                        mat.chenh_lech_tt > 0
                          ? "text-red-600"
                          : mat.chenh_lech_tt < 0
                            ? "text-green-600"
                            : ""
                      }`}
                    >
                      {formatVND(mat.chenh_lech_tt)}
                    </TableCell>
                  </TableRow>
                ))}
                {result.materials.length === 0 && (
                  <TableRow>
                    <TableCell
                      colSpan={9}
                      className="text-center py-6 text-muted-foreground"
                    >
                      {`Không có chênh lệch giá vật tư`}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>

          {/* Total */}
          <div className="flex justify-end">
            <div
              className={`text-lg font-bold px-4 py-2 rounded-md ${
                result.total_bu_gia > 0
                  ? "bg-red-50 text-red-700"
                  : result.total_bu_gia < 0
                    ? "bg-green-50 text-green-700"
                    : "bg-muted"
              }`}
            >
              {`Tổng bù giá VL: `}{formatVND(result.total_bu_gia)}
            </div>
          </div>

          {/* Per-item detail (collapsible) */}
          {result.items_detail.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold mb-2 text-muted-foreground">
                {`Chi tiết theo công việc`}
              </h4>
              <div className="space-y-1">
                {result.items_detail.map((item) => (
                  <div key={item.mhdg} className="border rounded-md">
                    <div
                      className="flex items-center justify-between px-3 py-2 cursor-pointer hover:bg-muted/30"
                      onClick={() => toggleItem(item.mhdg)}
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-xs">
                          {expandedItems.has(item.mhdg) ? "▼" : "▶"}
                        </span>
                        <span className="font-mono text-xs">
                          {item.mhdg}
                        </span>
                        <span className="text-sm truncate max-w-md">
                          {item.tcv}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          (SL: {item.quantity})
                        </span>
                      </div>
                      <span
                        className={`text-sm font-medium ${
                          item.bu_gia_item > 0
                            ? "text-red-600"
                            : item.bu_gia_item < 0
                              ? "text-green-600"
                              : ""
                        }`}
                      >
                        {formatVND(item.bu_gia_item)}
                      </span>
                    </div>
                    {expandedItems.has(item.mhdg) && (
                      <div className="px-3 pb-2">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead className="w-24 text-xs">
                                {`Mã VT`}
                              </TableHead>
                              <TableHead className="text-xs">
                                {`Tên vật tư`}
                              </TableHead>
                              <TableHead className="w-20 text-right text-xs">
                                {`Hao phí`}
                              </TableHead>
                              <TableHead className="w-24 text-right text-xs">
                                {`Giá ĐM`}
                              </TableHead>
                              <TableHead className="w-24 text-right text-xs">
                                {`Giá TT`}
                              </TableHead>
                              <TableHead className="w-24 text-right text-xs">
                                {`CL/đv`}
                              </TableHead>
                              <TableHead className="w-28 text-right text-xs">
                                {`Thành tiền`}
                              </TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {item.materials.map((m) => (
                              <TableRow key={m.msvt}>
                                <TableCell className="font-mono text-xs">
                                  {m.msvt}
                                </TableCell>
                                <TableCell className="text-xs truncate max-w-xs">
                                  {m.tvt}
                                </TableCell>
                                <TableCell className="text-right text-xs">
                                  {formatNumber(m.hao_phi, 4)}
                                </TableCell>
                                <TableCell className="text-right text-xs">
                                  {formatVND(m.gia_dm)}
                                </TableCell>
                                <TableCell className="text-right text-xs">
                                  {formatVND(m.gia_tt)}
                                </TableCell>
                                <TableCell
                                  className={`text-right text-xs font-medium ${
                                    m.chenh_lech_dv > 0
                                      ? "text-red-600"
                                      : m.chenh_lech_dv < 0
                                        ? "text-green-600"
                                        : ""
                                  }`}
                                >
                                  {formatVND(m.chenh_lech_dv)}
                                </TableCell>
                                <TableCell
                                  className={`text-right text-xs font-medium ${
                                    m.chenh_lech_tt > 0
                                      ? "text-red-600"
                                      : m.chenh_lech_tt < 0
                                        ? "text-green-600"
                                        : ""
                                  }`}
                                >
                                  {formatVND(m.chenh_lech_tt)}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}
