from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ProjectSettingsCreate(BaseModel):
    regulation_code: str = "TT12-2021"
    db_type: str = "XD+LD+SC"
    source: str = "norm"
    template: str | None = None
    zone: str | None = None
    chi_phi_chung_pct: float = 6.5
    thu_nhap_tt_pct: float = 5.5
    vat_pct: float = 10.0
    nha_tam_pct: float = 1.0
    truc_tiep_khac_pct: float = 2.5
    k_vlc: float | None = None
    k_nc: float | None = None
    k_mtc: float | None = None
    chu_dau_tu: str | None = None
    dia_diem: str | None = None
    nguoi_lap: str | None = None
    nguoi_kiem_tra: str | None = None


class ProjectSettingsResponse(ProjectSettingsCreate):
    id: int
    project_id: int
    model_config = {"from_attributes": True}


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    estimate_type: str = "new"  # "new" or "repair"
    settings: ProjectSettingsCreate = ProjectSettingsCreate()


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    estimate_type: str | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    estimate_type: str = "new"
    created_at: datetime
    updated_at: datetime
    item_count: int = 0
    settings: ProjectSettingsResponse | None = None
    user_id: int | None = None

    model_config = {"from_attributes": True}


class ProjectItemCreate(BaseModel):
    mhdg: str
    quantity: float = 0
    notes: str | None = None


class ProjectItemUpdate(BaseModel):
    quantity: float | None = None
    notes: str | None = None
    sort_order: int | None = None
    override_vlc: float | None = None
    override_nc: float | None = None
    override_mtc: float | None = None


class ProjectItemResponse(BaseModel):
    id: int
    mhdg: str
    tcv: str | None = None
    dvt: str | None = None
    quantity: float = 0
    vlc: float | None = 0
    vlp: float | None = 0
    nc: float | None = 0
    mtc: float | None = 0
    override_vlc: float | None = None
    override_nc: float | None = None
    override_mtc: float | None = None
    notes: str | None = None
    sort_order: int = 0
    section_id: int | None = None
    thanh_tien_vlc: float = 0
    thanh_tien_nc: float = 0
    thanh_tien_mtc: float = 0
    thanh_tien: float = 0

    model_config = {"from_attributes": True}


class CostSummaryResponse(BaseModel):
    vlc: float = 0
    nc: float = 0
    mtc: float = 0
    truc_tiep_khac: float = 0
    t: float = 0
    c: float = 0
    tl: float = 0
    g: float = 0
    gtgt: float = 0
    nha_tam: float = 0
    gxd: float = 0

    chi_phi_chung_pct: float = 6.5
    thu_nhap_tt_pct: float = 5.5
    vat_pct: float = 10.0
    nha_tam_pct: float = 1.0
    truc_tiep_khac_pct: float = 2.5

    estimate_type: str = "new"
    k_vlc: float | None = None
    k_nc: float | None = None
    k_mtc: float | None = None


# --- Section schemas ---


class ProjectSectionCreate(BaseModel):
    name: str
    cost_type: str  # XD, LD, SC, KS
    sort_order: int = 0
    chi_phi_chung_pct: float | None = None
    thu_nhap_tt_pct: float | None = None


class ProjectSectionResponse(BaseModel):
    id: int
    project_id: int
    name: str
    cost_type: str
    sort_order: int
    chi_phi_chung_pct: float | None = None
    thu_nhap_tt_pct: float | None = None

    model_config = {"from_attributes": True}


class SectionCostSummary(BaseModel):
    vlc: float = 0
    nc: float = 0
    mtc: float = 0
    truc_tiep_khac: float = 0
    t: float = 0
    c: float = 0
    tl: float = 0
    g: float = 0
    gtgt: float = 0
    nha_tam: float = 0
    gxd: float = 0
    chi_phi_chung_pct: float = 6.5
    thu_nhap_tt_pct: float = 5.5


class SectionWithItems(ProjectSectionResponse):
    items: list[ProjectItemResponse] = []
    subtotal: SectionCostSummary | None = None


class ProjectDetailResponse(BaseModel):
    project: ProjectResponse
    items: list[ProjectItemResponse]
    sections: list[SectionWithItems] = []
    summary: CostSummaryResponse


# --- Price Adjustment (Bù giá) schemas ---


# --- THVT (Tổng hợp vật tư) schemas ---


class ThvtResource(BaseModel):
    msvt: str
    tvt: str | None = None
    dvt: str | None = None
    total_hao_phi: float = 0
    gia: float = 0
    thanh_tien: float = 0


class ThvtResourceCount(BaseModel):
    vl: int = 0
    nc: int = 0
    mtc: int = 0


