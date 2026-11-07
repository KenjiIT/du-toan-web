"""ORM models cho bảng chi phi van chuyen (CVC)."""

from sqlalchemy import Column, Integer, String

from app.database import Base


def _parse_vn_float(value: str | None) -> float:
    """Parse so thap phan kieu Viet (dau phay) thanh float."""
    if not value:
        return 0.0
    return float(value.replace(",", "."))


class CvcDmBocXep(Base):
    """Dinh muc boc xep."""

    __tablename__ = "cvc_dm_bocxep"

    Id = Column(String, primary_key=True)
    macv = Column(String)
    haophi = Column(String)

    @property
    def haophi_f(self) -> float:
        return _parse_vn_float(self.haophi)


class CvcDmMay(Base):
    """Dinh muc van chuyen co gioi."""

    __tablename__ = "cvc_dm_may"

    Id = Column(String, primary_key=True)
    vatlieu = Column(String)
    phuongtien = Column(String)
    culy = Column(String)
    loai = Column(String)
    haophi = Column(String)
    donvi = Column(String)
    quydoidv = Column(String)

    @property
    def haophi_f(self) -> float:
        return _parse_vn_float(self.haophi)

    @property
    def quydoidv_f(self) -> float:
        return _parse_vn_float(self.quydoidv)


class CvcDmThuCong(Base):
    """Dinh muc van chuyen thu cong."""

    __tablename__ = "cvc_dm_thucong"

    Id = Column(String, primary_key=True)
    nhomvatlieu = Column(String)
    culy = Column(String)
    haophi = Column(String)
    donvi = Column(String)
    quydoidv = Column(String)
    boclen = Column(String)
    bocxuong = Column(String)

    @property
    def haophi_f(self) -> float:
        return _parse_vn_float(self.haophi)

    @property
    def quydoidv_f(self) -> float:
        return _parse_vn_float(self.quydoidv)

    @property
    def boclen_f(self) -> float:
        return _parse_vn_float(self.boclen)

    @property
    def bocxuong_f(self) -> float:
        return _parse_vn_float(self.bocxuong)


class CvcHsDiaHinh(Base):
    """He so dia hinh."""

    __tablename__ = "cvc_hs_diahinh"

    Id = Column(String, primary_key=True)
    diahinh = Column(String)
    heso = Column(String)

    @property
    def heso_f(self) -> float:
        return _parse_vn_float(self.heso)


class CvcHsDoDoc(Base):
    """He so do doc."""

    __tablename__ = "cvc_hs_dodoc"

    Id = Column(String, primary_key=True)
    dodoc = Column(String)
    heso = Column(String)

    @property
    def heso_f(self) -> float:
        return _parse_vn_float(self.heso)


class CvcHsLoaiDuong(Base):
    """He so loai duong."""

    __tablename__ = "cvc_hs_loaiduong"

    Id = Column(String, primary_key=True)
    loaiduong = Column(String)
    heso = Column(String)

    @property
    def heso_f(self) -> float:
        return _parse_vn_float(self.heso)


class CvcMaMay(Base):
    """Ma may (ma phuong tien van chuyen)."""

    __tablename__ = "cvc_ma_may"

    Id = Column(String, primary_key=True)
    loaioto = Column(String)
    mamay = Column(String)
