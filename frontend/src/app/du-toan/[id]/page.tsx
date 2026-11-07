"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import {
  getProject,
  deleteProject,
  updateProjectItem,
  deleteProjectItem,
  getExportExcelUrl,
  getExportPdfUrl,
  getExportThvtExcelUrl,
  getExportPhanTichDonGiaUrl,
  getExportNhanCongUrl,
  getExportCaMayUrl,
  getExportFullReportUrl,
  getExportTmdtExcelUrl,
  getExportMau01Url,
  getExportMau02Url,
  getExportMau03Url,
  copyProject,
  getExportJsonUrl,
} from "@/lib/api";
import { ChevronDown } from "lucide-react";
import type { ProjectItem } from "@/lib/types";
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
import { AddItemDialog } from "@/components/du-toan/AddItemDialog";
import { CostSummaryCard } from "@/components/du-toan/CostSummary";
import { PriceAdjustment } from "@/components/du-toan/PriceAdjustment";
import { SettingsPanel } from "@/components/du-toan/SettingsPanel";

const CHAPTER_NAMES: Record<string, string> = {
  "AA": "Phát rừng, phát hoang",
  "AB": "Công tác đất",
  "AC": "Công tác đóng cọc",
  "AD": "Công tác làm đường",
  "AE": "Công tác xây",
  "AF": "Công tác bê tông",
  "AG": "Bê tông đúc sẵn",
  "AH": "Công tác gỗ",
  "AI": "Kết cấu thép",
  "AK": "Mái, trần, chống thấm",
  "AL": "Công tác dưới nước",
  "AM": "Bốc xếp, vận chuyển",
  "AN": "Tro xỉ",
  "BA": "Lắp đặt điện",
  "BB": "Lắp đặt ống",
  "BC": "Bảo ôn, cách nhiệt",
  "BD": "Khoan ngầm",
  "SA": "Phá dỡ",
  "SB": "Sửa chữa xây",
  "SE": "Sửa chữa đường",
  "SF": "Sửa chữa mái dốc",
  "TT": "Công tác tạm",
  "CA": "Khảo sát địa hình",
  "CB": "Khảo sát địa chất",
  "CC": "Khảo sát thủy văn",
};

function groupByChapter(
  items: ProjectItem[],
): { chapter: string; name: string; items: ProjectItem[]; subtotal: number }[] {
  const groups: Record<string, ProjectItem[]> = {};
  for (const item of items) {
    const ch = item.mhdg.substring(0, 2).toUpperCase();
    if (!groups[ch]) groups[ch] = [];
    groups[ch].push(item);
  }
  return Object.entries(groups)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([ch, chItems]) => ({
      chapter: ch,
      name: CHAPTER_NAMES[ch] || ch,
      items: chItems,
      subtotal: chItems.reduce((sum, i) => sum + i.thanh_tien, 0),
    }));
}

