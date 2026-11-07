from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    estimate_type = Column(String(20), default="new")  # "new" or "repair"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # nullable for backward compat
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    settings = relationship("ProjectSettings", uselist=False, back_populates="project", cascade="all, delete-orphan")
    items = relationship("ProjectItem", back_populates="project", cascade="all, delete-orphan", order_by="ProjectItem.sort_order")
    sections = relationship("ProjectSection", back_populates="project", cascade="all, delete-orphan", order_by="ProjectSection.sort_order")
    other_costs = relationship("ProjectOtherCost", back_populates="project", cascade="all, delete-orphan")


class ProjectSection(Base):
    __tablename__ = "project_sections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    cost_type = Column(String(10), nullable=False)  # XD, LD, SC, KS
    sort_order = Column(Integer, default=0)
    chi_phi_chung_pct = Column(Float, nullable=True)
    thu_nhap_tt_pct = Column(Float, nullable=True)

    project = relationship("Project", back_populates="sections")
    items = relationship("ProjectItem", back_populates="section")


class ProjectItem(Base):
    __tablename__ = "project_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id = Column(Integer, ForeignKey("project_sections.id", ondelete="SET NULL"), nullable=True, index=True)
    mhdg = Column(String(25), nullable=False)
    tcv = Column(Text)
    dvt = Column(String(25))
    quantity = Column(Float, default=0)
    vlc = Column(Float, default=0)
    vlp = Column(Float, default=0)
    nc = Column(Float, default=0)
    mtc = Column(Float, default=0)
    override_vlc = Column(Float, nullable=True, default=None)
    override_nc = Column(Float, nullable=True, default=None)
    override_mtc = Column(Float, nullable=True, default=None)
    notes = Column(Text)
    sort_order = Column(Integer, default=0)
    actual_quantity = Column(Float, nullable=True)  # khoi luong thuc te nghiem thu
    acceptance_date = Column(DateTime, nullable=True)  # ngay nghiem thu
    acceptance_notes = Column(Text, nullable=True)  # ghi chu nghiem thu

    bid_package_id = Column(Integer, ForeignKey("bid_packages.id", ondelete="SET NULL"), nullable=True)

    project = relationship("Project", back_populates="items")
    section = relationship("ProjectSection", back_populates="items")
    bid_package = relationship("BidPackage", back_populates="items")


class ProjectSettings(Base):
    __tablename__ = "project_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True)
    regulation_code = Column(String(50), default="TT12-2021")
    db_type = Column(String(50), default="XD+LD+SC")
    source = Column(String(50), default="norm")
    template = Column(String(100))
    zone = Column(String(10))
    chi_phi_chung_pct = Column(Float, default=6.5)
    thu_nhap_tt_pct = Column(Float, default=5.5)
    vat_pct = Column(Float, default=10.0)
    nha_tam_pct = Column(Float, default=1.0)
    truc_tiep_khac_pct = Column(Float, default=2.5)
    k_vlc = Column(Float, nullable=True)   # VLC coefficient for repair (e.g., 1.05)
    k_nc = Column(Float, nullable=True)    # NC coefficient for repair (e.g., 1.1)
    k_mtc = Column(Float, nullable=True)   # MTC coefficient for repair (e.g., 1.1)
    chu_dau_tu = Column(String(255), nullable=True)
    dia_diem = Column(String(255), nullable=True)
    nguoi_lap = Column(String(100), nullable=True)
    nguoi_kiem_tra = Column(String(100), nullable=True)

    project = relationship("Project", back_populates="settings")


class ProjectOtherCost(Base):
    __tablename__ = "project_other_costs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(50), nullable=False)  # "thiet_bi", "tu_van", "qlda", "khac", "du_phong"
    name = Column(String(255), nullable=False)
    calc_type = Column(String(20), default="percent")  # "percent" or "fixed"
    percent_value = Column(Float, nullable=True)
    fixed_value = Column(Float, nullable=True)
    notes = Column(Text)
    sort_order = Column(Integer, default=0)

    project = relationship("Project", back_populates="other_costs")


class BidPackage(Base):
    __tablename__ = "bid_packages"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    package_type = Column(String(50), default="XD")  # XD, TB, TV, etc.
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    project = relationship("Project", backref="bid_packages")
    items = relationship("ProjectItem", back_populates="bid_package")
