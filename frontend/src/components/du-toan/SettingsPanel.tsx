"use client";

import { useState, useEffect, useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  updateProjectSettings,
  updateProject,
  recalculateProject,
  switchRegulation,
  getRegulations,
  getRegions,
} from "@/lib/api";
import type { ProjectSettings } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";

interface SettingsPanelProps {
  projectId: number;
  settings: ProjectSettings;
  estimateType?: string;
}

export function SettingsPanel({ projectId, settings, estimateType = "new" }: SettingsPanelProps) {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<ProjectSettings>({ ...settings });
  const [currentEstimateType, setCurrentEstimateType] = useState(estimateType);
  const [showRegulationConfirm, setShowRegulationConfirm] = useState(false);
  const [pendingRegulation, setPendingRegulation] = useState<string | null>(null);
  const [switchResult, setSwitchResult] = useState<{ updated: number; not_found: string[] } | null>(null);
  const prevRegulationRef = useRef(settings.regulation_code);

  useEffect(() => {
    setForm({ ...settings });
    setCurrentEstimateType(estimateType);
    prevRegulationRef.current = settings.regulation_code;
  }, [settings, estimateType]);

  const { data: regulations } = useQuery({
    queryKey: ["regulations"],
    queryFn: getRegulations,
    enabled: open,
  });

  const { data: regions } = useQuery({
    queryKey: ["regions"],
    queryFn: getRegions,
    enabled: open,
  });

  const saveMutation = useMutation({
    mutationFn: async (data: Partial<ProjectSettings>) => {
      // If estimate_type changed, update the project too
      if (currentEstimateType !== estimateType) {
        await updateProject(projectId, { estimate_type: currentEstimateType } as Record<string, string>);
      }
      return updateProjectSettings(projectId, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    },
  });

  const recalcMutation = useMutation({
    mutationFn: () => recalculateProject(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    },
  });

  const switchRegMutation = useMutation({
    mutationFn: (data: { regulation_code: string; source?: string }) =>
      switchRegulation(projectId, data),
    onSuccess: (result) => {
      setSwitchResult(result);
      setShowRegulationConfirm(false);
      setPendingRegulation(null);
      prevRegulationRef.current = form.regulation_code;
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    },
  });

  const handleRegulationChange = (newRegCode: string) => {
    setForm({ ...form, regulation_code: newRegCode });
    if (newRegCode !== prevRegulationRef.current) {
      setPendingRegulation(newRegCode);
      setShowRegulationConfirm(true);
    }
  };

  const handleConfirmSwitch = () => {
    if (pendingRegulation) {
      switchRegMutation.mutate({
        regulation_code: pendingRegulation,
        source: form.source,
      });
    }
  };

  const handleCancelSwitch = () => {
    setForm({ ...form, regulation_code: prevRegulationRef.current });
    setShowRegulationConfirm(false);
    setPendingRegulation(null);
  };

  const handleSave = () => {
    saveMutation.mutate(form);
  };

  const handleEstimateTypeChange = (type: string) => {
    setCurrentEstimateType(type);
    if (type === "repair") {
      // Set default K values if not already set
      setForm((prev) => ({
        ...prev,
        k_vlc: prev.k_vlc ?? 1.05,
        k_nc: prev.k_nc ?? 1.1,
        k_mtc: prev.k_mtc ?? 1.1,
      }));
    }
  };

  // Build region/source options from the regions data
  const sourceOptions = regions
    ? [
        { value: "norm", label: "Theo định mức (norm)" },
        ...regions.map((r) => ({
          value: r.name,
          label: r.name,
        })),
      ]
    : [{ value: form.source, label: form.source }];

  if (!open) {
    return (
      <div className="flex items-center gap-3">
        <Button variant="outline" size="sm" onClick={() => setOpen(true)}>
          Cài đặt dự toán
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => recalcMutation.mutate()}
          disabled={recalcMutation.isPending}
        >
          {recalcMutation.isPending ? "Đang tính..." : "Tính lại đơn giá"}
        </Button>
        {currentEstimateType === "repair" && (
          <span className="text-xs text-orange-600 font-medium px-2 py-0.5 bg-orange-50 rounded">
            Dự toán sửa chữa
          </span>
        )}
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center justify-between">
          <span>Cài đặt dự toán</span>
          <Button variant="ghost" size="sm" onClick={() => setOpen(false)}>
            Thu gọn
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Estimate Type Selection */}
        <div className="mb-4">
          <label className="text-sm font-medium mb-2 block">
            Loại dự toán
          </label>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="estimate_type"
                value="new"
                checked={currentEstimateType === "new"}
                onChange={() => handleEstimateTypeChange("new")}
                className="w-4 h-4"
              />
              <span className="text-sm">Công trình mới</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="estimate_type"
                value="repair"
                checked={currentEstimateType === "repair"}
                onChange={() => handleEstimateTypeChange("repair")}
                className="w-4 h-4"
              />
              <span className="text-sm">Sửa chữa, cải tạo</span>
            </label>
          </div>
        </div>

        {/* K Coefficients for repair */}
        {currentEstimateType === "repair" && (
          <div className="mb-4 p-3 bg-orange-50 rounded-md border border-orange-200">
            <label className="text-sm font-medium mb-2 block text-orange-800">
              Hệ số K (sửa chữa, cải tạo)
            </label>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="text-xs text-orange-700 mb-1 block">
                  K vật liệu (VLC)
                </label>
                <Input
                  type="number"
                  step="0.01"
                  className="h-8"
                  value={form.k_vlc ?? ""}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      k_vlc: e.target.value ? parseFloat(e.target.value) : null,
                    })
                  }
                  placeholder="1.05"
                />
              </div>
              <div>
                <label className="text-xs text-orange-700 mb-1 block">
                  K nhân công (NC)
                </label>
                <Input
                  type="number"
                  step="0.01"
                  className="h-8"
                  value={form.k_nc ?? ""}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      k_nc: e.target.value ? parseFloat(e.target.value) : null,
                    })
                  }
                  placeholder="1.1"
                />
              </div>
              <div>
                <label className="text-xs text-orange-700 mb-1 block">
                  K máy (MTC)
                </label>
                <Input
                  type="number"
                  step="0.01"
                  className="h-8"
                  value={form.k_mtc ?? ""}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      k_mtc: e.target.value ? parseFloat(e.target.value) : null,
                    })
                  }
                  placeholder="1.1"
                />
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {/* Regulation */}
          <div>
            <label className="text-sm font-medium mb-1 block">
              Thông tư / Quy định
            </label>
            <select
              className="w-full h-8 rounded-md border border-input bg-transparent px-2 text-sm"
              value={form.regulation_code}
              onChange={(e) => handleRegulationChange(e.target.value)}
            >
              {regulations?.map((r) => (
                <option key={r.code} value={r.code}>
                  {r.code} - {r.name}
                </option>
              )) ?? (
                <option value={form.regulation_code}>
                  {form.regulation_code}
                </option>
              )}
            </select>
          </div>

          {/* Source */}
          <div>
            <label className="text-sm font-medium mb-1 block">
              Nguồn giá / Vùng
            </label>
            <select
              className="w-full h-8 rounded-md border border-input bg-transparent px-2 text-sm"
              value={form.source}
              onChange={(e) => setForm({ ...form, source: e.target.value })}
            >
              {sourceOptions.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>

          {/* DB Type */}
          <div>
            <label className="text-sm font-medium mb-1 block">
              Loại công trình
            </label>
            <select
              className="w-full h-8 rounded-md border border-input bg-transparent px-2 text-sm"
              value={form.db_type}
              onChange={(e) => setForm({ ...form, db_type: e.target.value })}
            >
              <option value="XD+LD+SC">XD+LD+SC</option>
              <option value="XD">Xây dựng (XD)</option>
              <option value="LD">Lắp đặt (LD)</option>
              <option value="SC">Sửa chữa (SC)</option>
            </select>
          </div>

          {/* Cost percentages */}
          <div>
            <label className="text-sm font-medium mb-1 block">
              Chi phí chung (%)
            </label>
            <Input
              type="number"
              step="0.1"
              className="h-8"
              value={form.chi_phi_chung_pct}
              onChange={(e) =>
                setForm({
                  ...form,
                  chi_phi_chung_pct: parseFloat(e.target.value) || 0,
                })
              }
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-1 block">
              Thu nhập TT (%)
            </label>
            <Input
              type="number"
              step="0.1"
              className="h-8"
              value={form.thu_nhap_tt_pct}
              onChange={(e) =>
                setForm({
                  ...form,
                  thu_nhap_tt_pct: parseFloat(e.target.value) || 0,
                })
              }
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-1 block">VAT (%)</label>
            <Input
              type="number"
              step="0.1"
              className="h-8"
              value={form.vat_pct}
              onChange={(e) =>
                setForm({
                  ...form,
                  vat_pct: parseFloat(e.target.value) || 0,
                })
              }
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-1 block">
              Nhà tạm (%)
            </label>
            <Input
              type="number"
              step="0.1"
              className="h-8"
              value={form.nha_tam_pct}
              onChange={(e) =>
                setForm({
                  ...form,
                  nha_tam_pct: parseFloat(e.target.value) || 0,
                })
              }
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-1 block">
              Trực tiếp khác (%)
            </label>
            <Input
              type="number"
              step="0.1"
              className="h-8"
              value={form.truc_tiep_khac_pct}
              onChange={(e) =>
                setForm({
                  ...form,
                  truc_tiep_khac_pct: parseFloat(e.target.value) || 0,
                })
              }
            />
          </div>
        </div>

        <div className="mt-6 mb-2">
          <h4 className="text-sm font-semibold text-muted-foreground border-b pb-1">
            Thông tin biểu mẫu
          </h4>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <label className="text-sm font-medium mb-1 block">
              Chủ đầu tư
            </label>
            <Input
              type="text"
              className="h-8"
              value={form.chu_dau_tu ?? ""}
              onChange={(e) =>
                setForm({
                  ...form,
                  chu_dau_tu: e.target.value || null,
                })
              }
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-1 block">
              Địa điểm
            </label>
            <Input
              type="text"
              className="h-8"
              value={form.dia_diem ?? ""}
              onChange={(e) =>
                setForm({
                  ...form,
                  dia_diem: e.target.value || null,
                })
              }
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-1 block">
              Người lập
            </label>
            <Input
              type="text"
              className="h-8"
              value={form.nguoi_lap ?? ""}
              onChange={(e) =>
                setForm({
                  ...form,
                  nguoi_lap: e.target.value || null,
                })
              }
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-1 block">
              Người kiểm tra
            </label>
            <Input
              type="text"
              className="h-8"
              value={form.nguoi_kiem_tra ?? ""}
              onChange={(e) =>
                setForm({
                  ...form,
                  nguoi_kiem_tra: e.target.value || null,
                })
              }
            />
          </div>
        </div>

        <div className="flex gap-2 mt-4">
          <Button onClick={handleSave} disabled={saveMutation.isPending}>
            {saveMutation.isPending ? "Đang lưu..." : "Lưu cài đặt"}
          </Button>
          <Button
            variant="outline"
            onClick={() => recalcMutation.mutate()}
            disabled={recalcMutation.isPending}
          >
            {recalcMutation.isPending ? "Đang tính..." : "Tính lại đơn giá"}
          </Button>
          <Button variant="ghost" onClick={() => setOpen(false)}>
            Đóng
          </Button>
        </div>

        {saveMutation.isSuccess && (
          <p className="text-sm text-green-600 mt-2">Đã lưu cài đặt.</p>
        )}
        {recalcMutation.isSuccess && (
          <p className="text-sm text-green-600 mt-2">
            Đã tính lại đơn giá cho tất cả công việc.
          </p>
        )}

        {/* Regulation switch confirmation dialog */}
        {showRegulationConfirm && (
          <div className="mt-3 p-3 bg-yellow-50 border border-yellow-300 rounded-md">
            <p className="text-sm text-yellow-800 mb-2">
              Đổi thông tư sẽ tính lại giá tất cả công việc. Tiếp tục?
            </p>
            <div className="flex gap-2">
              <Button
                size="sm"
                onClick={handleConfirmSwitch}
                disabled={switchRegMutation.isPending}
              >
                {switchRegMutation.isPending ? "Đang chuyển..." : "Đồng ý chuyển"}
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={handleCancelSwitch}
                disabled={switchRegMutation.isPending}
              >
                Hủy
              </Button>
            </div>
          </div>
        )}

        {/* Switch regulation result */}
        {switchResult && (
          <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-md">
            <p className="text-sm text-blue-800">
              Đã cập nhật {switchResult.updated} công việc.
              {switchResult.not_found.length > 0 && (
                <span className="block mt-1 text-orange-700">
                  {switchResult.not_found.length} công việc không tìm thấy trong thông tư mới:{" "}
                  {switchResult.not_found.join(", ")}
                </span>
              )}
            </p>
            <Button
              size="sm"
              variant="ghost"
              className="mt-1"
              onClick={() => setSwitchResult(null)}
            >
              Đóng
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