class ThvtResponse(BaseModel):
    vat_lieu: list[ThvtResource] = []
    nhan_cong: list[ThvtResource] = []
    may_thi_cong: list[ThvtResource] = []
    total_vl: float = 0
    total_nc: float = 0
    total_mtc: float = 0
    total: float = 0
    item_count: int = 0
    resource_count: ThvtResourceCount = ThvtResourceCount()


# --- Price Adjustment (Bù giá) schemas ---


class BuGiaMaterial(BaseModel):
    msvt: str
    tvt: str | None = None
    dvt: str | None = None
    total_hao_phi: float = 0
    gia_dm: float = 0
    gia_tt: float = 0
    chenh_lech_dv: float = 0
    chenh_lech_tt: float = 0


class BuGiaItemMaterial(BaseModel):
    msvt: str
    tvt: str | None = None
    dvt: str | None = None
    hao_phi: float = 0
    gia_dm: float = 0
    gia_tt: float = 0
    chenh_lech_dv: float = 0
    chenh_lech_tt: float = 0


class BuGiaItemDetail(BaseModel):
    mhdg: str
    tcv: str | None = None
    quantity: float = 0
    materials: list[BuGiaItemMaterial] = []
    bu_gia_item: float = 0


class BuGiaResponse(BaseModel):
    source_norm: str = "norm"
    source_market: str
    materials: list[BuGiaMaterial] = []
    total_bu_gia: float = 0
    items_detail: list[BuGiaItemDetail] = []


# --- TMDT (Tổng mức đầu tư) schemas ---


class OtherCostCreate(BaseModel):
    category: str
    name: str
    calc_type: str = "percent"
    percent_value: float | None = None
    fixed_value: float | None = None
    notes: str | None = None
    sort_order: int = 0


class OtherCostUpdate(BaseModel):
    name: str | None = None
    calc_type: str | None = None
    percent_value: float | None = None
    fixed_value: float | None = None
    notes: str | None = None
    sort_order: int | None = None


class OtherCostResponse(BaseModel):
    id: int
    project_id: int
    category: str
    name: str
    calc_type: str
    percent_value: float | None = None
    fixed_value: float | None = None
    notes: str | None = None
    sort_order: int = 0

    model_config = {"from_attributes": True}


class TmdtCategoryItem(BaseModel):
    id: int
    name: str
    calc_type: str
    percent_value: float | None = None
    fixed_value: float | None = None
    amount: float = 0


class TmdtCategory(BaseModel):
    category: str
    label: str
    items: list[TmdtCategoryItem] = []
    subtotal: float = 0


class TmdtResponse(BaseModel):
    g_xd: float = 0
    categories: list[TmdtCategory] = []
    g_tb: float = 0
    g_tv: float = 0
    g_qlda: float = 0
    g_k: float = 0
    subtotal_before_dp: float = 0
    g_dp: float = 0
    tmdt: float = 0


# --- Bid Package (Gói thầu) schemas ---


class BidPackageCreate(BaseModel):
    name: str
    package_type: str = "XD"
    description: str | None = None
    sort_order: int = 0


class BidPackageUpdate(BaseModel):
    name: str | None = None
    package_type: str | None = None
    description: str | None = None
    sort_order: int | None = None


class BidPackageResponse(BaseModel):
    id: int
    project_id: int
    name: str
    package_type: str
    description: str | None = None
    sort_order: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class BidPackageSummary(BidPackageResponse):
    item_count: int = 0
    total_cost: float = 0
    vlc: float = 0
    nc: float = 0
    mtc: float = 0


class BidPackageDetail(BidPackageSummary):
    items: list[ProjectItemResponse] = []
    cost_breakdown: CostSummaryResponse | None = None


# --- Settlement (Quyết toán) schemas ---


class SettlementItemUpdate(BaseModel):
    actual_quantity: float | None = None
    acceptance_date: datetime | None = None
    acceptance_notes: str | None = None


class SettlementItem(BaseModel):
    id: int
    mhdg: str
    tcv: str | None = None
    dvt: str | None = None
    quantity: float = 0
    actual_quantity: float | None = None
    acceptance_date: datetime | None = None
    acceptance_notes: str | None = None
    unit_price: float = 0
    thanh_tien_du_toan: float = 0
    thanh_tien_thuc_te: float = 0
    chenh_lech: float = 0
    section_id: int | None = None
    section_name: str | None = None
    model_config = {"from_attributes": True}


class SettlementSectionSummary(BaseModel):
    section_id: int | None = None
    section_name: str | None = None
    total_du_toan: float = 0
    total_thuc_te: float = 0
    chenh_lech: float = 0
    item_count: int = 0


class SettlementReport(BaseModel):
    project_id: int
    project_name: str
    items: list[SettlementItem] = []
    sections: list[SettlementSectionSummary] = []
    total_du_toan: float = 0
    total_thuc_te: float = 0
    total_chenh_lech: float = 0
    pct_hoan_thanh: float = 0
    items_with_actual: int = 0
    total_items: int = 0
