"use client";

import { useQuery } from "@tanstack/react-query";
import { getPhanTich } from "@/lib/api";
import { formatVND, formatNumber } from "@/lib/formatters";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface Props {
  mhdg: string;
  source?: string;
}

const TYPE_STYLES: Record<string, string> = {
  VL: "bg-blue-100 text-blue-800",
  NC: "bg-green-100 text-green-800",
  MTC: "bg-orange-100 text-orange-800",
};

export function ItemDetail({ mhdg, source }: Props) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["phan-tich", mhdg, source],
    queryFn: () => getPhanTich(mhdg, source || "norm"),
  });

  if (isLoading)
    return (
      <div className="p-4 text-sm text-muted-foreground">Đang tải...</div>
    );
  if (error)
    return <div className="p-4 text-sm text-destructive">Lỗi tải dữ liệu</div>;
  if (!data) return null;

  return (
    <div className="p-4 bg-muted/30 border-t">
      <div className="text-sm font-medium mb-2">
        Phân tích đơn giá &mdash; {data.mhdg}: {data.tcv}
      </div>
      {data.phu_luc_vua && (
        <div className="text-xs text-muted-foreground mb-2 bg-blue-50 p-2 rounded">
          <strong>Phụ lục vữa:</strong> {data.phu_luc_vua.btm} &mdash;{" "}
          {data.phu_luc_vua.tg} = {formatVND(data.phu_luc_vua.total_cost)}/m³
          <div className="mt-1 ml-4 space-y-0.5">
            {data.phu_luc_vua.components.map((c, i) => (
              <div key={i} className="flex gap-2">
                <span className="font-mono w-20">{c.msvt}</span>
                <span className="flex-1">{c.tvt}</span>
                <span>{formatNumber(c.hao_phi, 3)}</span>
                <span className="text-muted-foreground">×</span>
                <span className="w-24 text-right">{formatVND(c.gia)}</span>
                <span className="text-muted-foreground">=</span>
                <span className="w-24 text-right font-medium">
                  {formatVND(c.thanh_tien)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-16">Loại</TableHead>
            <TableHead className="w-28">Mã VT</TableHead>
            <TableHead>Tên vật tư</TableHead>
            <TableHead className="w-16">ĐVT</TableHead>
            <TableHead className="w-24 text-right">Hao phí</TableHead>
            <TableHead className="w-28 text-right">Đơn giá</TableHead>
            <TableHead className="w-28 text-right">Thành tiền</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.details.map((d, i) => (
            <TableRow key={i}>
              <TableCell>
                <Badge className={TYPE_STYLES[d.type] || ""}>
                  {d.type}
                </Badge>
              </TableCell>
              <TableCell className="font-mono text-xs">{d.msvt}</TableCell>
              <TableCell>{d.tvt}</TableCell>
              <TableCell>{d.dvt}</TableCell>
              <TableCell className="text-right">
                {formatNumber(d.hao_phi, 4)}
              </TableCell>
              <TableCell className="text-right">{formatVND(d.gia)}</TableCell>
              <TableCell className="text-right font-medium">
                {formatVND(d.thanh_tien)}
              </TableCell>
            </TableRow>
          ))}
          {data.details.length === 0 && (
            <TableRow>
              <TableCell colSpan={7} className="text-center py-4 text-muted-foreground">
                Không có dữ liệu định mức
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
      <div className="flex gap-6 mt-3 text-sm flex-wrap">
        <span>
          <strong className="text-blue-700">VLC:</strong> {formatVND(data.vlc)}
        </span>
        <span>
          <strong className="text-green-700">NC:</strong> {formatVND(data.nc)}
        </span>
        <span>
          <strong className="text-orange-700">MTC:</strong> {formatVND(data.mtc)}
        </span>
        <span className="font-bold">Tổng: {formatVND(data.total)}</span>
      </div>
    </div>
  );
}
