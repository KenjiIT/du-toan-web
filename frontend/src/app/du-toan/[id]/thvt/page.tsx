"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { getProject, getThvt, getExportThvtExcelUrl } from "@/lib/api";
import type { ThvtResource } from "@/lib/types";
import { formatVND, formatNumber } from "@/lib/formatters";
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

type TabKey = "vat_lieu" | "nhan_cong" | "may_thi_cong";

const TAB_CONFIG: { key: TabKey; label: string; totalKey: "total_vl" | "total_nc" | "total_mtc" }[] = [
  { key: "vat_lieu", label: "Vật liệu", totalKey: "total_vl" },
  { key: "nhan_cong", label: "Nhân công", totalKey: "total_nc" },
  { key: "may_thi_cong", label: "Máy thi công", totalKey: "total_mtc" },
];

function ResourceTable({
  resources,
  total,
  filter,
}: {
  resources: ThvtResource[];
  total: number;
  filter: string;
}) {
  const filtered = filter
    ? resources.filter(
        (r) =>
          r.msvt.toLowerCase().includes(filter.toLowerCase()) ||
          (r.tvt && r.tvt.toLowerCase().includes(filter.toLowerCase())),
      )
    : resources;

  return (
    <div className="border rounded-md overflow-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12 text-center">STT</TableHead>
            <TableHead className="w-28">Mã vật tư</TableHead>
            <TableHead>Tên vật tư</TableHead>
            <TableHead className="w-16">ĐVT</TableHead>
            <TableHead className="w-32 text-right">Tổng hao phí</TableHead>
            <TableHead className="w-32 text-right">Đơn giá</TableHead>
            <TableHead className="w-36 text-right">Thành tiền</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {filtered.map((r, idx) => (
            <TableRow key={`${r.msvt}-${idx}`}>
              <TableCell className="text-center">{idx + 1}</TableCell>
              <TableCell className="font-mono text-xs">{r.msvt}</TableCell>
              <TableCell className="max-w-md truncate">{r.tvt}</TableCell>
              <TableCell>{r.dvt}</TableCell>
              <TableCell className="text-right">
                {formatNumber(r.total_hao_phi, 4)}
              </TableCell>
              <TableCell className="text-right">{formatVND(r.gia)}</TableCell>
              <TableCell className="text-right font-medium">
                {formatVND(r.thanh_tien)}
              </TableCell>
            </TableRow>
          ))}
          {filtered.length === 0 && (
            <TableRow>
              <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                {filter ? "Không tìm thấy vật tư phù hợp" : "Không có dữ liệu"}
              </TableCell>
            </TableRow>
          )}
          {filtered.length > 0 && (
            <TableRow className="bg-muted/30 font-bold">
              <TableCell colSpan={6} className="text-center">
                TỔNG CỘNG ({filtered.length} mục)
              </TableCell>
              <TableCell className="text-right">
                {formatVND(
                  filter
                    ? filtered.reduce((s, r) => s + r.thanh_tien, 0)
                    : total,
                )}
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}

export default function ThvtPage() {
  const params = useParams();
  const projectId = Number(params.id);
  const [activeTab, setActiveTab] = useState<TabKey>("vat_lieu");
  const [filter, setFilter] = useState("");

  const { data: projectData } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => getProject(projectId),
    enabled: !isNaN(projectId),
  });

  const { data: thvt, isLoading } = useQuery({
    queryKey: ["thvt", projectId],
    queryFn: () => getThvt(projectId),
    enabled: !isNaN(projectId),
  });

  const projectName = projectData?.project?.name || "...";

  return (
    <div className="space-y-6">
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
            <h1 className="text-2xl font-bold">
              Tổng hợp vật tư - {projectName}
            </h1>
            {thvt && (
              <p className="text-muted-foreground mt-1">
                {thvt.item_count} công việc | {thvt.resource_count.vl} vật liệu,{" "}
                {thvt.resource_count.nc} nhân công, {thvt.resource_count.mtc} máy
              </p>
            )}
          </div>
          <Button
            variant="outline"
            onClick={() =>
              window.open(getExportThvtExcelUrl(projectId), "_blank")
            }
          >
            Xuất Excel THVT
          </Button>
        </div>
      </div>

      {isLoading && (
        <p className="text-muted-foreground">Đang tính tổng hợp vật tư...</p>
      )}

      {thvt && (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-4 gap-4">
            {TAB_CONFIG.map((tab) => (
              <Card
                key={tab.key}
                className={`p-4 cursor-pointer transition-colors ${
                  activeTab === tab.key
                    ? "ring-2 ring-primary"
                    : "hover:bg-muted/30"
                }`}
                onClick={() => setActiveTab(tab.key)}
              >
                <div className="text-sm text-muted-foreground">{tab.label}</div>
                <div className="text-xl font-bold mt-1">
                  {formatVND(thvt[tab.totalKey])}
                </div>
                <div className="text-xs text-muted-foreground">
                  {thvt.resource_count[tab.key === "vat_lieu" ? "vl" : tab.key === "nhan_cong" ? "nc" : "mtc"]} mục
                </div>
              </Card>
            ))}
            <Card className="p-4">
              <div className="text-sm text-muted-foreground">Tổng cộng</div>
              <div className="text-xl font-bold mt-1 text-primary">
                {formatVND(thvt.total)}
              </div>
              <div className="text-xs text-muted-foreground">
                {thvt.resource_count.vl + thvt.resource_count.nc + thvt.resource_count.mtc} mục
              </div>
            </Card>
          </div>

          {/* Tab buttons */}
          <div className="flex gap-2 items-center">
            {TAB_CONFIG.map((tab) => (
              <Button
                key={tab.key}
                variant={activeTab === tab.key ? "default" : "outline"}
                size="sm"
                onClick={() => setActiveTab(tab.key)}
              >
                {tab.label} ({thvt[tab.key].length})
              </Button>
            ))}
            <div className="flex-1" />
            <Input
              placeholder="Tìm mã hoặc tên vật tư..."
              className="w-64"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            />
          </div>

          {/* Active table */}
          {TAB_CONFIG.map((tab) =>
            activeTab === tab.key ? (
              <ResourceTable
                key={tab.key}
                resources={thvt[tab.key]}
                total={thvt[tab.totalKey]}
                filter={filter}
              />
            ) : null,
          )}
        </>
      )}
    </div>
  );
}
