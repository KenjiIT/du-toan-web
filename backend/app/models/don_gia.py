from sqlalchemy import Column, Float, Index, Integer, String, Text

from app.database import Base


class DonGia(Base):
    __tablename__ = "don_gia"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mhdg = Column(String(25), nullable=False, index=True)
    tcv = Column(Text)
    dvt = Column(String(25))
    vlc = Column(Float, default=0)
    vlp = Column(Float, default=0)
    nc = Column(Float, default=0)
    mtc = Column(Float, default=0)
    mhdm = Column(String(25), index=True)
    plv = Column(String(25))
    tk = Column(Text)
    regulation_code = Column(String(25), nullable=False, index=True)
    db_type = Column(String(25), nullable=False)
    source = Column(String(50))


class DinhMuc(Base):
    __tablename__ = "dinh_muc"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mhdm = Column(String(25), nullable=False, index=True)
    msvt = Column(String(25), nullable=False, index=True)
    hao_phi = Column(Float, default=0)
    lvt = Column(String(10))
    gc = Column(String(10))
    regulation_code = Column(String(25), nullable=False)
    db_type = Column(String(25), nullable=False)


class TuDienVatTu(Base):
    __tablename__ = "tu_dien_vat_tu"

    id = Column(Integer, primary_key=True, autoincrement=True)
    msvt = Column(String(25), nullable=False, index=True)
    tvt = Column(Text)
    dvt = Column(String(25))
    gia_goc = Column(Float, default=0)
    lvt = Column(String(25))
    tlg = Column(String(25))
    hsbh = Column(String(25))
    regulation_code = Column(String(25), nullable=False)
    db_type = Column(String(25), nullable=False)
    source = Column(String(50))


class GiaCaMay(Base):
    __tablename__ = "gia_ca_may"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mh = Column(String(25), nullable=False, index=True)
    lm_tb = Column(Text)
    sc = Column(Float, default=0)
    dmkh = Column(Float, default=0)
    hsth = Column(Float, default=0)
    dmsc = Column(Float, default=0)
    dmcp = Column(Float, default=0)
    dmth = Column(Float, default=0)
    lnl = Column(String(255))
    hsnl = Column(Float, default=0)
    tpcb = Column(Text)
    cpkh = Column(Float, default=0)
    cpsc = Column(Float, default=0)
    cpk = Column(Float, default=0)
    cpnl = Column(Float, default=0)
    cptl = Column(Float, default=0)
    gcm = Column(Float, default=0)
    ngg = Column(Float, default=0)
    ngdc = Column(Float, default=0)
    ltdkm = Column(Text)
    ctnl = Column(Text)
    regulation_code = Column(String(25), nullable=False)
    db_type = Column(String(25), nullable=False)
    source = Column(String(50))


class PhuLucVua(Base):
    __tablename__ = "phu_luc_vua"

    id = Column(Integer, primary_key=True, autoincrement=True)
    btm = Column(String(25), nullable=False, index=True)
    tg = Column(Text)
    dvt = Column(String(25))
    mxm = Column(String(25))
    hpxm = Column(Float, default=0)
    cat = Column(String(25))
    hpc = Column(Float, default=0)
    da = Column(String(25))
    hpd = Column(Float, default=0)
    vcuc = Column(String(25))
    hpv = Column(Float, default=0)
    ma1 = Column(String(25))
    hp1 = Column(Float, default=0)
    ma2 = Column(String(25))
    hp2 = Column(Float, default=0)
    ma3 = Column(String(25))
    hp3 = Column(Float, default=0)
    ma4 = Column(String(25))
    hp4 = Column(Float, default=0)
    regulation_code = Column(String(25), nullable=False)
    db_type = Column(String(25), nullable=False)
