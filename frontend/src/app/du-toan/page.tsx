"use client";

import { useRef, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { getProjects, createProject, deleteProject, importProjectJson } from "@/lib/api";
import { formatVND } from "@/lib/formatters";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { CreateProjectDialog } from "@/components/du-toan/CreateProjectDialog";

export default function DuToanPage() {
  const [showCreate, setShowCreate] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const { data: projects, isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: getProjects,
  });

  const deleteMutation = useMutation({
    mutationFn: deleteProject,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["projects"] }),
  });

  const importMutation = useMutation({
    mutationFn: importProjectJson,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });

  const handleImportFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      importMutation.mutate(file);
    }
    // Reset so the same file can be selected again
    e.target.value = "";
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Lập dự toán</h1>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => fileInputRef.current?.click()}
            disabled={importMutation.isPending}
          >
            {importMutation.isPending ? "Đang nhập..." : "Nhập dự toán"}
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            className="hidden"
            onChange={handleImportFile}
          />
          <Button onClick={() => setShowCreate(true)}>+ Tạo dự toán mới</Button>
        </div>
      </div>

      {isLoading && <p className="text-muted-foreground">Đang tải...</p>}

      {projects && projects.length === 0 && (
        <div className="text-center py-16 text-muted-foreground">
          <p className="text-lg mb-2">Chưa có dự toán nào</p>
          <p className="text-sm">Bấm &quot;Tạo dự toán mới&quot; để bắt đầu</p>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {projects?.map((p) => (
          <Card key={p.id} className="p-4 hover:shadow-md transition-shadow">
            <Link href={`/du-toan/${p.id}`} className="block">
              <h3 className="font-semibold text-lg mb-1">{p.name}</h3>
              {p.description && (
                <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
                  {p.description}
                </p>
              )}
              <div className="flex gap-4 text-sm text-muted-foreground mb-2">
                <span>{p.item_count} công việc</span>
                <span>{formatVND(p.total_cost)}</span>
              </div>
              <div className="text-xs text-muted-foreground">
                Cập nhật: {new Date(p.updated_at).toLocaleDateString("vi-VN")}
              </div>
            </Link>
            <div className="mt-3 flex gap-2">
              <Link href={`/du-toan/${p.id}`}>
                <Button variant="outline" size="sm">Mở</Button>
              </Link>
              <Button
                variant="outline"
                size="sm"
                className="text-red-600 hover:text-red-700"
                onClick={(e) => {
                  e.preventDefault();
                  if (confirm("Xóa dự toán này?")) deleteMutation.mutate(p.id);
                }}
              >
                Xóa
              </Button>
            </div>
          </Card>
        ))}
      </div>

      <CreateProjectDialog
        open={showCreate}
        onOpenChange={setShowCreate}
      />
    </div>
  );
}
