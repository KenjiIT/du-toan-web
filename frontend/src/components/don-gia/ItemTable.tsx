"use client";

import { Fragment, useState } from "react";
import type { DonGia } from "@/lib/types";
import { formatVND } from "@/lib/formatters";
import { ItemDetail } from "./ItemDetail";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";

interface Props {
  items: DonGia[];
  total: number;
  page: number;
  limit: number;
  onPageChange: (page: number) => void;
  region?: string;
}

export function ItemTable({ items, total, page, limit, onPageChange, region }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const pages = Math.ceil(total / limit);
  const showPrices = !!region;

  return (
    <div>
      <div className="text-sm text-muted-foreground mb-2">
        Tìm thấy {total.toLocaleString("vi-VN")} công việc
      </div>
      <div className="border rounded-md overflow-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-28">Mã</TableHead>
              <TableHead>Tên công việc</TableHead>
              <TableHead className="w-16">ĐVT</TableHead>
              {showPrices && (
                <>
                  <TableHead className="w-28 text-right">VLC</TableHead>
                  <TableHead className="w-28 text-right">NC</TableHead>
                  <TableHead className="w-28 text-right">MTC</TableHead>
                </>
              )}
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((item) => (
              <Fragment key={item.mhdg}>
                <TableRow
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() =>
                    setExpanded(expanded === item.mhdg ? null : item.mhdg)
                  }
                >
                  <TableCell className="font-mono text-xs">
                    {item.mhdg}
                  </TableCell>
                  <TableCell className="max-w-md">{item.tcv}</TableCell>
                  <TableCell>{item.dvt}</TableCell>
                  {showPrices && (
                    <>
                      <TableCell className="text-right text-blue-700">
                        {formatVND(item.vlc)}
                      </TableCell>
                      <TableCell className="text-right text-green-700">
                        {formatVND(item.nc)}
                      </TableCell>
                      <TableCell className="text-right text-orange-700">
                        {formatVND(item.mtc)}
                      </TableCell>
                    </>
                  )}
                </TableRow>
                {expanded === item.mhdg && (
                  <TableRow>
                    <TableCell colSpan={showPrices ? 6 : 3} className="p-0">
                      <ItemDetail mhdg={item.mhdg} source={region} />
                    </TableCell>
                  </TableRow>
                )}
              </Fragment>
            ))}
            {items.length === 0 && (
              <TableRow>
                <TableCell
                  colSpan={showPrices ? 6 : 3}
                  className="text-center py-8 text-muted-foreground"
                >
                  Không tìm thấy công việc nào
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      {pages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-4">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
          >
            Trước
          </Button>
          <span className="text-sm text-muted-foreground">
            Trang {page} / {pages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= pages}
            onClick={() => onPageChange(page + 1)}
          >
            Sau
          </Button>
        </div>
      )}
    </div>
  );
}
