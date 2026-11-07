"""Export endpoints for Excel and PDF downloads."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project, ProjectItem, ProjectSettings
from app.services.cost_summary import calculate_cost_summary_for_project
from app.services.export_service import generate_excel, generate_pdf
from app.services.price_calculator import calculate_unit_price
from app.services.report_service import (
    generate_ca_may_excel,
    generate_full_report_excel,
    generate_nhan_cong_excel,
    generate_phan_tich_don_gia_excel,
)
from app.services.thvt_service import calculate_thvt

router = APIRouter(prefix="/projects", tags=["export"])


def _get_project_data(project_id: int, db: Session):
    """Fetch project, items, and summary for export."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    items = (
        db.query(ProjectItem)
        .filter(ProjectItem.project_id == project_id)
        .order_by(ProjectItem.sort_order)
        .all()
    )

    item_dicts = []
    for item in items:
        qty = item.quantity or 0
        vlc = item.vlc or 0
        nc = item.nc or 0
        mtc = item.mtc or 0
        tt_vlc = round(qty * vlc)
        tt_nc = round(qty * nc)
        tt_mtc = round(qty * mtc)
        item_dicts.append({
            "mhdg": item.mhdg,
            "tcv": item.tcv or "",
            "dvt": item.dvt or "",
            "quantity": qty,
            "vlc": vlc,
            "nc": nc,
            "mtc": mtc,
            "thanh_tien_vlc": tt_vlc,
            "thanh_tien_nc": tt_nc,
            "thanh_tien_mtc": tt_mtc,
            "thanh_tien": tt_vlc + tt_nc + tt_mtc,
        })

    summary = calculate_cost_summary_for_project(db, project_id)

    project_dict = {
        "name": project.name,
        "description": project.description or "",
    }

    return project_dict, item_dicts, summary


@router.get("/{project_id}/export/excel")
def export_excel(project_id: int, db: Session = Depends(get_db)):
    """Export project as Excel file (.xlsx)."""
    project_dict, item_dicts, summary = _get_project_data(project_id, db)
    buf = generate_excel(project_dict, item_dicts, summary)

    filename = f"du_toan_{project_id}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{project_id}/export/pdf")
def export_pdf(project_id: int, db: Session = Depends(get_db)):
    """Export project as PDF file."""
    project_dict, item_dicts, summary = _get_project_data(project_id, db)
    buf = generate_pdf(project_dict, item_dicts, summary)

    filename = f"du_toan_{project_id}.pdf"
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{project_id}/export/tmdt-excel")
def export_tmdt_excel(project_id: int, db: Session = Depends(get_db)):
    """Export TMDT as Excel file (.xlsx)."""
    from app.services.export_service import generate_tmdt_excel
    from app.services.tmdt_service import calculate_tmdt

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    tmdt_data = calculate_tmdt(db, project_id)
    project_dict = {"name": project.name, "description": project.description or ""}
    buf = generate_tmdt_excel(project_dict, tmdt_data)

    filename = f"tmdt_{project_id}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{project_id}/export/phan-tich-don-gia")
def export_phan_tich_don_gia(project_id: int, db: Session = Depends(get_db)):
    """Export detailed price analysis for all project items (.xlsx)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    settings = (
        db.query(ProjectSettings)
        .filter(ProjectSettings.project_id == project_id)
        .first()
    )
    reg = settings.regulation_code if settings else "TT12-2021"
    dbt = settings.db_type if settings else "XD+LD+SC"
    src = settings.source if settings else "norm"

    items = (
        db.query(ProjectItem)
        .filter(ProjectItem.project_id == project_id)
        .order_by(ProjectItem.sort_order)
        .all()
    )

    items_with_details = []
    for item in items:
        calc = calculate_unit_price(db, item.mhdg, reg, dbt, src)
        if "error" in calc:
            items_with_details.append({"error": calc["error"], "mhdg": item.mhdg})
            continue
        items_with_details.append(calc)

    buf = generate_phan_tich_don_gia_excel(project.name, items_with_details)

    filename = f"phan_tich_don_gia_{project_id}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{project_id}/export/th-nhan-cong")
def export_th_nhan_cong(project_id: int, db: Session = Depends(get_db)):
    """Export labor summary (.xlsx)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    thvt = calculate_thvt(db, project_id)
    buf = generate_nhan_cong_excel(project.name, thvt["nhan_cong"], thvt["total_nc"])

    filename = f"th_nhan_cong_{project_id}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{project_id}/export/th-ca-may")
def export_th_ca_may(project_id: int, db: Session = Depends(get_db)):
    """Export machine summary (.xlsx)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    thvt = calculate_thvt(db, project_id)
    buf = generate_ca_may_excel(project.name, thvt["may_thi_cong"], thvt["total_mtc"])

    filename = f"th_ca_may_{project_id}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{project_id}/export/full-report")
def export_full_report(project_id: int, db: Session = Depends(get_db)):
    """Export combined full report with all sheets (.xlsx)."""
    project_dict, item_dicts, summary = _get_project_data(project_id, db)
    thvt = calculate_thvt(db, project_id)

    tmdt_data = None
    try:
        from app.services.tmdt_service import calculate_tmdt

        tmdt_data = calculate_tmdt(db, project_id)
    except Exception:
        pass

    buf = generate_full_report_excel(
        project_dict["name"], item_dicts, thvt, summary, tmdt_data
    )

    filename = f"bao_cao_tong_hop_{project_id}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
