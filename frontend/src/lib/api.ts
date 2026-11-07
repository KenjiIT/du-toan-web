import type {
  DonGia,
  DonGiaDetail,
  DonGiaCompareResult,
  PhanTichResult,
  Regulation,
  Region,
  Chapter,
  SearchParams,
  PaginatedResponse,
  Project,
  ProjectDetail,
  ProjectItem,
  ProjectCreate,
  ProjectItemCreate,
  CostSummary,
  ProjectSettings,
  ProjectSection,
  VatTu,
  VatTuCompareResult,
  CvcVehicle,
  CvcMaterial,
  CvcRoadType,
  CvcTerrainType,
  CvcSlopeType,
  CvcCalculateRequest,
  CvcCalculateResult,
  BuGiaResponse,
  ThvtResponse,
  OtherCost,
  OtherCostCreate,
  TmdtResponse,
  CoefficientRegion,
  LaborPriceResponse,
  MachinePriceResponse,
  SuatVonDauTu,
  SvdtCalculateRequest,
  SvdtCalculateResult,
  BidPackage,
  BidPackageSummary,
  BidPackageDetail,
  BidPackageCreate,
  SettlementReport,
  SettlementItemUpdate,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("auth_token");
}

function getAuthHeaders(): Record<string, string> {
  const token = getAuthToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function fetchApi<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${BASE_URL}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== "") url.searchParams.set(k, v);
    });
  }
  const res = await fetch(url.toString(), {
    headers: { ...getAuthHeaders() },
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function searchDonGia(
  params: SearchParams
): Promise<PaginatedResponse<DonGia>> {
  const query: Record<string, string> = {};
  if (params.q) query.q = params.q;
  if (params.chapter) query.chapter = params.chapter;
  if (params.regulation_code) query.regulation_code = params.regulation_code;
  if (params.db_type) query.db_type = params.db_type;
  if (params.region) query.region = params.region;
  if (params.page) query.page = String(params.page);
  if (params.limit) query.limit = String(params.limit);
  return fetchApi<PaginatedResponse<DonGia>>("/don-gia", query);
}

export async function getDonGiaDetail(
  mhdg: string,
  regulationCode?: string,
  region?: string
): Promise<DonGiaDetail> {
  const query: Record<string, string> = {};
  if (regulationCode) query.regulation_code = regulationCode;
  if (region) query.region = region;
  return fetchApi<DonGiaDetail>(`/don-gia/${encodeURIComponent(mhdg)}`, query);
}

export async function getRegulations(): Promise<Regulation[]> {
  return fetchApi<Regulation[]>("/config/regulations");
}

export async function getRegions(): Promise<Region[]> {
  return fetchApi<Region[]>("/config/regions");
}

export async function getChapters(regulationCode?: string): Promise<Chapter[]> {
  const query: Record<string, string> = {};
  if (regulationCode) query.regulation_code = regulationCode;
  return fetchApi<Chapter[]>("/don-gia/chapters", query);
}

export async function getPhanTich(
  mhdg: string,
  source?: string,
  regulationCode?: string,
  dbType?: string,
): Promise<PhanTichResult> {
  const query: Record<string, string> = {};
  if (source) query.source = source;
  if (regulationCode) query.regulation_code = regulationCode;
  if (dbType) query.db_type = dbType;
  return fetchApi<PhanTichResult>(`/don-gia/${encodeURIComponent(mhdg)}/phan-tich`, query);
}

// --- Project APIs ---

async function mutateApi<T>(
  path: string,
  method: "POST" | "PUT" | "PATCH" | "DELETE",
  body?: unknown,
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: {
      ...getAuthHeaders(),
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (method === "DELETE" && res.status === 204) return undefined as T;
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error: ${res.status} ${text}`);
  }
  return res.json();
}

export async function getProjects(): Promise<Project[]> {
  return fetchApi<Project[]>("/projects");
}

export async function getProject(id: number): Promise<ProjectDetail> {
  return fetchApi<ProjectDetail>(`/projects/${id}`);
}

export async function createProject(data: ProjectCreate): Promise<Project> {
  return mutateApi<Project>("/projects", "POST", data);
}

export async function updateProject(id: number, data: { name?: string; description?: string; estimate_type?: string }): Promise<Project> {
  return mutateApi<Project>(`/projects/${id}`, "PATCH", data);
}

export async function deleteProject(id: number): Promise<void> {
  return mutateApi<void>(`/projects/${id}`, "DELETE");
}

export async function addProjectItem(projectId: number, data: ProjectItemCreate): Promise<ProjectItem> {
  return mutateApi<ProjectItem>(`/projects/${projectId}/items`, "POST", data);
}

export async function updateProjectItem(
  projectId: number,
  itemId: number,
  data: {
    quantity?: number;
    notes?: string;
    override_vlc?: number | null;
    override_nc?: number | null;
    override_mtc?: number | null;
  },
): Promise<ProjectItem> {
  return mutateApi<ProjectItem>(`/projects/${projectId}/items/${itemId}`, "PATCH", data);
}

export async function deleteProjectItem(projectId: number, itemId: number): Promise<void> {
  return mutateApi<void>(`/projects/${projectId}/items/${itemId}`, "DELETE");
}

export async function getProjectSummary(id: number): Promise<CostSummary> {
  return fetchApi<CostSummary>(`/projects/${id}/summary`);
}

export async function updateProjectSettings(
  projectId: number,
  settings: Partial<ProjectSettings>,
): Promise<ProjectSettings> {
  return mutateApi<ProjectSettings>(`/projects/${projectId}/settings`, "PUT", settings);
}

export async function recalculateProject(id: number): Promise<{ updated: number }> {
  return mutateApi<{ updated: number }>(`/projects/${id}/recalculate`, "POST");
}

export async function switchRegulation(
  projectId: number,
  data: { regulation_code: string; source?: string },
): Promise<{ updated: number; not_found: string[] }> {
  return mutateApi<{ updated: number; not_found: string[] }>(
    `/projects/${projectId}/switch-regulation`,
    "POST",
    data,
  );
}

// --- Section APIs ---

export async function createSection(
  projectId: number,
  data: { name: string; cost_type: string; sort_order?: number; chi_phi_chung_pct?: number | null; thu_nhap_tt_pct?: number | null },
): Promise<ProjectSection> {
  return mutateApi<ProjectSection>(`/projects/${projectId}/sections`, "POST", data);
}

export async function updateSection(
  projectId: number,
  sectionId: number,
  data: { name: string; cost_type: string; sort_order?: number; chi_phi_chung_pct?: number | null; thu_nhap_tt_pct?: number | null },
): Promise<ProjectSection> {
  return mutateApi<ProjectSection>(`/projects/${projectId}/sections/${sectionId}`, "PUT", data);
}

export async function deleteSection(projectId: number, sectionId: number): Promise<void> {
  return mutateApi<void>(`/projects/${projectId}/sections/${sectionId}`, "DELETE");
}

export async function getChapterNames(projectId: number): Promise<Record<string, string>> {
  return fetchApi<Record<string, string>>(`/projects/${projectId}/chapters`);
}

// --- Export APIs ---

export function getExportExcelUrl(projectId: number): string {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  return `${base}/projects/${projectId}/export/excel`;
}

export function getExportPdfUrl(projectId: number): string {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  return `${base}/projects/${projectId}/export/pdf`;
}

// --- CVC (Transport Cost) APIs ---

export async function getCvcVehicles(): Promise<CvcVehicle[]> {
  return fetchApi<CvcVehicle[]>("/cvc/vehicles");
}

export async function getCvcMaterials(): Promise<CvcMaterial[]> {
  return fetchApi<CvcMaterial[]>("/cvc/materials");
}

export async function getCvcRoadTypes(): Promise<CvcRoadType[]> {
  return fetchApi<CvcRoadType[]>("/cvc/road-types");
}

export async function getCvcTerrainTypes(): Promise<CvcTerrainType[]> {
  return fetchApi<CvcTerrainType[]>("/cvc/terrain-types");
}

export async function getCvcSlopeTypes(): Promise<CvcSlopeType[]> {
  return fetchApi<CvcSlopeType[]>("/cvc/slope-types");
}

export async function calculateCvc(data: CvcCalculateRequest): Promise<CvcCalculateResult> {
  return mutateApi<CvcCalculateResult>("/cvc/calculate", "POST", data);
}

// --- Vat Tu (Material Price) APIs ---

export async function searchVatTu(params: {
  q?: string;
  regulation_code?: string;
  source?: string;
  page?: number;
  limit?: number;
}): Promise<PaginatedResponse<VatTu>> {
  const query: Record<string, string> = {};
  if (params.q) query.q = params.q;
  if (params.regulation_code) query.regulation_code = params.regulation_code;
  if (params.source) query.source = params.source;
  if (params.page) query.page = String(params.page);
  if (params.limit) query.limit = String(params.limit);
  return fetchApi<PaginatedResponse<VatTu>>("/vat-tu", query);
}

// --- Price Adjustment (Bù giá) APIs ---

export async function getPriceAdjustmentSources(projectId: number): Promise<string[]> {
  return fetchApi<string[]>(`/projects/${projectId}/bu-gia/sources`);
}

export async function getPriceAdjustment(
  projectId: number,
  sourceMarket: string,
): Promise<BuGiaResponse> {
  return fetchApi<BuGiaResponse>(`/projects/${projectId}/bu-gia`, {
    source_market: sourceMarket,
  });
}

// --- THVT (Tổng hợp vật tư) APIs ---

export async function getThvt(projectId: number): Promise<ThvtResponse> {
  return fetchApi<ThvtResponse>(`/projects/${projectId}/thvt`);
}

export function getExportThvtExcelUrl(projectId: number): string {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  return `${base}/projects/${projectId}/export/thvt-excel`;
}

export function getExportPhanTichDonGiaUrl(projectId: number): string {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  return `${base}/projects/${projectId}/export/phan-tich-don-gia`;
}

export function getExportNhanCongUrl(projectId: number): string {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  return `${base}/projects/${projectId}/export/th-nhan-cong`;
}

export function getExportCaMayUrl(projectId: number): string {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  return `${base}/projects/${projectId}/export/th-ca-may`;
}

export function getExportFullReportUrl(projectId: number): string {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  return `${base}/projects/${projectId}/export/full-report`;
}

export async function updateVatTuPrice(id: number, gia_goc: number): Promise<VatTu> {
  return mutateApi<VatTu>(`/vat-tu/${id}`, "PATCH", { gia_goc });
}

export async function importVatTuCsv(
  file: File,
  regulationCode?: string,
): Promise<{ created: number; updated: number }> {
  const formData = new FormData();
  formData.append("file", file);
  const params = new URLSearchParams();
  if (regulationCode) params.set("regulation_code", regulationCode);
  const qs = params.toString() ? `?${params.toString()}` : "";
  const res = await fetch(`${BASE_URL}/vat-tu/import-csv${qs}`, {
    method: "POST",
    headers: { ...getAuthHeaders() },
    body: formData,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error: ${res.status} ${text}`);
  }
  return res.json();
}

// --- TMDT (Tổng mức đầu tư) APIs ---

export async function getTmdt(projectId: number): Promise<TmdtResponse> {
  return fetchApi<TmdtResponse>(`/projects/${projectId}/tmdt`);
}

export async function getOtherCosts(projectId: number): Promise<OtherCost[]> {
  return fetchApi<OtherCost[]>(`/projects/${projectId}/other-costs`);
}

export async function createOtherCost(projectId: number, data: OtherCostCreate): Promise<OtherCost> {
  return mutateApi<OtherCost>(`/projects/${projectId}/other-costs`, "POST", data);
}

export async function updateOtherCost(
  projectId: number,
  costId: number,
  data: Partial<OtherCostCreate>,
): Promise<OtherCost> {
  return mutateApi<OtherCost>(`/projects/${projectId}/other-costs/${costId}`, "PATCH", data);
}

export async function deleteOtherCost(projectId: number, costId: number): Promise<void> {
  return mutateApi<void>(`/projects/${projectId}/other-costs/${costId}`, "DELETE");
}

export async function initDefaultOtherCosts(projectId: number): Promise<OtherCost[]> {
  return mutateApi<OtherCost[]>(`/projects/${projectId}/other-costs/init-defaults`, "POST");
}

export function getExportTmdtExcelUrl(projectId: number): string {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  return `${base}/projects/${projectId}/export/tmdt-excel`;
}

// --- Copy / Import / Export Project APIs ---

export async function copyProject(id: number): Promise<Project> {
  return mutateApi<Project>(`/projects/${id}/copy`, "POST");
}

export function getExportJsonUrl(projectId: number): string {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  return `${base}/projects/${projectId}/export/json`;
}

export async function importProjectJson(file: File): Promise<Project> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}/projects/import`, {
    method: "POST",
    headers: { ...getAuthHeaders() },
    body: formData,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error: ${res.status} ${text}`);
  }
  return res.json();
}

