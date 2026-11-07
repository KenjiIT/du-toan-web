# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Optional

import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.don_gia import CHAPTER_NAMES
from app.database import get_db
from app.models.project import Project, ProjectItem, ProjectOtherCost, ProjectSection, ProjectSettings
from app.models.user import ProjectShare, User
from app.services.auth_service import get_optional_user
from app.schemas.project import (
    BuGiaResponse,
    CostSummaryResponse,
    OtherCostCreate,
    OtherCostResponse,
    OtherCostUpdate,
    ProjectCreate,
    ProjectDetailResponse,
    ProjectItemCreate,
    ProjectItemResponse,
    ProjectItemUpdate,
    ProjectResponse,
    ProjectSectionCreate,
    ProjectSectionResponse,
    ProjectSettingsCreate,
    ProjectSettingsResponse,
    ProjectUpdate,
    SectionCostSummary,
    SectionWithItems,
    SettlementItemUpdate,
    SettlementReport,
    ThvtResponse,
    TmdtResponse,
)
from app.services.cost_summary import (
    DEFAULT_SECTION_RATES,
    SECTION_NAMES,
    calculate_cost_summary_for_project,
    calculate_section_summary,
    detect_cost_type,
)
from app.services.price_calculator import calculate_unit_price

router = APIRouter(prefix="/projects", tags=["projects"])


class SwitchRegulationRequest(BaseModel):
    regulation_code: str
    source: str | None = None


def _item_response(item: ProjectItem) -> ProjectItemResponse:
    """Build an item response, applying overrides for thanh_tien calculations."""
    qty = item.quantity or 0
    eff_vlc = item.override_vlc if item.override_vlc is not None else (item.vlc or 0)
    eff_nc = item.override_nc if item.override_nc is not None else (item.nc or 0)
    eff_mtc = item.override_mtc if item.override_mtc is not None else (item.mtc or 0)
    tt_vlc = round(qty * eff_vlc)
    tt_nc = round(qty * eff_nc)
    tt_mtc = round(qty * eff_mtc)
    return ProjectItemResponse(
        id=item.id,
        mhdg=item.mhdg,
        tcv=item.tcv,
        dvt=item.dvt,
        quantity=qty,
        vlc=item.vlc,
        vlp=item.vlp,
        nc=item.nc,
        mtc=item.mtc,
        override_vlc=item.override_vlc,
        override_nc=item.override_nc,
        override_mtc=item.override_mtc,
        notes=item.notes,
        sort_order=item.sort_order or 0,
        section_id=item.section_id,
        thanh_tien_vlc=tt_vlc,
        thanh_tien_nc=tt_nc,
        thanh_tien_mtc=tt_mtc,
        thanh_tien=tt_vlc + tt_nc + tt_mtc,
    )


def _recalculate_items(db: Session, project_id: int, reg: str, dbt: str, src: str) -> int:
    """Recalculate prices for all items in a project. Returns count of updated items."""
    items = db.query(ProjectItem).filter(ProjectItem.project_id == project_id).all()
    count = 0
    for item in items:
        calc = calculate_unit_price(db, item.mhdg, reg, dbt, src)
        if "error" in calc:
            continue
        item.vlc = calc["vlc"]
        item.nc = calc["nc"]
        item.mtc = calc["mtc"]
        if calc.get("tcv"):
            item.tcv = calc["tcv"]
        if calc.get("dvt"):
            item.dvt = calc["dvt"]
        count += 1
    return count


def _project_response(project: Project, db: Session) -> dict:
    item_count = db.query(ProjectItem).filter(ProjectItem.project_id == project.id).count()
    resp = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "estimate_type": project.estimate_type or "new",
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "item_count": item_count,
        "settings": project.settings,
        "user_id": project.user_id,
    }
    return resp