export default function ProjectPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = Number(params.id);
  const queryClient = useQueryClient();
  const [showAdd, setShowAdd] = useState(false);
  const [showReportMenu, setShowReportMenu] = useState(false);
  const [editingQty, setEditingQty] = useState<number | null>(null);
  const [qtyValue, setQtyValue] = useState("");
  const [editingOverride, setEditingOverride] = useState<{
    itemId: number;
    field: "override_vlc" | "override_nc" | "override_mtc";
  } | null>(null);
  const [overrideValue, setOverrideValue] = useState("");
  const [collapsedSections, setCollapsedSections] = useState<Set<number>>(
    new Set(),
  );

  const { data, isLoading } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => getProject(projectId),
    enabled: !isNaN(projectId),
  });

  const deleteItemMutation = useMutation({
    mutationFn: (itemId: number) => deleteProjectItem(projectId, itemId),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["project", projectId] }),
  });

  const updateItemMutation = useMutation({
    mutationFn: ({ itemId, quantity }: { itemId: number; quantity: number }) =>
      updateProjectItem(projectId, itemId, { quantity }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      setEditingQty(null);
    },
  });

  const overrideMutation = useMutation({
    mutationFn: ({
      itemId,
      field,
      value,
    }: {
      itemId: number;
      field: "override_vlc" | "override_nc" | "override_mtc";
      value: number | null;
    }) => updateProjectItem(projectId, itemId, { [field]: value }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      setEditingOverride(null);
    },
  });

  const deleteProjectMutation = useMutation({
    mutationFn: () => deleteProject(projectId),
    onSuccess: () => router.push("/du-toan"),
  });

  const copyMutation = useMutation({
    mutationFn: () => copyProject(projectId),
    onSuccess: (newProject) => {
      router.push(`/du-toan/${newProject.id}`);
    },
  });

  const toggleSection = (id: number) => {
    setCollapsedSections((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  if (isLoading) {
    return <p className="text-muted-foreground">Đang tải dự toán...</p>;
  }

  if (!data) {
    return <p className="text-red-600">Không tìm thấy dự toán</p>;
  }

  const { project, items, sections, summary } = data;
  const hasSections = sections && sections.length > 0;

  function renderItemRow(item: ProjectItem, idx: number) {
    return (
      <TableRow key={item.id}>
        <TableCell className="text-center">{idx + 1}</TableCell>
        <TableCell className="font-mono text-xs">{item.mhdg}</TableCell>
        <TableCell className="max-w-xs truncate">{item.tcv}</TableCell>
        <TableCell>{item.dvt}</TableCell>
        <TableCell className="text-right">
          {editingQty === item.id ? (
            <Input
              type="number"
              step="any"
              className="w-20 h-7 text-right text-sm"
              value={qtyValue}
              autoFocus
              onChange={(e) => setQtyValue(e.target.value)}
              onBlur={() => {
                const v = parseFloat(qtyValue);
                if (!isNaN(v) && v !== item.quantity) {
                  updateItemMutation.mutate({
                    itemId: item.id,
                    quantity: v,
                  });
                } else {
                  setEditingQty(null);
                }
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  (e.target as HTMLInputElement).blur();
                }
                if (e.key === "Escape") setEditingQty(null);
              }}
            />
          ) : (
            <span
              className="cursor-pointer hover:underline"
              onClick={() => {
                setEditingQty(item.id);
                setQtyValue(String(item.quantity));
              }}
            >
              {item.quantity}
            </span>
          )}
        </TableCell>
        {(
          [
            {
              field: "override_vlc" as const,
              base: item.vlc,
              override: item.override_vlc,
              tt: item.thanh_tien_vlc,
              color: "text-blue-700",
            },
            {
              field: "override_nc" as const,
              base: item.nc,
              override: item.override_nc,
              tt: item.thanh_tien_nc,
              color: "text-green-700",
            },
            {
              field: "override_mtc" as const,
              base: item.mtc,
              override: item.override_mtc,
              tt: item.thanh_tien_mtc,
              color: "text-orange-700",
            },
          ] as const
        ).map((col) => (
          <TableCell
            key={col.field}
            className={`text-right ${col.color}`}
          >
            {editingOverride?.itemId === item.id &&
            editingOverride?.field === col.field ? (
              <Input
                type="number"
                step="any"
                className="w-24 h-7 text-right text-sm"
                value={overrideValue}
                autoFocus
                onChange={(e) => setOverrideValue(e.target.value)}
                onBlur={() => {
                  if (overrideValue === "") {
                    overrideMutation.mutate({
                      itemId: item.id,
                      field: col.field,
                      value: null,
                    });
                  } else {
                    const v = parseFloat(overrideValue);
                    if (!isNaN(v)) {
                      overrideMutation.mutate({
                        itemId: item.id,
                        field: col.field,
                        value: v,
                      });
                    } else {
                      setEditingOverride(null);
                    }
                  }
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter")
                    (e.target as HTMLInputElement).blur();
                  if (e.key === "Escape") setEditingOverride(null);
                }}
              />
            ) : (
              <span
                className="cursor-pointer hover:underline inline-flex items-center gap-1"
                title={
                  col.override !== null && col.override !== undefined
                    ? `Giá gốc: ${formatVND(col.base)} - Đang dùng giá thủ công. Xóa ô trống để trả về giá gốc.`
                    : "Bấm để nhập giá thủ công"
                }
                onClick={() => {
                  setEditingOverride({
                    itemId: item.id,
                    field: col.field,
                  });
                  setOverrideValue(
                    col.override !== null && col.override !== undefined
                      ? String(col.override)
                      : String(col.base),
                  );
                }}
              >
                {formatVND(col.tt)}
                {col.override !== null && col.override !== undefined && (
                  <span
                    className="inline-block w-2 h-2 rounded-full bg-amber-500 shrink-0"
                    title="Giá thủ công"
                  />
                )}
              </span>
            )}
          </TableCell>
        ))}
        <TableCell className="text-right font-medium">
          {formatVND(item.thanh_tien)}
        </TableCell>
        <TableCell>
          <Button
            variant="ghost"
            size="sm"
            className="text-red-500 h-7 px-2"
            onClick={() => {
              if (confirm("Xóa công việc này?"))
                deleteItemMutation.mutate(item.id);
            }}
          >
            Xóa
          </Button>
        </TableCell>
      </TableRow>
    );
  }

  function renderTableHeader() {
    return (
      <TableHeader>
        <TableRow>
          <TableHead className="w-12">STT</TableHead>
          <TableHead className="w-28">Mã</TableHead>
          <TableHead>Tên công việc</TableHead>
          <TableHead className="w-16">ĐVT</TableHead>
          <TableHead className="w-24 text-right">Khối lượng</TableHead>
          <TableHead className="w-28 text-right">VLC</TableHead>
          <TableHead className="w-28 text-right">NC</TableHead>
          <TableHead className="w-28 text-right">MTC</TableHead>
          <TableHead className="w-32 text-right">Thành tiền</TableHead>
          <TableHead className="w-20"></TableHead>
        </TableRow>
      </TableHeader>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Link
            href="/du-toan"
            className="text-sm text-muted-foreground hover:underline"
          >
            ← Danh sách dự toán
          </Link>
        </div>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold">{project.name}</h1>
            {project.description && (
              <p className="text-muted-foreground mt-1">
                {project.description}
              </p>
            )}
            <div className="flex gap-2 mt-2">
              {project.settings && (
                <>
                  <Badge variant="outline">
                    {project.settings.regulation_code}
                  </Badge>
                  <Badge variant="outline">{project.settings.source}</Badge>
                </>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setShowAdd(true)}>+ Thêm công việc</Button>
            <Link href={`/du-toan/${projectId}/thvt`}>
              <Button variant="outline">Tổng hợp vật tư</Button>
            </Link>
            <Link href={`/du-toan/${projectId}/tmdt`}>
              <Button variant="outline">Tổng mức đầu tư</Button>
            </Link>
            <Link href={`/du-toan/${projectId}/goi-thau`}>
              <Button variant="outline">Gói thầu</Button>
            </Link>
            <Link href={`/du-toan/${projectId}/quyet-toan`}>
              <Button variant="outline">Quyết toán</Button>
            </Link>
            <div className="relative">
              <Button
                variant="outline"
                onClick={() => setShowReportMenu(!showReportMenu)}
                onBlur={() => setTimeout(() => setShowReportMenu(false), 200)}
              >
                Báo cáo <ChevronDown className="ml-1 h-4 w-4" />
              </Button>
              {showReportMenu && (
                <div className="absolute right-0 top-full mt-1 z-50 min-w-[280px] bg-popover border rounded-md shadow-md py-1">
                  <div className="px-3 py-1.5 text-xs font-semibold text-muted-foreground">
                    Xuất báo cáo
                  </div>
                  <button
                    className="w-full text-left px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
                    onMouseDown={() => window.open(getExportExcelUrl(projectId), "_blank")}
                  >
                    Bảng dự toán (Excel)
                  </button>
                  <button
                    className="w-full text-left px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
                    onMouseDown={() => window.open(getExportPdfUrl(projectId), "_blank")}
                  >
                    Bảng dự toán (PDF)
                  </button>
                  <div className="h-px bg-border mx-2 my-1" />
                  <button
                    className="w-full text-left px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
                    onMouseDown={() => window.open(getExportPhanTichDonGiaUrl(projectId), "_blank")}
                  >
                    Phân tích đơn giá chi tiết
                  </button>
                  <div className="h-px bg-border mx-2 my-1" />
                  <div className="px-3 py-1.5 text-xs font-semibold text-muted-foreground">
                    Tổng hợp
                  </div>
                  <button
                    className="w-full text-left px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
                    onMouseDown={() => window.open(getExportThvtExcelUrl(projectId), "_blank")}
                  >
                    Tổng hợp vật tư (Excel)
                  </button>
                  <button
                    className="w-full text-left px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
                    onMouseDown={() => window.open(getExportNhanCongUrl(projectId), "_blank")}
                  >
                    Tổng hợp nhân công
                  </button>
                  <button
                    className="w-full text-left px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
                    onMouseDown={() => window.open(getExportCaMayUrl(projectId), "_blank")}
                  >
                    Tổng hợp ca máy
                  </button>
                  <div className="h-px bg-border mx-2 my-1" />
                  <button
                    className="w-full text-left px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
                    onMouseDown={() => window.open(getExportTmdtExcelUrl(projectId), "_blank")}
                  >
                    Tổng mức đầu tư (Excel)
                  </button>
                  <div className="h-px bg-border mx-2 my-1" />
                  <button
                    className="w-full text-left px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground"
                    onMouseDown={() => window.open(getExportFullReportUrl(projectId), "_blank")}
                  >
                    Báo cáo tổng hợp (tất cả)
                  </button>
                  <div className="h-px bg-border mx-2 my-1" />
                  <div className="px-3 py-1.5 text-xs font-semibold text-muted-foreground">
                    Biểu mẫu chuẩn
                  </div>
                  <button
                    className="w-full text-left px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
                    onMouseDown={() => window.open(getExportMau01Url(projectId), "_blank")}
                  >
                    Mẫu 01 - TH dự toán XD
                  </button>
                  <button
                    className="w-full text-left px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
                    onMouseDown={() => window.open(getExportMau02Url(projectId), "_blank")}
                  >
                    Mẫu 02 - Chi phí XD
                  </button>
                  <button
                    className="w-full text-left px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
                    onMouseDown={() => window.open(getExportMau03Url(projectId), "_blank")}
                  >
                    Mẫu 03 - KL đơn giá
                  </button>
                </div>
              )}
            </div>
            <Button
              variant="outline"
              onClick={() => copyMutation.mutate()}
              disabled={copyMutation.isPending}
            >
              {copyMutation.isPending ? "Đang sao chép..." : "Sao chép"}
            </Button>
            <Button
              variant="outline"
              onClick={() =>
                window.open(getExportJsonUrl(projectId), "_blank")
              }
            >
              Xuất JSON
            </Button>
            <Button
              variant="outline"
              className="text-red-600"
              onClick={() => {
                if (confirm("Xóa dự toán này?"))
                  deleteProjectMutation.mutate();
              }}
            >
              Xóa
            </Button>
          </div>
        </div>
      </div>

      {project.settings && (
        <SettingsPanel projectId={projectId} settings={project.settings} estimateType={project.estimate_type || "new"} />
      )}

      {hasSections ? (
        <div className="space-y-4">
          {sections.map((section) => {
            const chapters = groupByChapter(section.items);
            const isCollapsed = collapsedSections.has(section.id);
            return (
              <Card key={section.id} className="overflow-hidden">
                <div
                  className="flex items-center justify-between px-4 py-3 bg-muted/30 cursor-pointer select-none"
                  onClick={() => toggleSection(section.id)}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-sm">
                      {isCollapsed ? "▶" : "▼"}
                    </span>
                    <div>
                      <h3 className="font-semibold">{section.name}</h3>
                      <span className="text-xs text-muted-foreground">
                        {section.items.length} công việc
                      </span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold">
                      {formatVND(section.subtotal?.gxd ?? 0)}
                    </div>
                    <div className="text-xs text-muted-foreground">GXD</div>
                  </div>
                </div>
                {!isCollapsed && (
                  <div>
                    {chapters.map((ch) => (
                      <div key={ch.chapter}>
                        <div className="flex items-center justify-between px-4 py-2 bg-muted/10 border-t">
                          <span className="text-sm font-medium">
                            Chương {ch.chapter}: {ch.name}
                          </span>
                          <span className="text-sm font-medium">
                            {formatVND(ch.subtotal)}
                          </span>
                        </div>
                        <div className="overflow-auto">
                          <Table>
                            {renderTableHeader()}
                            <TableBody>
                              {ch.items.map((item, idx) =>
                                renderItemRow(item, idx),
                              )}
                            </TableBody>
                          </Table>
                        </div>
                      </div>
                    ))}
                    {section.subtotal && (
                      <div className="px-4 py-3 border-t bg-muted/20">
                        <div className="grid grid-cols-4 gap-4 text-sm">
                          <div>
                            <span className="text-muted-foreground">T:</span>{" "}
                            <span className="font-medium">
                              {formatVND(section.subtotal.t)}
                            </span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">
                              C ({section.subtotal.chi_phi_chung_pct}%):
                            </span>{" "}
                            <span className="font-medium">
                              {formatVND(section.subtotal.c)}
                            </span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">G:</span>{" "}
                            <span className="font-medium">
                              {formatVND(section.subtotal.g)}
                            </span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">
                              GXD:
                            </span>{" "}
                            <span className="font-semibold">
                              {formatVND(section.subtotal.gxd)}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      ) : (
        <div className="border rounded-md overflow-auto">
          <Table>
            {renderTableHeader()}
            <TableBody>
              {items.map((item, idx) => renderItemRow(item, idx))}
              {items.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={10}
                    className="text-center py-8 text-muted-foreground"
                  >
                    Chưa có công việc nào. Bấm &quot;Thêm công việc&quot; để bắt
                    đầu.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      )}

      {items.length > 0 && (
        <PriceAdjustment projectId={projectId} />
      )}

      {items.length > 0 && (
        <CostSummaryCard summary={summary} sections={sections} />
      )}

      <AddItemDialog
        projectId={projectId}
        open={showAdd}
        onOpenChange={setShowAdd}
      />
    </div>
  );
}