// --- Price Comparison APIs ---

export async function compareDonGia(mhdg: string, sources: string[]): Promise<DonGiaCompareResult> {
  return fetchApi<DonGiaCompareResult>(`/don-gia/${encodeURIComponent(mhdg)}/compare`, {
    sources: sources.join(","),
  });
}

export async function compareVatTu(msvt: string, sources: string[]): Promise<VatTuCompareResult> {
  return fetchApi<VatTuCompareResult>(`/vat-tu/${encodeURIComponent(msvt)}/compare`, {
    sources: sources.join(","),
  });
}

export async function getCompareSources(): Promise<string[]> {
  return fetchApi<string[]>("/compare/sources");
}

// --- Coefficients (Hệ số điều chỉnh) APIs ---

export async function getCoefficientRegions(): Promise<CoefficientRegion[]> {
  return fetchApi<CoefficientRegion[]>("/coefficients/regions");
}

export async function getLaborPrices(
  region: string,
  params?: { q?: string; page?: number; limit?: number },
): Promise<LaborPriceResponse> {
  const query: Record<string, string> = { region };
  if (params?.q) query.q = params.q;
  if (params?.page) query.page = String(params.page);
  if (params?.limit) query.limit = String(params.limit);
  return fetchApi<LaborPriceResponse>("/coefficients/labor-prices", query);
}

