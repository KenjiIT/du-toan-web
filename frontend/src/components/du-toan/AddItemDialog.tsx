"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { searchDonGia, addProjectItem } from "@/lib/api";
import type { DonGia } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface Props {
  projectId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AddItemDialog({ projectId, open, onOpenChange }: Props) {
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<DonGia | null>(null);
  const [quantity, setQuantity] = useState("1");
  const queryClient = useQueryClient();

  const { data: results, isFetching } = useQuery({
    queryKey: ["don-gia-search", search],
    queryFn: () => searchDonGia({ q: search, limit: 20 }),
    enabled: search.length >= 2,
  });

  const mutation = useMutation({
    mutationFn: (data: { mhdg: string; quantity: number }) =>
      addProjectItem(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      onOpenChange(false);
      setSearch("");
      setSelected(null);
      setQuantity("1");
    },
  });

  const handleAdd = () => {
    if (!selected) return;
    mutation.mutate({
      mhdg: selected.mhdg,
      quantity: parseFloat(quantity) || 1,
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-3xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Thêm công việc</DialogTitle>
        </DialogHeader>

        <div className="space-y-3 flex-1 overflow-hidden flex flex-col">
          <Input
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setSelected(null);
            }}
            placeholder="Tìm theo mã hoặc tên công việc..."
            autoFocus
          />

          {selected ? (
            <div className="border rounded-md p-3 bg-muted/30">
              <div className="font-mono text-sm">{selected.mhdg}</div>
              <div className="text-sm mt-1">{selected.tcv}</div>
              <div className="text-xs text-muted-foreground mt-1">
                ĐVT: {selected.dvt}
              </div>
              <div className="mt-3">
                <label className="text-sm font-medium mb-1 block">
                  Khối lượng
                </label>
                <Input
                  type="number"
                  step="any"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  className="w-40"
                />
              </div>
            </div>
          ) : (
            <div className="flex-1 overflow-auto border rounded-md">
              {isFetching && (
                <p className="p-3 text-sm text-muted-foreground">
                  Đang tìm...
                </p>
              )}
              {results && results.items.length === 0 && (
                <p className="p-3 text-sm text-muted-foreground">
                  Không tìm thấy
                </p>
              )}
              {results && results.items.length > 0 && (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-28">Mã</TableHead>
                      <TableHead>Tên công việc</TableHead>
                      <TableHead className="w-16">ĐVT</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {results.items.map((item) => (
                      <TableRow
                        key={item.mhdg}
                        className="cursor-pointer hover:bg-muted/50"
                        onClick={() => setSelected(item)}
                      >
                        <TableCell className="font-mono text-xs">
                          {item.mhdg}
                        </TableCell>
                        <TableCell className="text-sm">{item.tcv}</TableCell>
                        <TableCell className="text-sm">{item.dvt}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => {
              if (selected) {
                setSelected(null);
              } else {
                onOpenChange(false);
              }
            }}
          >
            {selected ? "Chọn lại" : "Hủy"}
          </Button>
          <Button
            onClick={handleAdd}
            disabled={!selected || mutation.isPending}
          >
            {mutation.isPending ? "Đang thêm..." : "Thêm công việc"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