def _ensure_section(db: Session, project_id: int, cost_type: str) -> ProjectSection:
    """Find or create a section for the given cost_type in the project."""
    section = db.query(ProjectSection).filter(
        ProjectSection.project_id == project_id,
        ProjectSection.cost_type == cost_type,
    ).first()
    if not section:
        sort_map = {"XD": 0, "LD": 1, "SC": 2, "KS": 3}
        defaults = DEFAULT_SECTION_RATES.get(cost_type, DEFAULT_SECTION_RATES["XD"])
        section = ProjectSection(
            project_id=project_id,
            name=f"Phần {cost_type} - {SECTION_NAMES.get(cost_type, cost_type)}",
            cost_type=cost_type,
            sort_order=sort_map.get(cost_type, 99),
            chi_phi_chung_pct=defaults["chi_phi_chung_pct"],
            thu_nhap_tt_pct=defaults["thu_nhap_tt_pct"],
        )
        db.add(section)
        db.flush()
    return section


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    if current_user:
        # Show: user's own projects + shared projects + legacy (no owner)
        shared_ids = db.query(ProjectShare.project_id).filter(
            ProjectShare.user_id == current_user.id
        ).subquery()
        projects = db.query(Project).filter(
            or_(
                Project.user_id == current_user.id,
                Project.id.in_(shared_ids),
                Project.user_id.is_(None),
            )
        ).order_by(Project.updated_at.desc()).all()
    else:
        projects = db.query(Project).order_by(Project.updated_at.desc()).all()
    return [_project_response(p, db) for p in projects]


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    project = Project(
        name=data.name,
        description=data.description,
        estimate_type=data.estimate_type,
        user_id=current_user.id if current_user else None,
    )
    db.add(project)
    db.flush()

    s = data.settings
    settings = ProjectSettings(
        project_id=project.id,
        regulation_code=s.regulation_code,
        db_type=s.db_type,
        source=s.source,
        template=s.template,
        zone=s.zone,
        chi_phi_chung_pct=s.chi_phi_chung_pct,
        thu_nhap_tt_pct=s.thu_nhap_tt_pct,
        vat_pct=s.vat_pct,
        nha_tam_pct=s.nha_tam_pct,
        truc_tiep_khac_pct=s.truc_tiep_khac_pct,
        k_vlc=s.k_vlc,
        k_nc=s.k_nc,
        k_mtc=s.k_mtc,
    )
    db.add(settings)
    db.commit()
    db.refresh(project)
    return _project_response(project, db)


