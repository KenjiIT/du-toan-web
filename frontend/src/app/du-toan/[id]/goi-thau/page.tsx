"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import {
  getProject,
  getBidPackages,
  createBidPackage,
  getBidPackageDetail,
  deleteBidPackage,
  assignItemsToBidPackage,
  removeItemsFromBidPackage,
  getExportBidPackageExcelUrl,
} from "@/lib/api";
import type { BidPackageSummary, BidPackageDetail, ProjectItem } from "@/lib/types";
import { formatVND } from "@/lib/formatters";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
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
import { ArrowLeft, Trash2, Download, Plus, X } from "lucide-react";

const PACKAGE_TYPES = [
  { value: "XD", label: "Xây dựng" },
  { value: "TB", label: "Thiết bị" },
  { value: "TV", label: "Tư vấn" },
  { value: "KS", label: "Khảo sát" },
];

function CostSummaryPanel({ cost }: { cost: BidPackageDetail["cost_breakdown"] }) {
  if (!cost) return null;
  const rows = [
    { label: "Chi phí vật liệu (VLC)", value: cost.vlc },
    { label: "Chi phí nhân công (NC)", value: cost.nc },
    { label: "Chi phí máy (MTC)", value: cost.mtc },
    { label: "Trực tiếp khác", value: cost.truc_tiep_khac },
    { label: "Chi phí trực tiếp (T)", value: cost.t, bold: true },
    { label: `Chi phí chung (C) - ${cost.chi_phi_chung_pct}%`, value: cost.c },
    { label: `Thu nhập chịu thuế (TL) - ${cost.thu_nhap_tt_pct}%`, value: cost.tl },
    { label: "Giá trị dự toán XD trước thuế (G)", value: cost.g, bold: true },
    { label: `Thuế GTGT - ${cost.vat_pct}%`, value: cost.gtgt },
    { label: "Giá trị dự toán XD sau thuế (GXD)", value: cost.gxd, bold: true },
  ];
  return (
    <Card className="p-4">
      <h3 className="font-semibold mb-3">Tổng hợp chi phí</h3>
      <div className="space-y-1">
        {rows.map((r) => (
          <div
            key={r.label}
            className={`flex justify-between text-sm ${r.bold ? "font-bold border-t pt-1" : ""}`}
          >
            <span>{r.label}</span>
            <span>{formatVND(r.value)}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}

function AssignItemsDialog({
  open,
  onOpenChange,
  unassignedItems,
  onAssign,
  isPending,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  unassignedItems: ProjectItem[];
  onAssign: (ids: number[]) => void;
  isPending: boolean;
}) {
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [filter, setFilter] = useState("");

  const filtered = filter
    ? unassignedItems.filter(
        (item) =>
          item.mhdg.toLowerCase().includes(filter.toLowerCase()) ||
          (item.tcv && item.tcv.toLowerCase().includes(filter.toLowerCase())),
      )
    : unassignedItems;

  const toggleItem = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (selected.size === filtered.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(filtered.map((i) => i.id)));
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Thêm công việc vào gói thầu</DialogTitle>
        </DialogHeader>
        <Input
          placeholder="Tìm theo mã hiệu hoặc tên..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="mb-2"
        />
        <div className="max-h-80 overflow-y-auto border rounded-md">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10">
                  <input
                    type="checkbox"
                    checked={filtered.length > 0 && selected.size === filtered.length}
                    onChange={toggleAll}
                    className="h-4 w-4 rounded border-gray-300"
                  />
                </TableHead>
                <TableHead className="w-28">Mã hiệu</TableHead>
                <TableHead>Tên công việc</TableHead>
                <TableHead className="w-16">ĐVT</TableHead>
                <TableHead className="w-24 text-right">Thành tiền</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((item) => (
                <TableRow
                  key={item.id}
                  className="cursor-pointer"
                  onClick={() => toggleItem(item.id)}
                >
                  <TableCell>
                    <input
                      type="checkbox"
                      checked={selected.has(item.id)}
                      onChange={() => toggleItem(item.id)}
                      className="h-4 w-4 rounded border-gray-300"
                    />
                  </TableCell>
                  <TableCell className="font-mono text-xs">{item.mhdg}</TableCell>
                  <TableCell className="max-w-xs truncate">{item.tcv}</TableCell>
                  <TableCell>{item.dvt}</TableCell>
                  <TableCell className="text-right">{formatVND(item.thanh_tien)}</TableCell>
                </TableRow>
              ))}
              {filtered.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                    Không có công việc chưa phân bổ
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <Button
            disabled={selected.size === 0 || isPending}
            onClick={() => onAssign(Array.from(selected))}
          >
            {isPending ? "Đang thêm..." : `Thêm ${selected.size} công việc`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function PackageDetailView({
  projectId,
  pkg,
  onClose,
}: {
  projectId: number;
  pkg: BidPackageSummary;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [showAssign, setShowAssign] = useState(false);
  const [removeSelected, setRemoveSelected] = useState<Set<number>>(new Set());

  const { data: detail, isLoading } = useQuery({
    queryKey: ["bid-package-detail", projectId, pkg.id],
    queryFn: () => getBidPackageDetail(projectId, pkg.id),
  });

  const { data: projectData } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => getProject(projectId),
    enabled: !isNaN(projectId),
  });

  // Get unassigned items from project
  const unassignedItems = (projectData?.items || []).filter(
    (item) => !detail?.items.some((di) => di.id === item.id),
  );

  const assignMutation = useMutation({
    mutationFn: (itemIds: number[]) => assignItemsToBidPackage(projectId, pkg.id, itemIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bid-package-detail", projectId, pkg.id] });
      queryClient.invalidateQueries({ queryKey: ["bid-packages", projectId] });
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      setShowAssign(false);
    },
  });

  const removeMutation = useMutation({
    mutationFn: (itemIds: number[]) => removeItemsFromBidPackage(projectId, pkg.id, itemIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bid-package-detail", projectId, pkg.id] });
      queryClient.invalidateQueries({ queryKey: ["bid-packages", projectId] });
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      setRemoveSelected(new Set());
    },
  });

  const toggleRemove = (id: number) => {
    setRemoveSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
          <h2 className="text-xl font-bold">{pkg.name}</h2>
          <Badge variant="outline">{pkg.package_type}</Badge>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => setShowAssign(true)}>
            <Plus className="h-4 w-4 mr-1" />
            Thêm công việc
          </Button>
          {removeSelected.size > 0 && (
            <Button
              variant="destructive"
              size="sm"
              disabled={removeMutation.isPending}
              onClick={() => removeMutation.mutate(Array.from(removeSelected))}
            >
              Bỏ {removeSelected.size} công việc
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.open(getExportBidPackageExcelUrl(projectId, pkg.id), "_blank")}
          >
            <Download className="h-4 w-4 mr-1" />
            Xuất Excel
          </Button>
        </div>
      </div>

      {pkg.description && (
        <p className="text-muted-foreground text-sm">{pkg.description}</p>
      )}

      {isLoading && <p className="text-muted-foreground">Đang tải...</p>}

      {detail && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            <div className="border rounded-md overflow-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-10">
                      <input
                        type="checkbox"
                        checked={
                          detail.items.length > 0 &&
                          removeSelected.size === detail.items.length
                        }
                        onChange={() => {
                          if (removeSelected.size === detail.items.length) {
                            setRemoveSelected(new Set());
                          } else {
                            setRemoveSelected(new Set(detail.items.map((i) => i.id)));
                          }
                        }}
                        className="h-4 w-4 rounded border-gray-300"
                      />
                    </TableHead>
                    <TableHead className="w-12 text-center">STT</TableHead>
                    <TableHead className="w-28">Mã hiệu</TableHead>
                    <TableHead>Tên công việc</TableHead>
                    <TableHead className="w-16">ĐVT</TableHead>
                    <TableHead className="w-20 text-right">KL</TableHead>
                    <TableHead className="w-32 text-right">Thành tiền</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {detail.items.map((item, idx) => (
                    <TableRow key={item.id}>
                      <TableCell>
                        <input
                          type="checkbox"
                          checked={removeSelected.has(item.id)}
                          onChange={() => toggleRemove(item.id)}
                          className="h-4 w-4 rounded border-gray-300"
                        />
                      </TableCell>
                      <TableCell className="text-center">{idx + 1}</TableCell>
                      <TableCell className="font-mono text-xs">{item.mhdg}</TableCell>
                      <TableCell className="max-w-xs truncate">{item.tcv}</TableCell>
                      <TableCell>{item.dvt}</TableCell>
                      <TableCell className="text-right">{item.quantity}</TableCell>
                      <TableCell className="text-right font-medium">
                        {formatVND(item.thanh_tien)}
                      </TableCell>
                    </TableRow>
                  ))}
                  {detail.items.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                        Chưa có công việc nào trong gói thầu này
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </div>
          <div>
            <CostSummaryPanel cost={detail.cost_breakdown} />
          </div>
        </div>
      )}

      <AssignItemsDialog
        open={showAssign}
        onOpenChange={setShowAssign}
        unassignedItems={unassignedItems}
        onAssign={(ids) => assignMutation.mutate(ids)}
        isPending={assignMutation.isPending}
      />
    </div>
  );
}

export default function GoiThauPage() {
  const params = useParams();
  const projectId = Number(params.id);
  const queryClient = useQueryClient();

  const [showCreate, setShowCreate] = useState(false);
  const [selectedPkg, setSelectedPkg] = useState<BidPackageSummary | null>(null);
  const [newName, setNewName] = useState("");
  const [newType, setNewType] = useState("XD");
  const [newDesc, setNewDesc] = useState("");

  const { data: projectData } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => getProject(projectId),
    enabled: !isNaN(projectId),
  });

  const { data: packages, isLoading } = useQuery({
    queryKey: ["bid-packages", projectId],
    queryFn: () => getBidPackages(projectId),
    enabled: !isNaN(projectId),
  });

  const createMutation = useMutation({
    mutationFn: (data: { name: string; package_type: string; description?: string }) =>
      createBidPackage(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bid-packages", projectId] });
      setShowCreate(false);
      setNewName("");
      setNewType("XD");
      setNewDesc("");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (pkgId: number) => deleteBidPackage(projectId, pkgId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bid-packages", projectId] });
      if (selectedPkg) setSelectedPkg(null);
    },
  });

  const projectName = projectData?.project?.name || "...";

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    createMutation.mutate({
      name: newName.trim(),
      package_type: newType,
      description: newDesc.trim() || undefined,
    });
  };

  if (selectedPkg) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-2">
          <Link
            href={`/du-toan/${projectId}`}
            className="text-sm text-muted-foreground hover:underline"
          >
            <ArrowLeft className="inline h-4 w-4 mr-1" />
            Dự toán
          </Link>
          <span className="text-muted-foreground">/</span>
          <button
            className="text-sm text-muted-foreground hover:underline"
            onClick={() => setSelectedPkg(null)}
          >
            Gói thầu
          </button>
        </div>
        <PackageDetailView
          projectId={projectId}
          pkg={selectedPkg}
          onClose={() => setSelectedPkg(null)}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Link
            href={`/du-toan/${projectId}`}
            className="text-sm text-muted-foreground hover:underline"
          >
            <ArrowLeft className="inline h-4 w-4 mr-1" />
            Quay lại dự toán
          </Link>
        </div>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold">Gói thầu - {projectName}</h1>
            <p className="text-muted-foreground mt-1">
              Quản lý các gói thầu của dự án
            </p>
          </div>
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="h-4 w-4 mr-1" />
            Tạo gói thầu
          </Button>
        </div>
      </div>

      {isLoading && <p className="text-muted-foreground">Đang tải...</p>}

      {packages && packages.length === 0 && (
        <Card className="p-8 text-center text-muted-foreground">
          Chưa có gói thầu nào. Bấm &quot;Tạo gói thầu&quot; để bắt đầu.
        </Card>
      )}

      {packages && packages.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {packages.map((pkg) => (
            <Card
              key={pkg.id}
              className="p-4 cursor-pointer hover:bg-muted/30 transition-colors"
              onClick={() => setSelectedPkg(pkg)}
            >
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h3 className="font-semibold">{pkg.name}</h3>
                  <Badge variant="outline" className="mt-1">
                    {pkg.package_type}
                  </Badge>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-destructive hover:text-destructive"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirm("Xóa gói thầu này?")) {
                      deleteMutation.mutate(pkg.id);
                    }
                  }}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
              {pkg.description && (
                <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
                  {pkg.description}
                </p>
              )}
              <div className="text-sm space-y-1">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Công việc:</span>
                  <span className="font-medium">{pkg.item_count}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Tổng chi phí:</span>
                  <span className="font-medium">{formatVND(pkg.total_cost)}</span>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create dialog */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Tạo gói thầu mới</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-1 block">
                Tên gói thầu *
              </label>
              <Input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Ví dụ: Gói thầu xây dựng phần thô"
                autoFocus
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">
                Loại gói thầu
              </label>
              <Select value={newType} onValueChange={(v) => setNewType(v ?? "XD")}>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PACKAGE_TYPES.map((t) => (
                    <SelectItem key={t.value} value={t.value}>
                      {t.value} - {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Mô tả</label>
              <Textarea
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                placeholder="Mô tả gói thầu..."
                rows={3}
              />
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowCreate(false)}
              >
                Hủy
              </Button>
              <Button type="submit" disabled={!newName.trim() || createMutation.isPending}>
                {createMutation.isPending ? "Đang tạo..." : "Tạo gói thầu"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