export async function getMachinePrices(
  region: string,
  zone: string,
  params?: { q?: string; page?: number; limit?: number },
): Promise<MachinePriceResponse> {
  const query: Record<string, string> = { region, zone };
  if (params?.q) query.q = params.q;
  if (params?.page) query.page = String(params.page);
  if (params?.limit) query.limit = String(params.limit);
  return fetchApi<MachinePriceResponse>("/coefficients/machine-prices", query);
}

// --- SVDT (Suất vốn đầu tư) APIs ---

export async function searchSvdt(params: {
  q?: string;
  nam?: number;
  quyet_dinh?: string;
  page?: number;
  limit?: number;
}): Promise<PaginatedResponse<SuatVonDauTu>> {
  const query: Record<string, string> = {};
  if (params.q) query.q = params.q;
  if (params.nam) query.nam = String(params.nam);
  if (params.quyet_dinh) query.quyet_dinh = params.quyet_dinh;
  if (params.page) query.page = String(params.page);
  if (params.limit) query.limit = String(params.limit);
  return fetchApi<PaginatedResponse<SuatVonDauTu>>("/svdt", query);
}

export async function calculateSvdt(data: SvdtCalculateRequest): Promise<SvdtCalculateResult> {
  return mutateApi<SvdtCalculateResult>("/svdt/calculate", "POST", data);
}

