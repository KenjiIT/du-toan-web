export interface DonGia {
  mhdg: string;
  tcv: string | null;
  dvt: string | null;
  vlc: number | null;
  vlp: number | null;
  nc: number | null;
  mtc: number | null;
  plv: string | null;
  regulation_code: string;
  source: string | null;
}

export interface DinhMuc {
  mhdm: string;
  msvt: string;
  tvt: string | null;
  dvt: string | null;
  hao_phi: number | null;
  gia: number | null;
  resource_type: string;
}

export interface PhuLucVua {
  btm: string;
  tg: string | null;
  dvt: string | null;
  mxm: string | null;
  hpxm: number | null;
  cat: string | null;
  hpc: number | null;
  da: string | null;
  hpd: number | null;
  vcuc: string | null;
  hpv: number | null;
}

export interface DonGiaDetail {
  don_gia: DonGia;
  dinh_muc: DinhMuc[];
  phu_luc_vua: PhuLucVua | null;
}

export interface Regulation {
  id: number;
  code: string;
  name: string;
  description: string;
}

export interface Region {
  id: number;
  name: string;
  category: string;
}

export interface Chapter {
  code: string;
  name: string;
  count: number;
}

export interface ProjectSettings {
  regulation_code: string;
  db_type: string;
  source: string;
  chi_phi_chung_pct: number;
  thu_nhap_tt_pct: number;
  vat_pct: number;
  nha_tam_pct: number;
  truc_tiep_khac_pct: number;
  k_vlc: number | null;
  k_nc: number | null;
  k_mtc: number | null;
  chu_dau_tu?: string | null;
  dia_diem?: string | null;
  nguoi_lap?: string | null;
  nguoi_kiem_tra?: string | null;
}