@router.post("/import", response_model=ProjectResponse, status_code=201)
async def import_project_json(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Import a project from a JSON file."""
    content = await file.read()
    try:
        data = json.loads(content.decode("utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(400, f"Invalid JSON file: {exc}")

    # Validate required fields
    if not isinstance(data, dict) or "name" not in data:
        raise HTTPException(400, "JSON must contain at least a 'name' field")

    project = Project(
        name=data["name"],
        description=data.get("description"),
        estimate_type=data.get("estimate_type", "new"),
    )
    db.add(project)
    db.flush()

    # Import settings
    if "settings" in data and isinstance(data["settings"], dict):
        s = data["settings"]
        settings = ProjectSettings(
            project_id=project.id,
            regulation_code=s.get("regulation_code", "TT12-2021"),
            db_type=s.get("db_type", "XD+LD+SC"),
            source=s.get("source", "norm"),
            template=s.get("template"),
            zone=s.get("zone"),
            chi_phi_chung_pct=s.get("chi_phi_chung_pct", 6.5),
            thu_nhap_tt_pct=s.get("thu_nhap_tt_pct", 5.5),
            vat_pct=s.get("vat_pct", 10.0),
            nha_tam_pct=s.get("nha_tam_pct", 1.0),
            truc_tiep_khac_pct=s.get("truc_tiep_khac_pct", 2.5),
            k_vlc=s.get("k_vlc"),
            k_nc=s.get("k_nc"),
            k_mtc=s.get("k_mtc"),
        )
        db.add(settings)
        db.flush()

    # Import sections – track index → new section id
    section_id_by_index: dict[int, int] = {}
    for idx, sec_data in enumerate(data.get("sections", [])):
        if not isinstance(sec_data, dict):
            continue
        sec = ProjectSection(
            project_id=project.id,
            name=sec_data.get("name", f"Section {idx}"),
            cost_type=sec_data.get("cost_type", "XD"),
            sort_order=sec_data.get("sort_order", idx),
            chi_phi_chung_pct=sec_data.get("chi_phi_chung_pct"),
            thu_nhap_tt_pct=sec_data.get("thu_nhap_tt_pct"),
        )
        db.add(sec)
        db.flush()
        section_id_by_index[idx] = sec.id

    # Import items
    for item_data in data.get("items", []):
        if not isinstance(item_data, dict) or "mhdg" not in item_data:
            continue
        section_idx = item_data.get("section_index")
        section_id = section_id_by_index.get(section_idx) if section_idx is not None else None
        item = ProjectItem(
            project_id=project.id,
            section_id=section_id,
            mhdg=item_data["mhdg"],
            tcv=item_data.get("tcv"),
            dvt=item_data.get("dvt"),
            quantity=item_data.get("quantity", 0),
            vlc=item_data.get("vlc", 0),
            vlp=item_data.get("vlp", 0),
            nc=item_data.get("nc", 0),
            mtc=item_data.get("mtc", 0),
            override_vlc=item_data.get("override_vlc"),
            override_nc=item_data.get("override_nc"),
            override_mtc=item_data.get("override_mtc"),
            notes=item_data.get("notes"),
            sort_order=item_data.get("sort_order", 0),
        )
        db.add(item)

    # Import other costs
    for cost_data in data.get("other_costs", []):
        if not isinstance(cost_data, dict):
            continue
        cost = ProjectOtherCost(
            project_id=project.id,
            category=cost_data.get("category", "khac"),
            name=cost_data.get("name", ""),
            calc_type=cost_data.get("calc_type", "percent"),
            percent_value=cost_data.get("percent_value"),
            fixed_value=cost_data.get("fixed_value"),
            notes=cost_data.get("notes"),
            sort_order=cost_data.get("sort_order", 0),
        )
        db.add(cost)

    db.commit()
    db.refresh(project)
    return _project_response(project, db)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    items = db.query(ProjectItem).filter(
        ProjectItem.project_id == project_id
    ).order_by(ProjectItem.sort_order).all()

    item_responses = [_item_response(item) for item in items]

    summary = calculate_cost_summary_for_project(db, project_id)

    # Build sections with their items and subtotals
    sections_data: list[SectionWithItems] = []
    sections = db.query(ProjectSection).filter(
        ProjectSection.project_id == project_id
    ).order_by(ProjectSection.sort_order).all()

    if sections:
        settings_obj = db.query(ProjectSettings).filter(
            ProjectSettings.project_id == project_id
        ).first()
        if not settings_obj:
            settings_obj = ProjectSettings()

        for sec in sections:
            sec_items = [item for item in items if item.section_id == sec.id]
            sec_item_responses = [_item_response(i) for i in sec_items]
            sec_summary = calculate_section_summary(sec_items, settings_obj, sec)
            sections_data.append(SectionWithItems(
                id=sec.id,
                project_id=sec.project_id,
                name=sec.name,
                cost_type=sec.cost_type,
                sort_order=sec.sort_order,
                chi_phi_chung_pct=sec.chi_phi_chung_pct,
                thu_nhap_tt_pct=sec.thu_nhap_tt_pct,
                items=sec_item_responses,
                subtotal=SectionCostSummary(
                    **{k: v for k, v in sec_summary.items() if k in SectionCostSummary.model_fields}
                ),
            ))

    return ProjectDetailResponse(
        project=_project_response(project, db),
        items=item_responses,
        sections=sections_data,
        summary=CostSummaryResponse(**summary),
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, data: ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description
    if data.estimate_type is not None:
        project.estimate_type = data.estimate_type
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    return _project_response(project, db)


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    db.delete(project)
    db.commit()


# --- Share ---


class ShareRequest(BaseModel):
    username: str
    permission: str = "view"  # "view" or "edit"


@router.post("/{project_id}/share")
def share_project(
    project_id: int,
    data: ShareRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    if not current_user:
        raise HTTPException(401, "Authentication required to share projects")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    if project.user_id != current_user.id:
        raise HTTPException(403, "Only the project owner can share")
    target_user = db.query(User).filter(User.username == data.username).first()
    if not target_user:
        raise HTTPException(404, "User not found")
    if target_user.id == current_user.id:
        raise HTTPException(400, "Cannot share with yourself")
    # Check if already shared
    existing = db.query(ProjectShare).filter(
        ProjectShare.project_id == project_id,
        ProjectShare.user_id == target_user.id,
    ).first()
    if existing:
        existing.permission = data.permission
    else:
        share = ProjectShare(
            project_id=project_id,
            user_id=target_user.id,
            permission=data.permission,
        )
        db.add(share)
    db.commit()
    return {"message": f"Project shared with {data.username}"}


# --- Copy / Export / Import ---


@router.post("/{project_id}/copy", response_model=ProjectResponse)
def copy_project(project_id: int, db: Session = Depends(get_db)):
    """Duplicate a project with all its items, sections, settings, and other costs."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    new_project = Project(
        name=project.name + " (Bản sao)",
        description=project.description,
        estimate_type=project.estimate_type,
    )
    db.add(new_project)
    db.flush()

    # Copy settings
    if project.settings:
        s = project.settings
        new_settings = ProjectSettings(
            project_id=new_project.id,
            regulation_code=s.regulation_code,
            db_type=s.db_type,
            source=s.source,
            template=s.template,
            zone=s.zone,
            chi_phi_chung_pct=s.chi_phi_chung_pct,
            thu_nhap_tt_pct=s.thu_nhap_tt_pct,
            vat_pct=s.vat_pct,
            nha_tam_pct=s.nha_tam_pct,
            truc_tiep_khac_pct=s.truc_tiep_khac_pct,
            k_vlc=s.k_vlc,
            k_nc=s.k_nc,
            k_mtc=s.k_mtc,
        )
        db.add(new_settings)
        db.flush()

    # Copy sections – map old section id → new section id
    section_id_map: dict[int, int] = {}
    for sec in project.sections:
        new_sec = ProjectSection(
            project_id=new_project.id,
            name=sec.name,
            cost_type=sec.cost_type,
            sort_order=sec.sort_order,
            chi_phi_chung_pct=sec.chi_phi_chung_pct,
            thu_nhap_tt_pct=sec.thu_nhap_tt_pct,
        )
        db.add(new_sec)
        db.flush()
        section_id_map[sec.id] = new_sec.id

    # Copy items
    for item in project.items:
        new_item = ProjectItem(
            project_id=new_project.id,
            section_id=section_id_map.get(item.section_id) if item.section_id else None,
            mhdg=item.mhdg,
            tcv=item.tcv,
            dvt=item.dvt,
            quantity=item.quantity,
            vlc=item.vlc,
            vlp=item.vlp,
            nc=item.nc,
            mtc=item.mtc,
            override_vlc=item.override_vlc,
            override_nc=item.override_nc,
            override_mtc=item.override_mtc,
            notes=item.notes,
            sort_order=item.sort_order,
        )
        db.add(new_item)

    # Copy other costs
    for cost in project.other_costs:
        new_cost = ProjectOtherCost(
            project_id=new_project.id,
            category=cost.category,
            name=cost.name,
            calc_type=cost.calc_type,
            percent_value=cost.percent_value,
            fixed_value=cost.fixed_value,
            notes=cost.notes,
            sort_order=cost.sort_order,
        )
        db.add(new_cost)

    db.commit()
    db.refresh(new_project)
    return _project_response(new_project, db)