export async function importSvdtCsv(file: File): Promise<{ created: number; errors: string[] }> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}/svdt/import-csv`, {
    method: "POST",
    headers: { ...getAuthHeaders() },
    body: formData,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error: ${res.status} ${text}`);
  }
  return res.json();
}

// --- Bid Package (Gói thầu) APIs ---

export async function getBidPackages(projectId: number): Promise<BidPackageSummary[]> {
  return fetchApi<BidPackageSummary[]>(`/projects/${projectId}/bid-packages`);
}

export async function createBidPackage(projectId: number, data: BidPackageCreate): Promise<BidPackage> {
  return mutateApi<BidPackage>(`/projects/${projectId}/bid-packages`, "POST", data);
}

export async function getBidPackageDetail(projectId: number, pkgId: number): Promise<BidPackageDetail> {
  return fetchApi<BidPackageDetail>(`/projects/${projectId}/bid-packages/${pkgId}`);
}

export async function updateBidPackage(projectId: number, pkgId: number, data: Partial<BidPackageCreate>): Promise<BidPackage> {
  return mutateApi<BidPackage>(`/projects/${projectId}/bid-packages/${pkgId}`, "PUT", data);
}

export async function deleteBidPackage(projectId: number, pkgId: number): Promise<void> {
  return mutateApi<void>(`/projects/${projectId}/bid-packages/${pkgId}`, "DELETE");
}