export interface Project {
  id: number;
  name: string;
  description: string | null;
  estimate_type: string;
  item_count: number;
  total_cost: number;
  settings: ProjectSettings | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectItem {
  id: number;
  mhdg: string;
  tcv: string | null;
  dvt: string | null;
  quantity: number;
  vlc: number;
  vlp: number;
  nc: number;
  mtc: number;
  override_vlc: number | null;
  override_nc: number | null;
  override_mtc: number | null;
  thanh_tien_vlc: number;
  thanh_tien_nc: number;
  thanh_tien_mtc: number;
  thanh_tien: number;
  notes: string | null;
  sort_order: number;
  section_id: number | null;
}

export interface CostSummary {
  vlc: number;
  nc: number;
  mtc: number;
  truc_tiep_khac: number;
  t: number;
  c: number;
  tl: number;
  g: number;
  gtgt: number;
  nha_tam: number;
  gxd: number;
  chi_phi_chung_pct: number;
  thu_nhap_tt_pct: number;
  vat_pct: number;
  nha_tam_pct: number;
  truc_tiep_khac_pct: number;
  estimate_type?: string;
  k_vlc?: number | null;
  k_nc?: number | null;
  k_mtc?: number | null;
}

export interface ProjectSection {
  id: number;
  project_id: number;
  name: string;
  cost_type: string;
  sort_order: number;
  chi_phi_chung_pct: number | null;
  thu_nhap_tt_pct: number | null;
}

export interface SectionCostSummary {
  vlc: number;
  nc: number;
  mtc: number;
  truc_tiep_khac: number;
  t: number;
  c: number;
  tl: number;
  g: number;
  gtgt: number;
  nha_tam: number;
  gxd: number;
  chi_phi_chung_pct: number;
  thu_nhap_tt_pct: number;
}

export interface SectionWithItems extends ProjectSection {
  items: ProjectItem[];
  subtotal: SectionCostSummary | null;
}

export interface ProjectDetail {
  project: Project;
  items: ProjectItem[];
  sections: SectionWithItems[];
  summary: CostSummary;
}

export interface ProjectCreate {
  name: string;
  description?: string;
  estimate_type?: string;
  settings?: {
    regulation_code?: string;
    db_type?: string;
    source?: string;
    k_vlc?: number | null;
    k_nc?: number | null;
    k_mtc?: number | null;
  };
}

export interface ProjectItemCreate {
  mhdg: string;
  quantity?: number;
  notes?: string;
}

export interface PhanTichResource {
  msvt: string;
  tvt: string | null;
  dvt: string | null;
  type: string;
  hao_phi: number;
  gia: number;
  thanh_tien: number;
}

export interface PhanTichPLV {
  btm: string;
  tg: string | null;
  total_cost: number;
  components: PhanTichResource[];
}

export interface PhanTichResult {
  mhdg: string;
  tcv: string | null;
  dvt: string | null;
  vlc: number;
  nc: number;
  mtc: number;
  total: number;
  details: PhanTichResource[];
  phu_luc_vua: PhanTichPLV | null;
}

export interface VatTu {
  id: number;
  msvt: string;
  tvt: string | null;
  dvt: string | null;
  gia_goc: number;
  lvt: string | null;
  regulation_code: string;
  source: string | null;
}

// --- CVC (Transport Cost) Types ---

export interface CvcVehicle {
  id: string;
  loaioto: string;
  mamay: string;
}

export interface CvcMaterial {
  vatlieu: string;
}

export interface CvcCoefficient {
  id: string;
  heso: string;
}

export interface CvcRoadType extends CvcCoefficient {
  loaiduong: string;
}

export interface CvcTerrainType extends CvcCoefficient {
  diahinh: string;
}

export interface CvcSlopeType extends CvcCoefficient {
  dodoc: string;
}

export interface CvcCalculateRequest {
  vatlieu: string;
  culy_km: number;
  vehicle_id?: string | null;
  loaiduong_id?: string;
  diahinh_id?: string;
  dodoc_id?: string;
}

export interface CvcMachineDetail {
  vatlieu: string;
  phuongtien: string;
  loaioto: string | null;
  culy: string;
  haophi: number;
  donvi: string;
  quydoidv: number;
  road_coeff: number;
  terrain_coeff: number;
  slope_coeff: number;
  adjusted_haophi: number;
}

export interface CvcManualDetail {
  nhomvatlieu: string;
  culy_m: number;
  haophi_base: number;
  haophi_extra: number;
  haophi_total: number;
  donvi: string;
  boclen: number;
  bocxuong: number;
  terrain_coeff: number;
  slope_coeff: number;
  adjusted_haophi: number;
}

export interface CvcCalculateResult {
  machine: CvcMachineDetail | null;
  manual: CvcManualDetail | null;
  loaiduong: string;
  diahinh: string;
  dodoc: string;
}

// --- Price Adjustment (Bù giá) Types ---

export interface BuGiaMaterial {
  msvt: string;
  tvt: string | null;
  dvt: string | null;
  total_hao_phi: number;
  gia_dm: number;
  gia_tt: number;
  chenh_lech_dv: number;
  chenh_lech_tt: number;
}

export interface BuGiaItemMaterial {
  msvt: string;
  tvt: string | null;
  dvt: string | null;
  hao_phi: number;
  gia_dm: number;
  gia_tt: number;
  chenh_lech_dv: number;
  chenh_lech_tt: number;
}

export interface BuGiaItemDetail {
  mhdg: string;
  tcv: string | null;
  quantity: number;
  materials: BuGiaItemMaterial[];
  bu_gia_item: number;
}

export interface BuGiaResponse {
  source_norm: string;
  source_market: string;
  materials: BuGiaMaterial[];
  total_bu_gia: number;
  items_detail: BuGiaItemDetail[];
}

// --- THVT (Tổng hợp vật tư) Types ---

export interface ThvtResource {
  msvt: string;
  tvt: string | null;
  dvt: string | null;
  total_hao_phi: number;
  gia: number;
  thanh_tien: number;
}

export interface ThvtResponse {
  vat_lieu: ThvtResource[];
  nhan_cong: ThvtResource[];
  may_thi_cong: ThvtResource[];
  total_vl: number;
  total_nc: number;
  total_mtc: number;
  total: number;
  item_count: number;
  resource_count: { vl: number; nc: number; mtc: number };
}

export interface SearchParams {
  q?: string;
  chapter?: string;
  regulation_code?: string;
  db_type?: string;
  region?: string;
  page?: number;
  limit?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}

// --- Price Comparison Types ---

export interface DonGiaComparison {
  source: string;
  vlc: number;
  nc: number;
  mtc: number;
  total: number;
}

export interface DonGiaCompareResult {
  mhdg: string;
  tcv: string | null;
  dvt: string | null;
  comparisons: DonGiaComparison[];
}

export interface VatTuComparison {
  source: string;
  gia_goc: number;
}

export interface VatTuCompareResult {
  msvt: string;
  tvt: string | null;
  dvt: string | null;
  comparisons: VatTuComparison[];
}

// --- Coefficients (Hệ số điều chỉnh) Types ---

export interface CoefficientRegion {
  region: string;
  decision_refs: string[];
  zones: string[];
}

export interface LaborPrice {
  ma_nc: string;
  nhom: string;
  khu_vuc_i: number | null;
  khu_vuc_ii: number | null;
}

export interface LaborPriceResponse {
  items: LaborPrice[];
  total: number;
  page: number;
  limit: number;
  region: string;
  decision_ref: string | null;
}

export interface MachinePrice {
  mh: string;
  lm_tb: string | null;
  gcm: number;
  cpkh: number;
  cpsc: number;
  cpk: number;
  cpnl: number;
  cptl: number;
}

export interface MachinePriceResponse {
  items: MachinePrice[];
  total: number;
  page: number;
  limit: number;
  region: string;
  zone: string;
  decision_ref: string | null;
}

// --- SVDT (Suất vốn đầu tư) Types ---

export interface SuatVonDauTu {
  id: number;
  loai_cong_trinh: string;
  don_vi: string | null;
  suat_von: number;
  trong_do_xd: number | null;
  trong_do_tb: number | null;
  nam: number | null;
  quyet_dinh: string | null;
  ghi_chu: string | null;
}

export interface SvdtCalculateRequest {
  svdt_id: number;
  dien_tich: number;
}

export interface SvdtCalculateResult {
  loai_cong_trinh: string;
  don_vi: string | null;
  suat_von: number;
  dien_tich: number;
  uoc_tinh_xd: number;
  uoc_tinh_tb: number;
  tong_uoc_tinh: number;
}

// --- TMDT (Tổng mức đầu tư) Types ---

export interface OtherCost {
  id: number;
  project_id: number;
  category: string;
  name: string;
  calc_type: string;
  percent_value: number | null;
  fixed_value: number | null;
  notes: string | null;
  sort_order: number;
}

export interface OtherCostCreate {
  category: string;
  name: string;
  calc_type?: string;
  percent_value?: number | null;
  fixed_value?: number | null;
  notes?: string | null;
  sort_order?: number;
}

export interface TmdtCategoryItem {
  id: number;
  name: string;
  calc_type: string;
  percent_value: number | null;
  fixed_value: number | null;
  amount: number;
}

export interface TmdtCategory {
  category: string;
  label: string;
  items: TmdtCategoryItem[];
  subtotal: number;
}

export interface TmdtResponse {
  g_xd: number;
  categories: TmdtCategory[];
  g_tb: number;
  g_tv: number;
  g_qlda: number;
  g_k: number;
  subtotal_before_dp: number;
  g_dp: number;
  tmdt: number;
}

// --- Gói thầu (Bid Package) Types ---

export interface BidPackage {
  id: number;
  project_id: number;
  name: string;
  package_type: string;
  description: string | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface BidPackageSummary extends BidPackage {
  item_count: number;
  total_cost: number;
  vlc: number;
  nc: number;
  mtc: number;
}

export interface BidPackageDetail extends BidPackageSummary {
  items: ProjectItem[];
  cost_breakdown: CostSummary | null;
}

export interface BidPackageCreate {
  name: string;
  package_type?: string;
  description?: string;
  sort_order?: number;
}

// --- Settlement (Quyết toán) Types ---

export interface SettlementItemUpdate {
  actual_quantity?: number | null;
  acceptance_date?: string | null;
  acceptance_notes?: string | null;
}

export interface SettlementItem {
  id: number;
  mhdg: string;
  tcv: string | null;
  dvt: string | null;
  quantity: number;
  actual_quantity: number | null;
  acceptance_date: string | null;
  acceptance_notes: string | null;
  unit_price: number;
  thanh_tien_du_toan: number;
  thanh_tien_thuc_te: number;
  chenh_lech: number;
  section_id: number | null;
  section_name: string | null;
}

export interface SettlementSectionSummary {
  section_id: number | null;
  section_name: string | null;
  total_du_toan: number;
  total_thuc_te: number;
  chenh_lech: number;
  item_count: number;
}

export interface SettlementReport {
  project_id: number;
  project_name: string;
  items: SettlementItem[];
  sections: SettlementSectionSummary[];
  total_du_toan: number;
  total_thuc_te: number;
  total_chenh_lech: number;
  pct_hoan_thanh: number;
  items_with_actual: number;
  total_items: number;
}
