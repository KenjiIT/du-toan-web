"use client";

import type { CostSummary as CostSummaryType, SectionWithItems } from "@/lib/types";
import { formatVND } from "@/lib/formatters";
import { Card } from "@/components/ui/card";

interface Props {
  summary: CostSummaryType;
  sections?: SectionWithItems[];
}

function Row({
  label,
  value,
  pct,
  bold,
  highlight,
}: {
  label: string;
  value: number;
  pct?: number;
  bold?: boolean;
  highlight?: boolean;
}) {
  return (
    <div
      className={`flex items-center justify-between py-1.5 ${bold ? "font-semibold" : ""} ${highlight ? "text-blue-700 text-lg" : ""}`}
    >
      <span>
        {label}
        {pct != null && (
          <span className="text-xs text-muted-foreground ml-1">({pct}%)</span>
        )}
      </span>
      <span className="tabular-nums">{formatVND(value)}</span>
    </div>
  );
}

function SectionSummaryBlock({ section }: { section: SectionWithItems }) {
  if (!section.subtotal) return null;
  const s = section.subtotal;
  return (
    <div className="py-2">
      <div className="text-sm font-semibold text-muted-foreground mb-1">
        {section.name}
      </div>
      <Row label="T (trực tiếp)" value={s.t} />
      <Row label="C (chi phí chung)" value={s.c} pct={s.chi_phi_chung_pct} />
      <Row label="TL (thu nhập)" value={s.tl} pct={s.thu_nhap_tt_pct} />
      <Row label="G" value={s.g} />
      <Row label="GTGT" value={s.gtgt} />
      <Row label="GXD" value={s.gxd} bold />
    </div>
  );
}

export function CostSummaryCard({ summary, sections }: Props) {
  const hasSections = sections && sections.length > 0;

  return (
    <Card className="p-5">
      <div className="flex items-center gap-2 mb-3">
        <h3 className="font-semibold text-lg">Tổng hợp kinh phí</h3>
        {summary.estimate_type === "repair" && (
          <span className="text-xs text-orange-600 font-medium px-2 py-0.5 bg-orange-50 rounded border border-orange-200">
            Sửa chữa, cải tạo
          </span>
        )}
      </div>
      <div className="divide-y">
        {hasSections && (
          <div className="pb-2">
            <div className="text-sm font-medium text-muted-foreground mb-2">
              Chi tiết theo hạng mục
            </div>
            {sections.map((sec) => (
              <SectionSummaryBlock key={sec.id} section={sec} />
            ))}
          </div>
        )}
        <div className={hasSections ? "pt-3" : ""}>
          <div className="text-sm font-medium text-muted-foreground mb-1">
            {hasSections ? "Tổng công trình" : "Chi phí trực tiếp"}
          </div>
          <Row label="Vật liệu (VLC)" value={summary.vlc} />
          {summary.estimate_type === "repair" && summary.k_vlc != null && (
            <div className="text-xs text-orange-600 ml-4 -mt-1 mb-1">
              (x K={summary.k_vlc})
            </div>
          )}
          <Row label="Nhân công (NC)" value={summary.nc} />
          {summary.estimate_type === "repair" && summary.k_nc != null && (
            <div className="text-xs text-orange-600 ml-4 -mt-1 mb-1">
              (x K={summary.k_nc})
            </div>
          )}
          <Row label="Máy thi công (MTC)" value={summary.mtc} />
          {summary.estimate_type === "repair" && summary.k_mtc != null && (
            <div className="text-xs text-orange-600 ml-4 -mt-1 mb-1">
              (x K={summary.k_mtc})
            </div>
          )}
          <Row
            label="Trực tiếp khác (TT)"
            value={summary.truc_tiep_khac}
            pct={summary.truc_tiep_khac_pct}
          />
          <Row label="T = VLC + NC + MTC + TT" value={summary.t} bold />
        </div>
        <div className="py-2">
          <Row
            label="Chi phí chung (C)"
            value={summary.c}
            pct={summary.chi_phi_chung_pct}
          />
          <Row
            label="Thu nhập chịu thuế (TL)"
            value={summary.tl}
            pct={summary.thu_nhap_tt_pct}
          />
          <Row label="G = T + C + TL" value={summary.g} bold />
        </div>
        <div className="py-2">
          <Row
            label="Thuế GTGT"
            value={summary.gtgt}
            pct={summary.vat_pct}
          />
          <Row
            label="Nhà tạm"
            value={summary.nha_tam}
            pct={summary.nha_tam_pct}
          />
        </div>
        <div className="pt-2">
          <Row label="GXD = G + GTGT + Nhà tạm" value={summary.gxd} bold highlight />
        </div>
      </div>
    </Card>
  );
}
