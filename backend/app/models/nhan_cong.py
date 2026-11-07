from sqlalchemy import Column, Float, Integer, String, Text

from app.database import Base


class NhanCong(Base):
    __tablename__ = "nhan_cong"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ma_nc = Column(String(25), nullable=False, index=True)
    ten = Column(String(255))
    cap_bac = Column(String(25))
    hsl_nd205 = Column(Float, default=0)
    hsl_tt05 = Column(Float, default=0)
    hsl_tt15 = Column(Float, default=0)
    cbbq = Column(Float, default=0)
    name = Column(String(50))
    phan_loai = Column(String(25))
    ten_tt = Column(String(255))


class GiaNhanCong(Base):
    __tablename__ = "gia_nhan_cong"

    id = Column(Integer, primary_key=True, autoincrement=True)
    region = Column(String(50), nullable=False, index=True)
    decision_ref = Column(String(255))
    ma_nc = Column(String(25), nullable=False)
    nhom = Column(String(100))
    khu_vuc_i = Column(Float, default=0)
    khu_vuc_ii = Column(Float, default=0)
    ghi_chu = Column(Text)


class GiaCaMayVung(Base):
    __tablename__ = "gia_ca_may_vung"

    id = Column(Integer, primary_key=True, autoincrement=True)
    region = Column(String(50), nullable=False, index=True)
    decision_ref = Column(String(255))
    zone = Column(String(10), nullable=False)
    mh = Column(String(25), nullable=False, index=True)
    lm_tb = Column(Text)
    cpkh = Column(Float, default=0)
    cpsc = Column(Float, default=0)
    cpk = Column(Float, default=0)
    cpnl = Column(Float, default=0)
    cptl = Column(Float, default=0)
    gcm = Column(Float, default=0)
