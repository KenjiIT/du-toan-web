"""SQLAlchemy model cho suat von dau tu."""

from sqlalchemy import Column, Float, Integer, String, Text

from app.database import Base


class SuatVonDauTu(Base):
    __tablename__ = "suat_von_dau_tu"

    id = Column(Integer, primary_key=True, autoincrement=True)
    loai_cong_trinh = Column(String(255))  # loai cong trinh
    don_vi = Column(String(50))  # don vi tinh (m2, m, ...)
    suat_von = Column(Float)  # suat von dau tu (VND/don vi)
    trong_do_xd = Column(Float)  # trong do: xay dung
    trong_do_tb = Column(Float)  # trong do: thiet bi
    nam = Column(Integer)  # nam ban hanh
    quyet_dinh = Column(String(100))  # so quyet dinh
    ghi_chu = Column(Text)  # ghi chu
