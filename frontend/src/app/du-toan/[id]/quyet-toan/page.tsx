"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import {
  getSettlement,
  updateItemSettlement,
  getExportSettlementExcelUrl,
} from "@/lib/api";
import type { SettlementItem } from "@/lib/types";
import { formatVND } from "@/lib/formatters";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export default function SettlementPage() {
  const params = useParams();
  const projectId = Number(params.id);
  const queryClient = useQueryClient();

  const [editingQty, setEditingQty] = useState<number | null>(null);
  const [qtyValue, setQtyValue] = useState("");
  const [editingNotes, setEditingNotes] = useState<number | null>(null);
  const [notesValue, setNotesValue] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["settlement", projectId],
    queryFn: () => getSettlement(projectId),
    enabled: !isNaN(projectId),
  });

  const updateMutation = useMutation({
    mutationFn: ({
      itemId,
      data: updateData,
    }: {
      itemId: number;
      data: Parameters<typeof updateItemSettlement>[2];
    }) => updateItemSettlement(projectId, itemId, updateData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settlement", projectId] });
      setEditingQty(null);
      setEditingNotes(null);
    },
  });

  if (isLoading) {
    return <p className="text-muted-foreground">Đang tải dữ liệu quyết toán...</p>;
  }

  if (!data) {
    return <p className="text-red-600">Không tìm thấy dữ liệu quyết toán</p>;
  }

  const {
    project_name,
    items,
    total_du_toan,
    total_thuc_te,
    total_chenh_lech,
    pct_hoan_thanh,
    items_with_actual,
    total_items,
  } = data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Link
            href={`/du-toan/${projectId}`}
            className="text-sm text-muted-foreground hover:underline"
          >
            ← Quay lại dự toán
          </Link>
        </div>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold">Quyết toán: {project_name}</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Đã nhập {items_with_actual}/{total_items} công việc
            </p>
          </div>
          <Button
            variant="outline"
            onClick={() =>
              window.open(getExportSettlementExcelUrl(projectId), "_blank")
            }
          >
            Xuất Excel quyết toán
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4 bg-blue-50 dark:bg-blue-950/30">
          <div className="text-sm text-muted-foreground">Tổng dự toán</div>
          <div className="text-lg font-bold text-blue-700 dark:text-blue-400">
            {formatVND(total_du_toan)}
          </div>
        </Card>
        <Card className="p-4 bg-green-50 dark:bg-green-950/30">
          <div className="text-sm text-muted-foreground">Tổng thực tế</div>
          <div className="text-lg font-bold text-green-700 dark:text-green-400">
            {formatVND(total_thuc_te)}
          </div>
        </Card>
        <Card
          className={`p-4 ${
            total_chenh_lech > 0
              ? "bg-red-50 dark:bg-red-950/30"
              : "bg-emerald-50 dark:bg-emerald-950/30"
          }`}
        >
          <div className="text-sm text-muted-foreground">Chênh lệch</div>
          <div
            className={`text-lg font-bold ${
              total_chenh_lech > 0
                ? "text-red-700 dark:text-red-400"
                : "text-emerald-700 dark:text-emerald-400"
            }`}
          >
            {formatVND(total_chenh_lech)}
          </div>
        </Card>
        <Card className="p-4 bg-purple-50 dark:bg-purple-950/30">
          <div className="text-sm text-muted-foreground">% hoàn thành</div>
          <div className="text-lg font-bold text-purple-700 dark:text-purple-400">
            {pct_hoan_thanh.toFixed(1)}%
          </div>
        </Card>
      </div>

      {/* Section Summaries */}
      {data.sections.length > 0 && (
        <Card className="p-4">
          <h3 className="text-sm font-semibold mb-3">Tổng hợp theo phần</h3>
          <div className="space-y-2">
            {data.sections.map((section, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between text-sm border-b pb-2 last:border-0"
              >
                <span className="font-medium">
                  {section.section_name ?? "Chưa phân loại"}
                </span>
                <div className="flex gap-6">
                  <span className="text-muted-foreground">
                    DT: {formatVND(section.total_du_toan)}
                  </span>
                  <span className="text-muted-foreground">
                    TT: {formatVND(section.total_thuc_te)}
                  </span>
                  <span
                    className={
                      section.chenh_lech > 0 ? "text-red-600" : "text-green-600"
                    }
                  >
                    CL: {formatVND(section.chenh_lech)}
                  </span>
                  <Badge variant="outline">{section.item_count} CV</Badge>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Items Table */}
      <div className="border rounded-md overflow-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-12">STT</TableHead>
              <TableHead className="w-28">Mã</TableHead>
              <TableHead>Tên công việc</TableHead>
              <TableHead className="w-16">ĐVT</TableHead>
              <TableHead className="w-24 text-right">KL dự toán</TableHead>
              <TableHead className="w-28 text-right">KL thực tế</TableHead>
              <TableHead className="w-28">Ngày NT</TableHead>
              <TableHead className="w-32 text-right">TT Dự toán</TableHead>
              <TableHead className="w-32 text-right">TT Thực tế</TableHead>
              <TableHead className="w-32 text-right">Chênh lệch</TableHead>
              <TableHead className="w-40">Ghi chú</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((item: SettlementItem, idx: number) => {
              const isOverBudget = item.chenh_lech > 0;
              return (
                <TableRow
                  key={idx}
                  className={
                    item.actual_quantity !== null
                      ? isOverBudget
                        ? "bg-red-50/50 dark:bg-red-950/10"
                        : "bg-green-50/50 dark:bg-green-950/10"
                      : ""
                  }
                >
                  <TableCell className="text-center">{idx + 1}</TableCell>
                  <TableCell className="font-mono text-xs">
                    {item.mhdg}
                  </TableCell>
                  <TableCell className="max-w-xs truncate">
                    {item.tcv}
                  </TableCell>
                  <TableCell>{item.dvt}</TableCell>
                  <TableCell className="text-right">{item.quantity}</TableCell>
                  <TableCell className="text-right">
                    {editingQty === item.id ? (
                      <Input
                        type="number"
                        step="any"
                        className="w-24 h-7 text-right text-sm"
                        value={qtyValue}
                        autoFocus
                        onChange={(e) => setQtyValue(e.target.value)}
                        onBlur={() => {
                          const v = parseFloat(qtyValue);
                          if (!isNaN(v)) {
                            updateMutation.mutate({
                              itemId: item.id,
                              data: { actual_quantity: v },
                            });
                          } else if (qtyValue === "") {
                            updateMutation.mutate({
                              itemId: item.id,
                              data: { actual_quantity: null },
                            });
                          } else {
                            setEditingQty(null);
                          }
                        }}
                        onKeyDown={(e) => {
                          if (e.key === "Enter")
                            (e.target as HTMLInputElement).blur();
                          if (e.key === "Escape") setEditingQty(null);
                        }}
                      />
                    ) : (
                      <span
                        className="cursor-pointer hover:underline"
                        onClick={() => {
                          setEditingQty(item.id);
                          setQtyValue(
                            item.actual_quantity !== null
                              ? String(item.actual_quantity)
                              : "",
                          );
                        }}
                      >
                        {item.actual_quantity !== null
                          ? item.actual_quantity
                          : "-"}
                      </span>
                    )}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {item.acceptance_date ?? "-"}
                  </TableCell>
                  <TableCell className="text-right">
                    {formatVND(item.thanh_tien_du_toan)}
                  </TableCell>
                  <TableCell className="text-right">
                    {formatVND(item.thanh_tien_thuc_te)}
                  </TableCell>
                  <TableCell
                    className={`text-right font-medium ${
                      isOverBudget ? "text-red-600" : "text-green-600"
                    }`}
                  >
                    {item.actual_quantity !== null
                      ? formatVND(item.chenh_lech)
                      : "-"}
                  </TableCell>
                  <TableCell>
                    {editingNotes === item.id ? (
                      <Input
                        type="text"
                        className="w-36 h-7 text-sm"
                        value={notesValue}
                        autoFocus
                        onChange={(e) => setNotesValue(e.target.value)}
                        onBlur={() => {
                          updateMutation.mutate({
                            itemId: item.id,
                            data: {
                              acceptance_notes: notesValue || null,
                            },
                          });
                        }}
                        onKeyDown={(e) => {
                          if (e.key === "Enter")
                            (e.target as HTMLInputElement).blur();
                          if (e.key === "Escape") setEditingNotes(null);
                        }}
                      />
                    ) : (
                      <span
                        className="cursor-pointer hover:underline text-sm text-muted-foreground"
                        onClick={() => {
                          setEditingNotes(item.id);
                          setNotesValue(item.acceptance_notes ?? "");
                        }}
                      >
                        {item.acceptance_notes || "-"}
                      </span>
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
            {items.length === 0 && (
              <TableRow>
                <TableCell
                  colSpan={11}
                  className="text-center py-8 text-muted-foreground"
                >
                  Chưa có công việc nào trong dự toán.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
