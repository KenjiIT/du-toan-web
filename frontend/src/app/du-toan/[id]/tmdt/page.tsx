"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import {
  getTmdt,
  createOtherCost,
  updateOtherCost,
  deleteOtherCost,
  initDefaultOtherCosts,
  getExportTmdtExcelUrl,
} from "@/lib/api";
import type { TmdtCategory, TmdtCategoryItem, OtherCostCreate } from "@/lib/types";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export default function TmdtPage() {
  const params = useParams();
  const projectId = Number(params.id);
  const queryClient = useQueryClient();

  const [editingCell, setEditingCell] = useState<{
    id: number;
    field: "percent_value" | "fixed_value";
  } | null>(null);
  const [editValue, setEditValue] = useState("");
  const [addingTo, setAddingTo] = useState<string | null>(null);
  const [newName, setNewName] = useState("");
  const [newCalcType, setNewCalcType] = useState("percent");
  const [newValue, setNewValue] = useState("");

  const { data: tmdt, isLoading } = useQuery({
    queryKey: ["tmdt", projectId],
    queryFn: () => getTmdt(projectId),
    enabled: !isNaN(projectId),
  });

  const initMutation = useMutation({
    mutationFn: () => initDefaultOtherCosts(projectId),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["tmdt", projectId] }),
  });

  const createMutation = useMutation({
    mutationFn: (data: OtherCostCreate) => createOtherCost(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tmdt", projectId] });
      setAddingTo(null);
      setNewName("");
      setNewValue("");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({
      costId,
      data,
    }: {
      costId: number;
      data: Partial<OtherCostCreate>;
    }) => updateOtherCost(projectId, costId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tmdt", projectId] });
      setEditingCell(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (costId: number) => deleteOtherCost(projectId, costId),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["tmdt", projectId] }),
  });

  if (isLoading) {
    return <p className="text-muted-foreground">Đang tải...</p>;
  }

  if (!tmdt) {
    return <p className="text-red-600">Không thể tải dữ liệu TMĐT</p>;
  }

  const hasItems = tmdt.categories.some((c) => c.items.length > 0);

  function handleSaveEdit(item: TmdtCategoryItem) {
    if (!editingCell) return;
    const val = parseFloat(editValue);
    if (isNaN(val)) {
      setEditingCell(null);
      return;
    }
    if (editingCell.field === "percent_value") {
      updateMutation.mutate({
        costId: item.id,
        data: { percent_value: val },
      });
    } else if (editingCell.field === "fixed_value") {
      updateMutation.mutate({
        costId: item.id,
        data: { fixed_value: val },
      });
    }
  }

  function handleCalcTypeChange(item: TmdtCategoryItem, newType: string) {
    if (newType === "percent") {
      updateMutation.mutate({
        costId: item.id,
        data: {
          calc_type: "percent",
          percent_value: item.percent_value ?? 0,
          fixed_value: null,
        },
      });
    } else {
      updateMutation.mutate({
        costId: item.id,
        data: {
          calc_type: "fixed",
          fixed_value: item.fixed_value ?? 0,
          percent_value: null,
        },
      });
    }
  }

  function handleAddItem(category: string) {
    if (!newName.trim()) return;
    const data: OtherCostCreate = {
      category,
      name: newName.trim(),
      calc_type: newCalcType,
    };
    const val = parseFloat(newValue);
    if (!isNaN(val)) {
      if (newCalcType === "percent") {
        data.percent_value = val;
      } else {
        data.fixed_value = val;
      }
    }
    createMutation.mutate(data);
  }

  function renderCategorySection(cat: TmdtCategory) {
    const baseLabel =
      cat.category === "du_phong" ? "tổng trước DP" : "GXD";

    return (
      <Card key={cat.category} className="overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 bg-muted/30">
          <h3 className="font-semibold">{cat.label}</h3>
          <span className="font-semibold">{formatVND(cat.subtotal)}</span>
        </div>
        <div className="overflow-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">STT</TableHead>
                <TableHead>Khoản mục</TableHead>
                <TableHead className="w-32">Cách tính</TableHead>
                <TableHead className="w-28 text-right">Giá trị</TableHead>
                <TableHead className="w-36 text-right">Thành tiền</TableHead>
                <TableHead className="w-20"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {cat.items.map((item, idx) => (
                <TableRow key={item.id}>
                  <TableCell className="text-center">{idx + 1}</TableCell>
                  <TableCell>{item.name}</TableCell>
                  <TableCell>
                    <Select
                      value={item.calc_type}
                      onValueChange={(v) => handleCalcTypeChange(item, v ?? "fixed")}
                    >
                      <SelectTrigger className="h-8 text-sm">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="percent">
                          % {baseLabel}
                        </SelectItem>
                        <SelectItem value="fixed">Cố định</SelectItem>
                      </SelectContent>
                    </Select>
                  </TableCell>
                  <TableCell className="text-right">
                    {editingCell?.id === item.id &&
                    (editingCell.field === "percent_value" ||
                      editingCell.field === "fixed_value") ? (
                      <Input
                        type="number"
                        step="any"
                        className="w-24 h-7 text-right text-sm"
                        value={editValue}
                        autoFocus
                        onChange={(e) => setEditValue(e.target.value)}
                        onBlur={() => handleSaveEdit(item)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter")
                            (e.target as HTMLInputElement).blur();
                          if (e.key === "Escape") setEditingCell(null);
                        }}
                      />
                    ) : (
                      <span
                        className="cursor-pointer hover:underline"
                        onClick={() => {
                          const field =
                            item.calc_type === "percent"
                              ? "percent_value"
                              : "fixed_value";
                          const val =
                            item.calc_type === "percent"
                              ? item.percent_value
                              : item.fixed_value;
                          setEditingCell({ id: item.id, field });
                          setEditValue(String(val ?? 0));
                        }}
                      >
                        {item.calc_type === "percent"
                          ? `${item.percent_value ?? 0}%`
                          : formatVND(item.fixed_value ?? 0)}
                      </span>
                    )}
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {formatVND(item.amount)}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-red-500 h-7 px-2"
                      onClick={() => {
                        if (confirm("Xóa khoản mục này?"))
                          deleteMutation.mutate(item.id);
                      }}
                    >
                      Xóa
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {addingTo === cat.category && (
                <TableRow>
                  <TableCell></TableCell>
                  <TableCell>
                    <Input
                      className="h-8 text-sm"
                      placeholder="Tên khoản mục"
                      value={newName}
                      autoFocus
                      onChange={(e) => setNewName(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") handleAddItem(cat.category);
                        if (e.key === "Escape") setAddingTo(null);
                      }}
                    />
                  </TableCell>
                  <TableCell>
                    <Select value={newCalcType} onValueChange={(v) => setNewCalcType(v ?? "fixed")}>
                      <SelectTrigger className="h-8 text-sm">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="percent">%</SelectItem>
                        <SelectItem value="fixed">Cố định</SelectItem>
                      </SelectContent>
                    </Select>
                  </TableCell>
                  <TableCell>
                    <Input
                      type="number"
                      step="any"
                      className="w-24 h-8 text-right text-sm"
                      placeholder={newCalcType === "percent" ? "%" : "VND"}
                      value={newValue}
                      onChange={(e) => setNewValue(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") handleAddItem(cat.category);
                        if (e.key === "Escape") setAddingTo(null);
                      }}
                    />
                  </TableCell>
                  <TableCell>
                    <Button
                      size="sm"
                      className="h-7"
                      onClick={() => handleAddItem(cat.category)}
                    >
                      Lưu
                    </Button>
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7"
                      onClick={() => setAddingTo(null)}
                    >
                      Hủy
                    </Button>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
        {addingTo !== cat.category && (
          <div className="px-4 py-2 border-t">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setAddingTo(cat.category);
                setNewName("");
                setNewCalcType("percent");
                setNewValue("");
              }}
            >
              + Thêm khoản mục
            </Button>
          </div>
        )}
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <Link
          href={`/du-toan/${projectId}`}
          className="text-sm text-muted-foreground hover:underline"
        >
          &larr; Quay lại dự toán
        </Link>
        <div className="flex items-center justify-between mt-2">
          <h1 className="text-2xl font-bold">Tổng mức đầu tư</h1>
          <div className="flex gap-2">
            {!hasItems && (
              <Button
                onClick={() => initMutation.mutate()}
                disabled={initMutation.isPending}
              >
                Khởi tạo mặc định
              </Button>
            )}
            <Button
              variant="outline"
              onClick={() =>
                window.open(getExportTmdtExcelUrl(projectId), "_blank")
              }
            >
              Xuất Excel TMĐT
            </Button>
          </div>
        </div>
      </div>

      {/* G_XD display */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold">Chi phí xây dựng (GXD)</h3>
            <p className="text-sm text-muted-foreground">
              Từ bảng dự toán chi tiết
            </p>
          </div>
          <span className="text-xl font-bold">{formatVND(tmdt.g_xd)}</span>
        </div>
      </Card>

      {/* Category sections */}
      {tmdt.categories.map((cat) => renderCategorySection(cat))}

      {/* Summary */}
      <Card className="p-4 space-y-3">
        <h3 className="font-semibold text-lg">Tổng hợp</h3>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span>Chi phí xây dựng (GXD)</span>
            <span className="font-medium">{formatVND(tmdt.g_xd)}</span>
          </div>
          <div className="flex justify-between">
            <span>Chi phí thiết bị (GTB)</span>
            <span className="font-medium">{formatVND(tmdt.g_tb)}</span>
          </div>
          <div className="flex justify-between">
            <span>Chi phí tư vấn (GTV)</span>
            <span className="font-medium">{formatVND(tmdt.g_tv)}</span>
          </div>
          <div className="flex justify-between">
            <span>Chi phí QLDA</span>
            <span className="font-medium">{formatVND(tmdt.g_qlda)}</span>
          </div>
          <div className="flex justify-between">
            <span>Chi phí khác (GK)</span>
            <span className="font-medium">{formatVND(tmdt.g_k)}</span>
          </div>
          <div className="flex justify-between border-t pt-2">
            <span className="font-semibold">Tổng trước dự phòng</span>
            <span className="font-semibold">
              {formatVND(tmdt.subtotal_before_dp)}
            </span>
          </div>
          <div className="flex justify-between">
            <span>Chi phí dự phòng (GĐP)</span>
            <span className="font-medium">{formatVND(tmdt.g_dp)}</span>
          </div>
          <div className="flex justify-between border-t pt-2 text-lg">
            <span className="font-bold">TỔNG MỨC ĐẦU TƯ</span>
            <span className="font-bold text-primary">
              {formatVND(tmdt.tmdt)}
            </span>
          </div>
        </div>
      </Card>
    </div>
  );
}