@router.get("/{project_id}/export/json")
def export_project_json(project_id: int, db: Session = Depends(get_db)):
    """Export project data as a downloadable JSON file."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    data: dict = {
        "name": project.name,
        "description": project.description,
        "estimate_type": project.estimate_type or "new",
    }

    if project.settings:
        s = project.settings
        data["settings"] = {
            "regulation_code": s.regulation_code,
            "db_type": s.db_type,
            "source": s.source,
            "template": s.template,
            "zone": s.zone,
            "chi_phi_chung_pct": s.chi_phi_chung_pct,
            "thu_nhap_tt_pct": s.thu_nhap_tt_pct,
            "vat_pct": s.vat_pct,
            "nha_tam_pct": s.nha_tam_pct,
            "truc_tiep_khac_pct": s.truc_tiep_khac_pct,
            "k_vlc": s.k_vlc,
            "k_nc": s.k_nc,
            "k_mtc": s.k_mtc,
        }

    data["sections"] = []
    for sec in project.sections:
        data["sections"].append({
            "name": sec.name,
            "cost_type": sec.cost_type,
            "sort_order": sec.sort_order,
            "chi_phi_chung_pct": sec.chi_phi_chung_pct,
            "thu_nhap_tt_pct": sec.thu_nhap_tt_pct,
        })

    # Build a map of section id → index in sections list for items
    section_idx_map: dict[int, int] = {}
    for idx, sec in enumerate(project.sections):
        section_idx_map[sec.id] = idx

    data["items"] = []
    for item in project.items:
        data["items"].append({
            "mhdg": item.mhdg,
            "tcv": item.tcv,
            "dvt": item.dvt,
            "quantity": item.quantity,
            "vlc": item.vlc,
            "vlp": item.vlp,
            "nc": item.nc,
            "mtc": item.mtc,
            "override_vlc": item.override_vlc,
            "override_nc": item.override_nc,
            "override_mtc": item.override_mtc,
            "notes": item.notes,
            "sort_order": item.sort_order,
            "section_index": section_idx_map.get(item.section_id) if item.section_id else None,
        })

    data["other_costs"] = []
    for cost in project.other_costs:
        data["other_costs"].append({
            "category": cost.category,
            "name": cost.name,
            "calc_type": cost.calc_type,
            "percent_value": cost.percent_value,
            "fixed_value": cost.fixed_value,
            "notes": cost.notes,
            "sort_order": cost.sort_order,
        })

    import io
    content = json.dumps(data, ensure_ascii=False, indent=2)
    buf = io.BytesIO(content.encode("utf-8"))
    filename = f"du-toan-{project_id}.json"
    return StreamingResponse(
        buf,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.put("/{project_id}/settings", response_model=ProjectSettingsResponse)
def update_settings(project_id: int, data: ProjectSettingsCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    settings = db.query(ProjectSettings).filter(ProjectSettings.project_id == project_id).first()
    if not settings:
        settings = ProjectSettings(project_id=project_id)
        db.add(settings)

    old_reg = settings.regulation_code
    old_src = settings.source

    for field in data.model_fields:
        setattr(settings, field, getattr(data, field))

    # Auto-recalculate if regulation or source changed
    needs_recalc = (data.regulation_code != old_reg or data.source != old_src)
    if needs_recalc:
        _recalculate_items(
            db, project_id,
            settings.regulation_code, settings.db_type, settings.source,
        )

    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(settings)
    return settings


@router.post("/{project_id}/recalculate")
def recalculate_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    settings = project.settings
    reg = settings.regulation_code if settings else "TT12-2021"
    dbt = settings.db_type if settings else "XD+LD+SC"
    src = settings.source if settings else "norm"

    count = _recalculate_items(db, project_id, reg, dbt, src)
    project.updated_at = datetime.utcnow()
    db.commit()
    return {"updated": count}


@router.post("/{project_id}/switch-regulation")
def switch_regulation(project_id: int, data: SwitchRegulationRequest, db: Session = Depends(get_db)):
    """Switch regulation and recalculate all item prices.

    This changes the regulation_code (and optionally source) in project settings,
    then recalculates all items using the new regulation's prices.
    Returns the count of updated items and list of items not found in the new regulation.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    settings = db.query(ProjectSettings).filter(ProjectSettings.project_id == project_id).first()
    if not settings:
        settings = ProjectSettings(project_id=project_id)
        db.add(settings)

    settings.regulation_code = data.regulation_code
    if data.source is not None:
        settings.source = data.source

    # Recalculate all items with new regulation, tracking not-found items
    items = db.query(ProjectItem).filter(ProjectItem.project_id == project_id).all()
    updated = 0
    not_found = []
    for item in items:
        calc = calculate_unit_price(
            db, item.mhdg,
            settings.regulation_code,
            settings.db_type,
            settings.source,
        )
        if "error" in calc:
            not_found.append(item.mhdg)
            continue
        item.vlc = calc["vlc"]
        item.nc = calc["nc"]
        item.mtc = calc["mtc"]
        if calc.get("tcv"):
            item.tcv = calc["tcv"]
        if calc.get("dvt"):
            item.dvt = calc["dvt"]
        updated += 1

    project.updated_at = datetime.utcnow()
    db.commit()
    return {"updated": updated, "not_found": not_found}