export async function assignItemsToBidPackage(projectId: number, pkgId: number, itemIds: number[]): Promise<{ updated: number }> {
  return mutateApi<{ updated: number }>(`/projects/${projectId}/bid-packages/${pkgId}/assign-items`, "POST", { item_ids: itemIds });
}

export async function removeItemsFromBidPackage(projectId: number, pkgId: number, itemIds: number[]): Promise<{ updated: number }> {
  return mutateApi<{ updated: number }>(`/projects/${projectId}/bid-packages/${pkgId}/remove-items`, "POST", { item_ids: itemIds });
}

export function getExportBidPackageExcelUrl(projectId: number, pkgId: number): string {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  return `${base}/projects/${projectId}/bid-packages/${pkgId}/export/excel`;
}

// --- Settlement (Quyết toán) APIs ---

export async function getSettlement(projectId: number): Promise<SettlementReport> {
  return fetchApi<SettlementReport>(`/projects/${projectId}/settlement`);
}

export async function updateItemSettlement(
  projectId: number,
  itemId: number,
  data: SettlementItemUpdate,
): Promise<ProjectItem> {
  return mutateApi<ProjectItem>(`/projects/${projectId}/items/${itemId}/settlement`, "PATCH", data);
}

export function getExportSettlementExcelUrl(projectId: number): string {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  return `${base}/projects/${projectId}/export/settlement-excel`;
}

// Government report export URLs
export function getExportMau01Url(projectId: number): string {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  return `${base}/projects/${projectId}/export/mau-01`;
}

export function getExportMau02Url(projectId: number): string {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  return `${base}/projects/${projectId}/export/mau-02`;
}

export function getExportMau03Url(projectId: number): string {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  return `${base}/projects/${projectId}/export/mau-03`;
}

// --- Auth APIs ---

export interface AuthUser {
  id: number;
  username: string;
  email: string | null;
  full_name: string | null;
  role: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  return mutateApi<LoginResponse>("/auth/login", "POST", { username, password });
}

export async function register(data: {
  username: string;
  password: string;
  email?: string;
  full_name?: string;
}): Promise<LoginResponse> {
  return mutateApi<LoginResponse>("/auth/register", "POST", data);
}

export async function getMe(): Promise<AuthUser> {
  return fetchApi<AuthUser>("/auth/me");
}

export async function updateProfile(data: { full_name?: string; email?: string }): Promise<AuthUser> {
  return mutateApi<AuthUser>("/auth/me", "PATCH", data);
}

export async function changePassword(oldPassword: string, newPassword: string): Promise<{ message: string }> {
  return mutateApi<{ message: string }>("/auth/change-password", "POST", {
    old_password: oldPassword,
    new_password: newPassword,
  });
}
