"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  getCoefficientRegions,
  getLaborPrices,
  getMachinePrices,
} from "@/lib/api";
import { formatVND } from "@/lib/formatters";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type TabType = "labor" | "machine";
const PAGE_SIZE = 20;

function Pagination({
  page,
  total,
  limit,
  onPageChange,
}: {
  page: number;
  total: number;
  limit: number;
  onPageChange: (p: number) => void;
}) {
  const totalPages = Math.ceil(total / limit);
  if (totalPages <= 1) return null;
  return (
    <div className="flex items-center justify-between pt-3">
      <span className="text-sm text-muted-foreground">
        {total} kết quả — Trang {page}/{totalPages}
      </span>
      <div className="flex gap-1">
        <Button
          variant="outline"
          size="sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          Trước
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          Sau
        </Button>
      </div>
    </div>
  );
}

export default function CoefficientsPage() {
  const [selectedRegion, setSelectedRegion] = useState<string>("");
  const [activeTab, setActiveTab] = useState<TabType>("labor");
  const [selectedZone, setSelectedZone] = useState<string>("I");
  const [laborSearch, setLaborSearch] = useState("");
  const [machineSearch, setMachineSearch] = useState("");
  const [laborPage, setLaborPage] = useState(1);
  const [machinePage, setMachinePage] = useState(1);

  const { data: regions, isLoading: regionsLoading } = useQuery({
    queryKey: ["coefficient-regions"],
    queryFn: getCoefficientRegions,
  });

  const currentRegionInfo = regions?.find((r) => r.region === selectedRegion);

  const {
    data: laborData,
    isLoading: laborLoading,
    error: laborError,
  } = useQuery({
    queryKey: ["labor-prices", selectedRegion, laborSearch, laborPage],
    queryFn: () =>
      getLaborPrices(selectedRegion, {
        q: laborSearch || undefined,
        page: laborPage,
        limit: PAGE_SIZE,
      }),
    enabled: !!selectedRegion && activeTab === "labor",
  });

  const {
    data: machineData,
    isLoading: machineLoading,
    error: machineError,
  } = useQuery({
    queryKey: ["machine-prices", selectedRegion, selectedZone, machineSearch, machinePage],
    queryFn: () =>
      getMachinePrices(selectedRegion, selectedZone, {
        q: machineSearch || undefined,
        page: machinePage,
        limit: PAGE_SIZE,
      }),
    enabled: !!selectedRegion && activeTab === "machine",
  });

  const handleRegionChange = (v: string) => {
    setSelectedRegion(v);
    setLaborPage(1);
    setMachinePage(1);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">
        Hệ số điều chỉnh - Giá nhân công & ca máy
      </h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Chọn khu vực</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Select value={selectedRegion} onValueChange={(v) => handleRegionChange(v ?? "")}>
            <SelectTrigger className="max-w-md">
              <SelectValue
                placeholder={
                  regionsLoading ? "Đang tải..." : "Chọn khu vực..."
                }
              />
            </SelectTrigger>
            <SelectContent>
              {regions?.map((r) => (
                <SelectItem key={r.region} value={r.region}>
                  {r.region}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {currentRegionInfo && (
            <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
              <span>Quyết định:</span>
              {currentRegionInfo.decision_refs.map((ref) => (
                <Badge key={ref} variant="secondary">
                  {ref}
                </Badge>
              ))}
              {currentRegionInfo.zones.length > 0 && (
                <>
                  <span className="ml-2">Khu vực:</span>
                  {currentRegionInfo.zones.map((z) => (
                    <Badge key={z} variant="secondary">
                      {z}
                    </Badge>
                  ))}
                </>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {selectedRegion && (
        <>
          <div className="flex gap-2">
            <Button
              variant={activeTab === "labor" ? "default" : "outline"}
              onClick={() => setActiveTab("labor")}
            >
              Giá nhân công
            </Button>
            <Button
              variant={activeTab === "machine" ? "default" : "outline"}
              onClick={() => setActiveTab("machine")}
            >
              Giá ca máy
            </Button>
          </div>

          {activeTab === "labor" && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">
                  Bảng giá nhân công - {selectedRegion}
                  {laborData?.decision_ref && (
                    <span className="ml-2 text-sm font-normal text-muted-foreground">
                      ({laborData.decision_ref})
                    </span>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Input
                  placeholder="Tìm theo mã NC hoặc nhóm..."
                  value={laborSearch}
                  onChange={(e) => {
                    setLaborSearch(e.target.value);
                    setLaborPage(1);
                  }}
                  className="max-w-sm"
                />
                {laborLoading ? (
                  <div className="text-center py-8 text-muted-foreground">
                    Đang tải...
                  </div>
                ) : laborError ? (
                  <div className="text-center py-8 text-destructive">
                    Lỗi tải dữ liệu giá nhân công.
                  </div>
                ) : laborData && laborData.items.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    Không có dữ liệu giá nhân công cho khu vực này.
                  </div>
                ) : laborData ? (
                  <>
                    <div className="border rounded-md">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead className="w-[120px]">Mã NC</TableHead>
                            <TableHead>Nhóm</TableHead>
                            <TableHead className="w-[160px] text-right">
                              Khu vực I
                            </TableHead>
                            <TableHead className="w-[160px] text-right">
                              Khu vực II
                            </TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {laborData.items.map((item, idx) => (
                            <TableRow key={`${item.ma_nc}-${idx}`}>
                              <TableCell className="font-mono text-sm">
                                {item.ma_nc}
                              </TableCell>
                              <TableCell>{item.nhom}</TableCell>
                              <TableCell className="text-right">
                                {formatVND(item.khu_vuc_i)}
                              </TableCell>
                              <TableCell className="text-right">
                                {formatVND(item.khu_vuc_ii)}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                    <Pagination
                      page={laborData.page}
                      total={laborData.total}
                      limit={laborData.limit}
                      onPageChange={setLaborPage}
                    />
                  </>
                ) : null}
              </CardContent>
            </Card>
          )}

          {activeTab === "machine" && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">
                    Bảng giá ca máy - {selectedRegion}
                    {machineData?.decision_ref && (
                      <span className="ml-2 text-sm font-normal text-muted-foreground">
                        ({machineData.decision_ref})
                      </span>
                    )}
                  </CardTitle>
                  <Select
                    value={selectedZone}
                    onValueChange={(v) => {
                      setSelectedZone(v ?? "I");
                      setMachinePage(1);
                    }}
                  >
                    <SelectTrigger className="w-[140px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {(currentRegionInfo?.zones || ["I", "II"]).map((z) => (
                        <SelectItem key={z} value={z}>
                          Khu vực {z}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <Input
                  placeholder="Tìm theo mã hiệu hoặc tên máy..."
                  value={machineSearch}
                  onChange={(e) => {
                    setMachineSearch(e.target.value);
                    setMachinePage(1);
                  }}
                  className="max-w-sm"
                />
                {machineLoading ? (
                  <div className="text-center py-8 text-muted-foreground">
                    Đang tải...
                  </div>
                ) : machineError ? (
                  <div className="text-center py-8 text-destructive">
                    Lỗi tải dữ liệu giá ca máy.
                  </div>
                ) : machineData && machineData.items.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    Không có dữ liệu giá ca máy cho khu vực này.
                  </div>
                ) : machineData ? (
                  <>
                    <div className="border rounded-md overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead className="w-[100px]">Mã hiệu</TableHead>
                            <TableHead>Loại máy / TB</TableHead>
                            <TableHead className="w-[110px] text-right">
                              Giá ca máy
                            </TableHead>
                            <TableHead className="w-[110px] text-right">
                              CP khấu hao
                            </TableHead>
                            <TableHead className="w-[110px] text-right">
                              CP sửa chữa
                            </TableHead>
                            <TableHead className="w-[110px] text-right">
                              CP khác
                            </TableHead>
                            <TableHead className="w-[110px] text-right">
                              CP nhiên liệu
                            </TableHead>
                            <TableHead className="w-[110px] text-right">
                              CP tiền lương
                            </TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {machineData.items.map((item, idx) => (
                            <TableRow key={`${item.mh}-${idx}`}>
                              <TableCell className="font-mono text-sm">
                                {item.mh}
                              </TableCell>
                              <TableCell>{item.lm_tb || "-"}</TableCell>
                              <TableCell className="text-right">
                                {formatVND(item.gcm)}
                              </TableCell>
                              <TableCell className="text-right">
                                {formatVND(item.cpkh)}
                              </TableCell>
                              <TableCell className="text-right">
                                {formatVND(item.cpsc)}
                              </TableCell>
                              <TableCell className="text-right">
                                {formatVND(item.cpk)}
                              </TableCell>
                              <TableCell className="text-right">
                                {formatVND(item.cpnl)}
                              </TableCell>
                              <TableCell className="text-right">
                                {formatVND(item.cptl)}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                    <Pagination
                      page={machineData.page}
                      total={machineData.total}
                      limit={machineData.limit}
                      onPageChange={setMachinePage}
                    />
                  </>
                ) : null}
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