# --- Section CRUD ---


@router.get("/{project_id}/sections", response_model=list[ProjectSectionResponse])
def list_sections(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    sections = db.query(ProjectSection).filter(
        ProjectSection.project_id == project_id
    ).order_by(ProjectSection.sort_order).all()
    return [ProjectSectionResponse.model_validate(s) for s in sections]


@router.post("/{project_id}/sections", response_model=ProjectSectionResponse, status_code=201)
def create_section(project_id: int, data: ProjectSectionCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    section = ProjectSection(
        project_id=project_id,
        name=data.name,
        cost_type=data.cost_type,
        sort_order=data.sort_order,
        chi_phi_chung_pct=data.chi_phi_chung_pct,
        thu_nhap_tt_pct=data.thu_nhap_tt_pct,
    )
    db.add(section)
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(section)
    return ProjectSectionResponse.model_validate(section)


@router.put("/{project_id}/sections/{section_id}", response_model=ProjectSectionResponse)
def update_section(project_id: int, section_id: int, data: ProjectSectionCreate, db: Session = Depends(get_db)):
    section = db.query(ProjectSection).filter(
        ProjectSection.id == section_id, ProjectSection.project_id == project_id
    ).first()
    if not section:
        raise HTTPException(404, "Section not found")
    section.name = data.name
    section.cost_type = data.cost_type
    section.sort_order = data.sort_order
    section.chi_phi_chung_pct = data.chi_phi_chung_pct
    section.thu_nhap_tt_pct = data.thu_nhap_tt_pct
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(section)
    return ProjectSectionResponse.model_validate(section)


@router.delete("/{project_id}/sections/{section_id}", status_code=204)
def delete_section(project_id: int, section_id: int, db: Session = Depends(get_db)):
    section = db.query(ProjectSection).filter(
        ProjectSection.id == section_id, ProjectSection.project_id == project_id
    ).first()
    if not section:
        raise HTTPException(404, "Section not found")
    # Unassign items from this section before deleting
    db.query(ProjectItem).filter(ProjectItem.section_id == section_id).update({"section_id": None})
    db.delete(section)
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        project.updated_at = datetime.utcnow()
    db.commit()


@router.get("/{project_id}/chapters")
def get_project_chapters(project_id: int, db: Session = Depends(get_db)):
    """Return chapter names mapping."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    return CHAPTER_NAMES


# --- Price Adjustment (Bù giá) ---


@router.get("/{project_id}/bu-gia/sources")
def get_bu_gia_sources(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    from app.services.price_adjustment import get_available_sources

    return get_available_sources(db)


@router.get("/{project_id}/bu-gia", response_model=BuGiaResponse)
def get_bu_gia(
    project_id: int,
    source_market: str = "HoChiMinh2023",
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    from app.services.price_adjustment import calculate_price_adjustment

    result = calculate_price_adjustment(db, project_id, source_market)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


# --- Item CRUD ---


@router.post("/{project_id}/items", response_model=ProjectItemResponse, status_code=201)
def add_item(project_id: int, data: ProjectItemCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    settings = project.settings
    reg = settings.regulation_code if settings else "TT12-2021"
    dbt = settings.db_type if settings else "XD+LD+SC"
    src = settings.source if settings else "norm"

    calc = calculate_unit_price(db, data.mhdg, reg, dbt, src)
    if "error" in calc:
        raise HTTPException(404, calc["error"])

    max_order = db.query(ProjectItem.sort_order).filter(
        ProjectItem.project_id == project_id
    ).order_by(ProjectItem.sort_order.desc()).first()
    next_order = (max_order[0] + 1) if max_order and max_order[0] is not None else 0

    # Auto-detect cost_type and assign to the right section
    cost_type = detect_cost_type(data.mhdg)
    section = _ensure_section(db, project_id, cost_type)

    item = ProjectItem(
        project_id=project_id,
        section_id=section.id,
        mhdg=data.mhdg,
        tcv=calc["tcv"],
        dvt=calc["dvt"],
        quantity=data.quantity,
        vlc=calc["vlc"],
        nc=calc["nc"],
        mtc=calc["mtc"],
        notes=data.notes,
        sort_order=next_order,
    )
    db.add(item)
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    return _item_response(item)


@router.patch("/{project_id}/items/{item_id}", response_model=ProjectItemResponse)
def update_item(project_id: int, item_id: int, data: ProjectItemUpdate, db: Session = Depends(get_db)):
    item = db.query(ProjectItem).filter(
        ProjectItem.id == item_id, ProjectItem.project_id == project_id
    ).first()
    if not item:
        raise HTTPException(404, "Item not found")

    if data.quantity is not None:
        item.quantity = data.quantity
    if data.notes is not None:
        item.notes = data.notes
    if data.sort_order is not None:
        item.sort_order = data.sort_order

    # Handle override fields: explicitly provided (even as null) -> update
    provided = data.model_fields_set
    if "override_vlc" in provided:
        item.override_vlc = data.override_vlc
    if "override_nc" in provided:
        item.override_nc = data.override_nc
    if "override_mtc" in provided:
        item.override_mtc = data.override_mtc

    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    return _item_response(item)


@router.delete("/{project_id}/items/{item_id}", status_code=204)
def delete_item(project_id: int, item_id: int, db: Session = Depends(get_db)):
    item = db.query(ProjectItem).filter(
        ProjectItem.id == item_id, ProjectItem.project_id == project_id
    ).first()
    if not item:
        raise HTTPException(404, "Item not found")
    db.delete(item)
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        project.updated_at = datetime.utcnow()
    db.commit()


@router.get("/{project_id}/summary", response_model=CostSummaryResponse)
def get_summary(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    summary = calculate_cost_summary_for_project(db, project_id)
    return CostSummaryResponse(**summary)


# --- THVT (Tổng hợp vật tư) ---


@router.get("/{project_id}/thvt", response_model=ThvtResponse)
def get_thvt(project_id: int, db: Session = Depends(get_db)):
    """Calculate material/labor/machine summary for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    from app.services.thvt_service import calculate_thvt

    result = calculate_thvt(db, project_id)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@router.get("/{project_id}/export/thvt-excel")
def export_thvt_excel(project_id: int, db: Session = Depends(get_db)):
    """Export THVT as Excel file (.xlsx) with 3 sheets."""
    from fastapi.responses import StreamingResponse

    from app.services.thvt_service import calculate_thvt, generate_thvt_excel

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    thvt_data = calculate_thvt(db, project_id)
    if "error" in thvt_data:
        raise HTTPException(400, thvt_data["error"])

    buf = generate_thvt_excel(project.name, thvt_data)
    filename = f"thvt_{project_id}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --- TMDT (Tổng mức đầu tư) ---


@router.get("/{project_id}/tmdt", response_model=TmdtResponse)
def get_tmdt(project_id: int, db: Session = Depends(get_db)):
    """Calculate full TMDT for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    from app.services.tmdt_service import calculate_tmdt

    return calculate_tmdt(db, project_id)


@router.get("/{project_id}/other-costs", response_model=list[OtherCostResponse])
def list_other_costs(project_id: int, db: Session = Depends(get_db)):
    """List all other costs for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    costs = db.query(ProjectOtherCost).filter(
        ProjectOtherCost.project_id == project_id
    ).order_by(ProjectOtherCost.category, ProjectOtherCost.sort_order).all()
    return [OtherCostResponse.model_validate(c) for c in costs]


@router.post("/{project_id}/other-costs", response_model=OtherCostResponse, status_code=201)
def create_other_cost(project_id: int, data: OtherCostCreate, db: Session = Depends(get_db)):
    """Add an other cost item to a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    cost = ProjectOtherCost(
        project_id=project_id,
        category=data.category,
        name=data.name,
        calc_type=data.calc_type,
        percent_value=data.percent_value,
        fixed_value=data.fixed_value,
        notes=data.notes,
        sort_order=data.sort_order,
    )
    db.add(cost)
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(cost)
    return OtherCostResponse.model_validate(cost)


@router.post("/{project_id}/other-costs/init-defaults", response_model=list[OtherCostResponse])
def init_other_cost_defaults(project_id: int, db: Session = Depends(get_db)):
    """Create default consulting/management/other cost items with typical percentages."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    from app.services.tmdt_service import init_default_costs

    created = init_default_costs(db, project_id)
    if not created:
        raise HTTPException(400, "Default costs already exist for this project")
    project.updated_at = datetime.utcnow()
    db.commit()
    return [OtherCostResponse.model_validate(c) for c in created]


@router.patch("/{project_id}/other-costs/{cost_id}", response_model=OtherCostResponse)
def update_other_cost(project_id: int, cost_id: int, data: OtherCostUpdate, db: Session = Depends(get_db)):
    """Update an other cost item."""
    cost = db.query(ProjectOtherCost).filter(
        ProjectOtherCost.id == cost_id, ProjectOtherCost.project_id == project_id
    ).first()
    if not cost:
        raise HTTPException(404, "Other cost not found")
    provided = data.model_fields_set
    if "name" in provided and data.name is not None:
        cost.name = data.name
    if "calc_type" in provided and data.calc_type is not None:
        cost.calc_type = data.calc_type
    if "percent_value" in provided:
        cost.percent_value = data.percent_value
    if "fixed_value" in provided:
        cost.fixed_value = data.fixed_value
    if "notes" in provided:
        cost.notes = data.notes
    if "sort_order" in provided and data.sort_order is not None:
        cost.sort_order = data.sort_order
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(cost)
    return OtherCostResponse.model_validate(cost)


@router.delete("/{project_id}/other-costs/{cost_id}", status_code=204)
def delete_other_cost(project_id: int, cost_id: int, db: Session = Depends(get_db)):
    """Delete an other cost item."""
    cost = db.query(ProjectOtherCost).filter(
        ProjectOtherCost.id == cost_id, ProjectOtherCost.project_id == project_id
    ).first()
    if not cost:
        raise HTTPException(404, "Other cost not found")
    db.delete(cost)
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        project.updated_at = datetime.utcnow()
    db.commit()


# --- Settlement (Quyet toan) ---


@router.patch("/{project_id}/items/{item_id}/settlement")
def update_item_settlement(
    project_id: int, item_id: int,
    data: SettlementItemUpdate,
    db: Session = Depends(get_db),
):
    item = db.query(ProjectItem).filter(
        ProjectItem.id == item_id, ProjectItem.project_id == project_id
    ).first()
    if not item:
        raise HTTPException(404, "Item not found")
    provided = data.model_fields_set
    if "actual_quantity" in provided:
        item.actual_quantity = data.actual_quantity
    if "acceptance_date" in provided:
        item.acceptance_date = data.acceptance_date
    if "acceptance_notes" in provided:
        item.acceptance_notes = data.acceptance_notes
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    return _item_response(item)


@router.get("/{project_id}/settlement", response_model=SettlementReport)
def get_settlement(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    from app.services.settlement_service import calculate_settlement
    result = calculate_settlement(db, project_id)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@router.get("/{project_id}/export/settlement-excel")
def export_settlement_excel(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    from app.services.settlement_service import calculate_settlement
    from app.services.report_service import generate_settlement_excel
    settlement_data = calculate_settlement(db, project_id)
    if "error" in settlement_data:
        raise HTTPException(400, settlement_data["error"])
    buf = generate_settlement_excel(project.name, settlement_data)
    filename = f"quyet-toan_{project_id}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --- Government Report Templates (Bieu mau chuan) ---


def _get_metadata(settings_obj) -> dict:
    """Extract metadata fields from project settings."""
    if not settings_obj:
        return {}
    return {
        "chu_dau_tu": getattr(settings_obj, "chu_dau_tu", None),
        "dia_diem": getattr(settings_obj, "dia_diem", None),
        "nguoi_lap": getattr(settings_obj, "nguoi_lap", None),
        "nguoi_kiem_tra": getattr(settings_obj, "nguoi_kiem_tra", None),
    }


@router.get("/{project_id}/export/mau-01")
def export_mau_01(project_id: int, db: Session = Depends(get_db)):
    """Export Mau 01: Tong hop du toan xay dung cong trinh."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    from app.services.tmdt_service import calculate_tmdt
    from app.services.report_service import generate_mau_01_excel

    settings_obj = project.settings
    metadata = _get_metadata(settings_obj)
    summary = calculate_cost_summary_for_project(db, project_id)
    tmdt_data = calculate_tmdt(db, project_id)
    if isinstance(tmdt_data, dict):
        tmdt_dict = tmdt_data
    else:
        tmdt_dict = tmdt_data.model_dump() if hasattr(tmdt_data, "model_dump") else tmdt_data.__dict__

    buf = generate_mau_01_excel(project.name, metadata, tmdt_dict, summary)
    filename = f"mau-01_{project_id}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{project_id}/export/mau-02")
def export_mau_02(project_id: int, db: Session = Depends(get_db)):
    """Export Mau 02: Bang tinh chi phi xay dung."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    from app.services.report_service import generate_mau_02_excel

    settings_obj = project.settings
    metadata = _get_metadata(settings_obj)

    items = db.query(ProjectItem).filter(
        ProjectItem.project_id == project_id
    ).order_by(ProjectItem.sort_order).all()
    items_data = [_item_response(i).model_dump() for i in items]
    summary = calculate_cost_summary_for_project(db, project_id)

    buf = generate_mau_02_excel(project.name, metadata, items_data, summary)
    filename = f"mau-02_{project_id}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{project_id}/export/mau-03")
def export_mau_03(project_id: int, db: Session = Depends(get_db)):
    """Export Mau 03: Bang tong hop khoi luong - don gia."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    from app.services.report_service import generate_mau_03_excel

    settings_obj = project.settings
    metadata = _get_metadata(settings_obj)

    items = db.query(ProjectItem).filter(
        ProjectItem.project_id == project_id
    ).order_by(ProjectItem.sort_order).all()
    items_data = [_item_response(i).model_dump() for i in items]

    buf = generate_mau_03_excel(project.name, metadata, items_data)
    filename = f"mau-03_{project_id}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
