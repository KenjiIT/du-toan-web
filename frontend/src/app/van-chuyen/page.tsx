"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  getCvcVehicles,
  getCvcMaterials,
  getCvcRoadTypes,
  getCvcTerrainTypes,
  getCvcSlopeTypes,
  calculateCvc,
} from "@/lib/api";
import type { CvcCalculateResult } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export default function VanChuyenPage() {
  const [vatlieu, setVatlieu] = useState("");
  const [culyKm, setCulyKm] = useState("5");
  const [vehicleId, setVehicleId] = useState<string>("");
  const [loaiduongId, setLoaiduongId] = useState("3");
  const [diahinhId, setDiahinhId] = useState("1");
  const [dodocId, setDodocId] = useState("1");
  const [result, setResult] = useState<CvcCalculateResult | null>(null);

  const { data: vehicles } = useQuery({
    queryKey: ["cvc-vehicles"],
    queryFn: getCvcVehicles,
  });

  const { data: materials } = useQuery({
    queryKey: ["cvc-materials"],
    queryFn: getCvcMaterials,
  });

  const { data: roadTypes } = useQuery({
    queryKey: ["cvc-road-types"],
    queryFn: getCvcRoadTypes,
  });

  const { data: terrainTypes } = useQuery({
    queryKey: ["cvc-terrain-types"],
    queryFn: getCvcTerrainTypes,
  });

  const { data: slopeTypes } = useQuery({
    queryKey: ["cvc-slope-types"],
    queryFn: getCvcSlopeTypes,
  });

  const calcMutation = useMutation({
    mutationFn: calculateCvc,
    onSuccess: (data) => setResult(data),
  });

  if (materials && materials.length > 0 && !vatlieu) {
    setVatlieu(materials[0].vatlieu);
  }

  const handleCalculate = () => {
    const km = parseFloat(culyKm);
    if (!vatlieu || isNaN(km) || km <= 0) return;
    calcMutation.mutate({
      vatlieu,
      culy_km: km,
      vehicle_id: vehicleId || undefined,
      loaiduong_id: loaiduongId,
      diahinh_id: diahinhId,
      dodoc_id: dodocId,
    });
  };

  const formatNum = (n: number, d = 4) =>
    new Intl.NumberFormat("vi-VN", {
      minimumFractionDigits: d,
      maximumFractionDigits: d,
    }).format(n);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Chi phí vận chuyển (CVC)</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Thông số tính toán</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium mb-1 block">
                Nhóm vật liệu
              </label>
              <select
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                value={vatlieu}
                onChange={(e) => setVatlieu(e.target.value)}
              >
                <option value="">-- Chọn vật liệu --</option>
                {materials?.map((m) => (
                  <option key={m.vatlieu} value={m.vatlieu}>
                    {m.vatlieu}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-sm font-medium mb-1 block">
                Cự ly (km)
              </label>
              <Input
                type="number"
                step="0.1"
                min="0"
                value={culyKm}
                onChange={(e) => setCulyKm(e.target.value)}
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-1 block">
                Phương tiện
              </label>
              <select
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                value={vehicleId}
                onChange={(e) => setVehicleId(e.target.value)}
              >
                <option value="">Tự động chọn</option>
                {vehicles?.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.loaioto} ({v.mamay})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-sm font-medium mb-1 block">
                Loại đường
              </label>
              <select
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                value={loaiduongId}
                onChange={(e) => setLoaiduongId(e.target.value)}
              >
                {roadTypes?.map((r) => (
                  <option key={r.id} value={r.id}>
                    Loại {r.loaiduong} (HS: {r.heso})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-sm font-medium mb-1 block">
                Địa hình
              </label>
              <select
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                value={diahinhId}
                onChange={(e) => setDiahinhId(e.target.value)}
              >
                {terrainTypes?.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.diahinh} (HS: {t.heso})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-sm font-medium mb-1 block">
                Độ dốc
              </label>
              <select
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                value={dodocId}
                onChange={(e) => setDodocId(e.target.value)}
              >
                {slopeTypes?.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.dodoc} (HS: {s.heso})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-4">
            <Button
              onClick={handleCalculate}
              disabled={calcMutation.isPending || !vatlieu}
            >
              {calcMutation.isPending ? "Đang tính..." : "Tính chi phí"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {calcMutation.isError && (
        <div className="text-red-600 text-sm">
          Lỗi: {(calcMutation.error as Error).message}
        </div>
      )}

      {result && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Kết quả tính toán</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 text-sm mb-4">
                <div>
                  <span className="text-muted-foreground">Loại đường:</span>{" "}
                  {result.loaiduong}
                </div>
                <div>
                  <span className="text-muted-foreground">Địa hình:</span>{" "}
                  {result.diahinh}
                </div>
                <div>
                  <span className="text-muted-foreground">Độ dốc:</span>{" "}
                  {result.dodoc}
                </div>
              </div>

              {result.machine && (
                <div className="mb-6">
                  <h3 className="font-semibold mb-2">
                    Vận chuyển cơ giới
                  </h3>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Vật liệu</TableHead>
                        <TableHead>Phương tiện</TableHead>
                        <TableHead>Cự ly</TableHead>
                        <TableHead className="text-right">
                          Hao phí gốc
                        </TableHead>
                        <TableHead className="text-right">Đơn vị</TableHead>
                        <TableHead className="text-right">HS Đường</TableHead>
                        <TableHead className="text-right">
                          HS Địa hình
                        </TableHead>
                        <TableHead className="text-right">HS Độ dốc</TableHead>
                        <TableHead className="text-right">
                          Hao phí điều chỉnh
                        </TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <TableRow>
                        <TableCell>{result.machine.vatlieu}</TableCell>
                        <TableCell>
                          {result.machine.loaioto || result.machine.phuongtien}
                        </TableCell>
                        <TableCell>{result.machine.culy}</TableCell>
                        <TableCell className="text-right">
                          {formatNum(result.machine.haophi)}
                        </TableCell>
                        <TableCell className="text-right">
                          {result.machine.donvi}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatNum(result.machine.road_coeff, 2)}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatNum(result.machine.terrain_coeff, 2)}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatNum(result.machine.slope_coeff, 2)}
                        </TableCell>
                        <TableCell className="text-right font-semibold">
                          {formatNum(result.machine.adjusted_haophi)}
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </div>
              )}

              {result.manual && (
                <div>
                  <h3 className="font-semibold mb-2">
                    Vận chuyển thủ công
                  </h3>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Nhóm VL</TableHead>
                        <TableHead className="text-right">Cự ly (m)</TableHead>
                        <TableHead className="text-right">
                          HP 10m KĐ
                        </TableHead>
                        <TableHead className="text-right">
                          HP 10m tiếp
                        </TableHead>
                        <TableHead className="text-right">Tổng HP</TableHead>
                        <TableHead className="text-right">Đơn vị</TableHead>
                        <TableHead className="text-right">Bốc lên</TableHead>
                        <TableHead className="text-right">
                          Bốc xuống
                        </TableHead>
                        <TableHead className="text-right">
                          HP điều chỉnh
                        </TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <TableRow>
                        <TableCell>{result.manual.nhomvatlieu}</TableCell>
                        <TableCell className="text-right">
                          {formatNum(result.manual.culy_m, 0)}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatNum(result.manual.haophi_base)}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatNum(result.manual.haophi_extra)}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatNum(result.manual.haophi_total)}
                        </TableCell>
                        <TableCell className="text-right">
                          {result.manual.donvi}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatNum(result.manual.boclen)}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatNum(result.manual.bocxuong)}
                        </TableCell>
                        <TableCell className="text-right font-semibold">
                          {formatNum(result.manual.adjusted_haophi)}
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </div>
              )}

              {!result.machine && !result.manual && (
                <p className="text-muted-foreground">
                  Không tìm thấy định mức vận chuyển cho thông số này.
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
