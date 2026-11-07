"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { createProject } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateProjectDialog({ open, onOpenChange }: Props) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [estimateType, setEstimateType] = useState("new");
  const queryClient = useQueryClient();
  const router = useRouter();

  const mutation = useMutation({
    mutationFn: createProject,
    onSuccess: (project) => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      onOpenChange(false);
      setName("");
      setDescription("");
      setEstimateType("new");
      router.push(`/du-toan/${project.id}`);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    mutation.mutate({
      name: name.trim(),
      description: description.trim() || undefined,
      estimate_type: estimateType,
      settings: estimateType === "repair"
        ? { k_vlc: 1.05, k_nc: 1.1, k_mtc: 1.1 }
        : undefined,
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Tạo dự toán mới</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-1 block">
              Tên dự toán *
            </label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ví dụ: Nhà phố 3 tầng Q.7"
              autoFocus
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-1 block">Mô tả</label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Ghi chú thêm về dự toán..."
              rows={3}
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">Loại dự toán</label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="create_estimate_type"
                  value="new"
                  checked={estimateType === "new"}
                  onChange={() => setEstimateType("new")}
                  className="w-4 h-4"
                />
                <span className="text-sm">Công trình mới</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="create_estimate_type"
                  value="repair"
                  checked={estimateType === "repair"}
                  onChange={() => setEstimateType("repair")}
                  className="w-4 h-4"
                />
                <span className="text-sm">Sửa chữa, cải tạo</span>
              </label>
            </div>
            {estimateType === "repair" && (
              <p className="text-xs text-muted-foreground mt-1">
                Hệ số K mặc định: VLC=1.05, NC=1.1, MTC=1.1 (có thể chỉnh trong cài đặt)
              </p>
            )}
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Hủy
            </Button>
            <Button type="submit" disabled={!name.trim() || mutation.isPending}>
              {mutation.isPending ? "Đang tạo..." : "Tạo dự toán"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
