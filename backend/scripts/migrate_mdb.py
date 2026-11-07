# Migrate GXD Access databases (.mdb) to SQLite.
# Reads from Dulieu folder, writes to backend/data/dutoan.db
import sys
import io
import os
import re
import sqlite3
import glob as globmod

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import pyodbc

DULIEU = r"C:\Users\minhk\Downloads\Dulieu"
DB_OUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "dutoan.db")
DRIVER = "{Microsoft Access Driver (*.mdb, *.accdb)}"


def mdb_connect(path):
    return pyodbc.connect(f"DRIVER={DRIVER};DBQ={path};ExtendedAnsiSQL=1;")


def mdb_rows(conn, sql, params=None):
    cur = conn.cursor()
    cur.execute(sql, params or [])
    cols = [d[0] for d in cur.description]
    return cols, cur.fetchall()


def parse_float(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s:
        return None
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def mdb_tables(conn):
    cur = conn.cursor()
    return [t.table_name for t in cur.tables(tableType="TABLE")]


# ---------------------------------------------------------------------------
# Schema creation
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS regulations (
    id INTEGER PRIMARY KEY,
    code TEXT,
    name TEXT,
    description TEXT,
    sort_order INTEGER
);

CREATE TABLE IF NOT EXISTS regions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    category TEXT
);

CREATE TABLE IF NOT EXISTS cost_formula (
    id INTEGER PRIMARY KEY,
    name TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS don_gia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mhdg TEXT,
    tcv TEXT,
    dvt TEXT,
    vlc REAL,
    vlp REAL,
    nc REAL,
    mtc REAL,
    mhdm TEXT,
    plv TEXT,
    tk TEXT,
    regulation_code TEXT,
    db_type TEXT,
    source TEXT
);

CREATE TABLE IF NOT EXISTS dinh_muc (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mhdm TEXT,
    msvt TEXT,
    hao_phi REAL,
    lvt TEXT,
    gc TEXT,
    regulation_code TEXT,
    db_type TEXT
);

CREATE TABLE IF NOT EXISTS tu_dien_vat_tu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    msvt TEXT,
    tvt TEXT,
    dvt TEXT,
    gia_goc REAL,
    lvt TEXT,
    tlg REAL,
    hsbh REAL,
    regulation_code TEXT,
    db_type TEXT,
    source TEXT
);

CREATE TABLE IF NOT EXISTS gia_ca_may (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mh TEXT,
    lm_tb TEXT,
    sc REAL,
    dmkh REAL,
    hsth REAL,
    dmsc REAL,
    dmcp REAL,
    dmth REAL,
    lnl TEXT,
    hsnl REAL,
    tpcb TEXT,
    cpkh REAL,
    cpsc REAL,
    cpk REAL,
    cpnl REAL,
    cptl REAL,
    gcm REAL,
    ngg REAL,
    ngdc REAL,
    ltdkm TEXT,
    ctnl TEXT,
    regulation_code TEXT,
    db_type TEXT,
    source TEXT
);

CREATE TABLE IF NOT EXISTS phu_luc_vua (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    btm TEXT,
    tg TEXT,
    dvt TEXT,
    mxm TEXT,
    hpxm REAL,
    cat TEXT,
    hpc REAL,
    da TEXT,
    hpd REAL,
    vcuc TEXT,
    hpv REAL,
    ma1 TEXT,
    hp1 REAL,
    ma2 TEXT,
    hp2 REAL,
    ma3 TEXT,
    hp3 REAL,
    ma4 TEXT,
    hp4 REAL,
    regulation_code TEXT,
    db_type TEXT
);

CREATE TABLE IF NOT EXISTS nhan_cong (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT,
    ten TEXT,
    capbac TEXT,
    hslnd205 REAL,
    hsltt05 REAL,
    name_short TEXT,
    hsltt15 REAL,
    cbbq REAL,
    phanloai TEXT,
    tentt TEXT
);

CREATE TABLE IF NOT EXISTS thong_tin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ma_tt TEXT,
    ten_tt TEXT,
    source TEXT
);

CREATE TABLE IF NOT EXISTS gia_nhan_cong (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    region TEXT,
    decision_ref TEXT,
    ma_nc TEXT,
    nhom TEXT,
    khu_vuc_i REAL,
    khu_vuc_ii REAL,
    ghi_chu TEXT
);

CREATE TABLE IF NOT EXISTS gia_ca_may_vung (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    region TEXT,
    decision_ref TEXT,
    zone TEXT,
    mh TEXT,
    lm_tb TEXT,
    gcm REAL,
    cpkh REAL,
    cpsc REAL,
    cpk REAL,
    cpnl REAL,
    cptl REAL
);
"""

INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_don_gia_mhdg ON don_gia(mhdg);
CREATE INDEX IF NOT EXISTS idx_don_gia_mhdm ON don_gia(mhdm);
CREATE INDEX IF NOT EXISTS idx_don_gia_plv ON don_gia(plv);
CREATE INDEX IF NOT EXISTS idx_don_gia_reg_src ON don_gia(regulation_code, source);
CREATE INDEX IF NOT EXISTS idx_dinh_muc_mhdm ON dinh_muc(mhdm);
CREATE INDEX IF NOT EXISTS idx_dinh_muc_msvt ON dinh_muc(msvt);
CREATE INDEX IF NOT EXISTS idx_tu_dien_vat_tu_msvt ON tu_dien_vat_tu(msvt);
CREATE INDEX IF NOT EXISTS idx_gia_ca_may_mh ON gia_ca_may(mh);
CREATE INDEX IF NOT EXISTS idx_phu_luc_vua_btm ON phu_luc_vua(btm);
CREATE INDEX IF NOT EXISTS idx_gia_nhan_cong_region ON gia_nhan_cong(region);
CREATE INDEX IF NOT EXISTS idx_gia_ca_may_vung_region ON gia_ca_may_vung(region, zone);
"""


# ---------------------------------------------------------------------------
# Import helpers
# ---------------------------------------------------------------------------

def import_config(sdb):
    """Import Config.mdb: regulations, regions, cost_formula."""
    path = os.path.join(DULIEU, "Config.mdb")
    if not os.path.exists(path):
        print(f"  WARN: {path} not found, skipping config import")
        return
    conn = mdb_connect(path)

    # regulations from tblTemp
    try:
        _, rows = mdb_rows(conn, "SELECT * FROM tblTemp")
        for i, r in enumerate(rows):
            name_val = r[0] if len(r) > 0 else None
            noidung = r[1] if len(r) > 1 else None
            tenhienthi = r[2] if len(r) > 2 else None
            sort_val = r[3] if len(r) > 3 else i
            sdb.execute(
                "INSERT INTO regulations (id, code, name, description, sort_order) VALUES (?,?,?,?,?)",
                (i + 1, name_val, tenhienthi, noidung, sort_val),
            )
        print(f"  regulations: {len(rows)} rows")
    except Exception as e:
        print(f"  WARN regulations: {e}")

    # regions from tblListMdb
    try:
        _, rows = mdb_rows(conn, "SELECT Name, Nhom FROM tblListMdb")
        for r in rows:
            sdb.execute("INSERT INTO regions (name, category) VALUES (?,?)", (r[0], r[1]))
        print(f"  regions: {len(rows)} rows")
    except Exception as e:
        print(f"  WARN regions: {e}")

    # cost_formula from tblDefine
    try:
        _, rows = mdb_rows(conn, "SELECT ID, name, Des FROM tblDefine")
        for r in rows:
            sdb.execute(
                "INSERT INTO cost_formula (id, name, description) VALUES (?,?,?)",
                (r[0], r[1], r[2]),
            )
        print(f"  cost_formula: {len(rows)} rows")
    except Exception as e:
        print(f"  WARN cost_formula: {e}")

    conn.close()


def safe_col(conn, table, col):
    """Check if a column exists in the table."""
    cur = conn.cursor()
    cols = [c.column_name.upper() for c in cur.columns(table=table)]
    return col.upper() in cols


def import_norm_db(sdb, mdb_path, regulation_code, db_type, source="norm"):
    """Import the 7-table schema from a norm or regional DB."""
    if not os.path.exists(mdb_path):
        print(f"  SKIP (not found): {mdb_path}")
        return
    try:
        conn = mdb_connect(mdb_path)
    except Exception as e:
        print(f"  SKIP (connect error): {mdb_path}: {e}")
        return

    tables = mdb_tables(conn)
    label = os.path.basename(mdb_path)

    # tbDonGia
    if "tbDonGia" in tables:
        try:
            cols, rows = mdb_rows(conn, "SELECT * FROM tbDonGia")
            col_idx = {c.upper(): i for i, c in enumerate(cols)}

            def g(row, name):
                idx = col_idx.get(name.upper())
                return row[idx] if idx is not None else None

            count = 0
            for r in rows:
                sdb.execute(
                    "INSERT INTO don_gia (mhdg,tcv,dvt,vlc,vlp,nc,mtc,mhdm,plv,tk,regulation_code,db_type,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        g(r, "MHDG"), g(r, "TCV"), g(r, "DVT"),
                        parse_float(g(r, "VLC")), parse_float(g(r, "VLP")),
                        parse_float(g(r, "NC")), parse_float(g(r, "MTC")),
                        g(r, "MHDM"), g(r, "PLV"), g(r, "TK"),
                        regulation_code, db_type, source,
                    ),
                )
                count += 1
            print(f"  {label} tbDonGia: {count} rows")
        except Exception as e:
            print(f"  WARN {label} tbDonGia: {e}")

    # tbDinhMuc
    if "tbDinhMuc" in tables:
        try:
            cols, rows = mdb_rows(conn, "SELECT * FROM tbDinhMuc")
            col_idx = {c.upper(): i for i, c in enumerate(cols)}

            def g(row, name):
                idx = col_idx.get(name.upper())
                return row[idx] if idx is not None else None

            count = 0
            for r in rows:
                sdb.execute(
                    "INSERT INTO dinh_muc (mhdm,msvt,hao_phi,lvt,gc,regulation_code,db_type) VALUES (?,?,?,?,?,?,?)",
                    (
                        g(r, "MHDM"), g(r, "MSVT"),
                        parse_float(g(r, "HPVT")),
                        g(r, "LVT"), g(r, "GC"),
                        regulation_code, db_type,
                    ),
                )
                count += 1
            print(f"  {label} tbDinhMuc: {count} rows")
        except Exception as e:
            print(f"  WARN {label} tbDinhMuc: {e}")

    # tbTuDienVatTu
    if "tbTuDienVatTu" in tables:
        try:
            cols, rows = mdb_rows(conn, "SELECT * FROM tbTuDienVatTu")
            col_idx = {c.upper(): i for i, c in enumerate(cols)}

            def g(row, name):
                idx = col_idx.get(name.upper())
                return row[idx] if idx is not None else None

            count = 0
            for r in rows:
                sdb.execute(
                    "INSERT INTO tu_dien_vat_tu (msvt,tvt,dvt,gia_goc,lvt,tlg,hsbh,regulation_code,db_type,source) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (
                        g(r, "MSVT"), g(r, "TVT"), g(r, "DVT"),
                        parse_float(g(r, "GG")),
                        g(r, "LVT"),
                        parse_float(g(r, "TLG")),
                        parse_float(g(r, "HSBH")),
                        regulation_code, db_type, source,
                    ),
                )
                count += 1
            print(f"  {label} tbTuDienVatTu: {count} rows")
        except Exception as e:
            print(f"  WARN {label} tbTuDienVatTu: {e}")

    # tbGiaCaMay
    if "tbGiaCaMay" in tables:
        try:
            cols, rows = mdb_rows(conn, "SELECT * FROM tbGiaCaMay")
            col_idx = {c.upper(): i for i, c in enumerate(cols)}

            def g(row, name):
                idx = col_idx.get(name.upper())
                return row[idx] if idx is not None else None

            count = 0
            for r in rows:
                sdb.execute(
                    "INSERT INTO gia_ca_may (mh,lm_tb,sc,dmkh,hsth,dmsc,dmcp,dmth,lnl,hsnl,tpcb,cpkh,cpsc,cpk,cpnl,cptl,gcm,ngg,ngdc,ltdkm,ctnl,regulation_code,db_type,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        g(r, "MH"), g(r, "LM_TB"),
                        parse_float(g(r, "SC")), parse_float(g(r, "DMKH")),
                        parse_float(g(r, "HSTH")), parse_float(g(r, "DMSC")),
                        parse_float(g(r, "DMCP")), parse_float(g(r, "DMTH")),
                        g(r, "LNL"), parse_float(g(r, "HSNL")),
                        g(r, "TPCB"),
                        parse_float(g(r, "CPKH")), parse_float(g(r, "CPSC")),
                        parse_float(g(r, "CPK")), parse_float(g(r, "CPNL")),
                        parse_float(g(r, "CPTL")), parse_float(g(r, "GCM")),
                        parse_float(g(r, "NGG")), parse_float(g(r, "NGDC")),
                        g(r, "LTDKM"), g(r, "CTNL"),
                        regulation_code, db_type, source,
                    ),
                )
                count += 1
            print(f"  {label} tbGiaCaMay: {count} rows")
        except Exception as e:
            print(f"  WARN {label} tbGiaCaMay: {e}")

    # tbPhuLucVua
    if "tbPhuLucVua" in tables:
        try:
            cols, rows = mdb_rows(conn, "SELECT * FROM tbPhuLucVua")
            col_idx = {c.upper(): i for i, c in enumerate(cols)}

            def g(row, name):
                idx = col_idx.get(name.upper())
                return row[idx] if idx is not None else None

            count = 0
            for r in rows:
                sdb.execute(
                    "INSERT INTO phu_luc_vua (btm,tg,dvt,mxm,hpxm,cat,hpc,da,hpd,vcuc,hpv,ma1,hp1,ma2,hp2,ma3,hp3,ma4,hp4,regulation_code,db_type) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        g(r, "BTM"), g(r, "TG"), g(r, "DVT"),
                        g(r, "MXM"), parse_float(g(r, "HPXM")),
                        g(r, "CAT"), parse_float(g(r, "HPC")),
                        g(r, "DA"), parse_float(g(r, "HPD")),
                        g(r, "VCUC"), parse_float(g(r, "HPV")),
                        g(r, "MA1"), parse_float(g(r, "HP1")),
                        g(r, "MA2"), parse_float(g(r, "HP2")),
                        g(r, "MA3"), parse_float(g(r, "HP3")),
                        g(r, "MA4"), parse_float(g(r, "HP4")),
                        regulation_code, db_type,
                    ),
                )
                count += 1
            print(f"  {label} tbPhuLucVua: {count} rows")
        except Exception as e:
            print(f"  WARN {label} tbPhuLucVua: {e}")

    # tbThongTin (regional only)
    if source != "norm" and "tbThongTin" in tables:
        try:
            _, rows = mdb_rows(conn, "SELECT * FROM tbThongTin")
            for r in rows:
                ma_tt = r[1] if len(r) > 1 else None
                ten_tt = r[2] if len(r) > 2 else None
                sdb.execute(
                    "INSERT INTO thong_tin (ma_tt, ten_tt, source) VALUES (?,?,?)",
                    (ma_tt, ten_tt, source),
                )
            print(f"  {label} tbThongTin: {len(rows)} rows")
        except Exception as e:
            print(f"  WARN {label} tbThongTin: {e}")

    conn.close()


def import_nhancong(sdb):
    """Import CommonFiles/Nhancong.mdb."""
    path = os.path.join(DULIEU, "CommonFiles", "Nhancong.mdb")
    if not os.path.exists(path):
        print(f"  WARN: {path} not found")
        return
    conn = mdb_connect(path)
    try:
        cols, rows = mdb_rows(conn, "SELECT * FROM tblNhancong")
        col_idx = {c.upper(): i for i, c in enumerate(cols)}

        def g(row, name):
            idx = col_idx.get(name.upper())
            return row[idx] if idx is not None else None

        for r in rows:
            sdb.execute(
                "INSERT INTO nhan_cong (code,ten,capbac,hslnd205,hsltt05,name_short,hsltt15,cbbq,phanloai,tentt) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    g(r, "ID"), g(r, "TEN"), g(r, "CAPBAC"),
                    parse_float(g(r, "HSLND205")),
                    parse_float(g(r, "HSLTT05")),
                    g(r, "NAME"), parse_float(g(r, "HSLTT15")),
                    parse_float(g(r, "CBBQ")),
                    g(r, "PHANLOAI"), g(r, "TENTT"),
                ),
            )
        print(f"  nhan_cong: {len(rows)} rows")
    except Exception as e:
        print(f"  WARN nhan_cong: {e}")
    conn.close()


def import_cvc(sdb):
    """Import CommonFiles/CVC.mdb — all 7 tables as generic copies."""
    path = os.path.join(DULIEU, "CommonFiles", "CVC.mdb")
    if not os.path.exists(path):
        print(f"  WARN: {path} not found")
        return
    conn = mdb_connect(path)
    table_map = {
        "tblDmBocxep": "cvc_dm_bocxep",
        "tblDmMay": "cvc_dm_may",
        "tblDmThucong": "cvc_dm_thucong",
        "tblHsDiahinh": "cvc_hs_diahinh",
        "tblHsDodoc": "cvc_hs_dodoc",
        "tblHsLoaiduong": "cvc_hs_loaiduong",
        "tblMamay": "cvc_ma_may",
    }
    for src_table, dst_table in table_map.items():
        try:
            cols, rows = mdb_rows(conn, f"SELECT * FROM [{src_table}]")
            if not rows:
                print(f"  {dst_table}: 0 rows (empty)")
                continue
            col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
            sdb.execute(f'CREATE TABLE IF NOT EXISTS "{dst_table}" ({col_defs})')
            placeholders = ", ".join(["?"] * len(cols))
            for r in rows:
                sdb.execute(f'INSERT INTO "{dst_table}" VALUES ({placeholders})', list(r))
            print(f"  {dst_table}: {len(rows)} rows")
        except Exception as e:
            print(f"  WARN {dst_table}: {e}")
    conn.close()


def import_gnc(sdb, region_dir, region_name):
    """Import GNC/*.mdb labor wage files for a region."""
    gnc_dir = os.path.join(DULIEU, region_dir, "GNC")
    if not os.path.isdir(gnc_dir):
        print(f"  SKIP GNC (no dir): {gnc_dir}")
        return
    for mdb_file in globmod.glob(os.path.join(gnc_dir, "*.mdb")):
        fname = os.path.basename(mdb_file)
        try:
            conn = mdb_connect(mdb_file)
            tables = mdb_tables(conn)
            if "tbNhanCong" not in tables:
                conn.close()
                continue
            cols, rows = mdb_rows(conn, "SELECT * FROM tbNhanCong")
            col_idx = {c.upper(): i for i, c in enumerate(cols)}

            def g(row, name):
                idx = col_idx.get(name.upper())
                return row[idx] if idx is not None else None

            for r in rows:
                sdb.execute(
                    "INSERT INTO gia_nhan_cong (region,decision_ref,ma_nc,nhom,khu_vuc_i,khu_vuc_ii,ghi_chu) VALUES (?,?,?,?,?,?,?)",
                    (
                        region_name, fname,
                        g(r, "MANC") or g(r, "MaNC"),
                        g(r, "NHOM") or g(r, "Nhom"),
                        parse_float(g(r, "KHUVUCI") or g(r, "KhuvucI")),
                        parse_float(g(r, "KHUVUCII") or g(r, "KhuvucII")),
                        g(r, "GHICHU") or g(r, "Ghichu"),
                    ),
                )
            print(f"  GNC {fname}: {len(rows)} rows")
            conn.close()
        except Exception as e:
            print(f"  WARN GNC {fname}: {e}")


def import_gcm(sdb, region_dir, region_name):
    """Import GCM/*.mdb machine rate files for a region."""
    gcm_dir = os.path.join(DULIEU, region_dir, "GCM")
    if not os.path.isdir(gcm_dir):
        print(f"  SKIP GCM (no dir): {gcm_dir}")
        return
    for mdb_file in globmod.glob(os.path.join(gcm_dir, "*.mdb")):
        fname = os.path.basename(mdb_file)
        try:
            conn = mdb_connect(mdb_file)
            tables = mdb_tables(conn)
            for zone_suffix, zone_label in [("_KV_I", "I"), ("_KV_II", "II")]:
                tname = f"tbGiaCaMay{zone_suffix}"
                if tname not in tables:
                    continue
                cols, rows = mdb_rows(conn, f"SELECT * FROM [{tname}]")
                col_idx = {c.upper(): i for i, c in enumerate(cols)}

                def g(row, name):
                    idx = col_idx.get(name.upper())
                    return row[idx] if idx is not None else None

                for r in rows:
                    sdb.execute(
                        "INSERT INTO gia_ca_may_vung (region,decision_ref,zone,mh,lm_tb,gcm,cpkh,cpsc,cpk,cpnl,cptl) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            region_name, fname, zone_label,
                            g(r, "MH"), g(r, "LM_TB"),
                            parse_float(g(r, "GCM")),
                            parse_float(g(r, "CPKH")),
                            parse_float(g(r, "CPSC")),
                            parse_float(g(r, "CPK")),
                            parse_float(g(r, "CPNL")),
                            parse_float(g(r, "CPTL")),
                        ),
                    )
                print(f"  GCM {fname} zone {zone_label}: {len(rows)} rows")
            conn.close()
        except Exception as e:
            print(f"  WARN GCM {fname}: {e}")


def detect_db_type(filename):
    """Infer db_type from filename like HoChiMinh2023_XD+LD+SC_TT12-2021.mdb."""
    fn = filename.upper()
    if "XD+LD+SC" in fn or "XD_LD_SC" in fn:
        return "XD+LD+SC"
    if "_KS_" in fn or "_KS." in fn:
        return "KS"
    if "_LDM_" in fn or "_LDM." in fn:
        return "LDM"
    if "_TNVL_" in fn or "_TNVL." in fn:
        return "TNVL"
    return "XD+LD+SC"


def detect_regulation(filename):
    fn = filename.upper()
    if "TT38" in fn:
        return "TT38-2026"
    return "TT12-2021"


def source_label(filename):
    """Extract a human label like 'HoChiMinh2023' from filename."""
    base = os.path.splitext(filename)[0]
    parts = base.split("_")
    return parts[0] if parts else base


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    os.makedirs(os.path.dirname(DB_OUT), exist_ok=True)
    if os.path.exists(DB_OUT):
        os.remove(DB_OUT)
    sdb = sqlite3.connect(DB_OUT)
    sdb.execute("PRAGMA journal_mode=WAL")
    sdb.execute("PRAGMA synchronous=NORMAL")
    sdb.executescript(SCHEMA_SQL)
    sdb.commit()

    # 1. Config
    print("=== Importing Config.mdb ===")
    import_config(sdb)
    sdb.commit()

    # 2. Norm databases
    norm_dbs = [
        ("12_2021_DM", "BXD_XD+LD+SC_TT12-2021.mdb", "TT12-2021", "XD+LD+SC"),
        ("12_2021_DM", "BXD_KS_TT12-2021.mdb", "TT12-2021", "KS"),
        ("12_2021_DM", "BXD_LDM_TT12-2021.mdb", "TT12-2021", "LDM"),
        ("12_2021_DM", "BXD_TNVL_TT12-2021.mdb", "TT12-2021", "TNVL"),
        ("38_2026_DM", "BXD_XD+LD+SC_TT38-2026.mdb", "TT38-2026", "XD+LD+SC"),
        ("38_2026_DM", "BXD_KS_TT38-2026.mdb", "TT38-2026", "KS"),
        ("38_2026_DM", "BXD_LDM_TT38-2026.mdb", "TT38-2026", "LDM"),
        ("38_2026_DM", "BXD_TNVL_TT38-2026.mdb", "TT38-2026", "TNVL"),
    ]
    for folder, fname, reg, dbt in norm_dbs:
        path = os.path.join(DULIEU, folder, fname)
        print(f"\n=== Norm: {folder}/{fname} ===")
        import_norm_db(sdb, path, reg, dbt, source="norm")
        sdb.commit()

    # 3. Regional databases (HoChiMinh, HaNoi — top-level .mdb files only)
    for region_dir in ["HoChiMinh", "HaNoi"]:
        region_path = os.path.join(DULIEU, region_dir)
        if not os.path.isdir(region_path):
            continue
        for mdb_file in globmod.glob(os.path.join(region_path, "*.mdb")):
            fname = os.path.basename(mdb_file)
            # skip GNC/GCM subdirs
            if "GNC" in mdb_file or "GCM" in mdb_file:
                continue
            dbt = detect_db_type(fname)
            reg = detect_regulation(fname)
            src = source_label(fname)
            print(f"\n=== Regional: {region_dir}/{fname} ===")
            import_norm_db(sdb, mdb_file, reg, dbt, source=src)
            sdb.commit()

    # 4. Nhancong
    print("\n=== Importing Nhancong.mdb ===")
    import_nhancong(sdb)
    sdb.commit()

    # 5. CVC
    print("\n=== Importing CVC.mdb ===")
    import_cvc(sdb)
    sdb.commit()

    # 6. GNC (labor wages)
    for region_dir, region_name in [("HoChiMinh", "HoChiMinh"), ("HaNoi", "HaNoi")]:
        print(f"\n=== GNC: {region_dir} ===")
        import_gnc(sdb, region_dir, region_name)
        sdb.commit()

    # 7. GCM (machine rates)
    for region_dir, region_name in [("HoChiMinh", "HoChiMinh"), ("HaNoi", "HaNoi")]:
        print(f"\n=== GCM: {region_dir} ===")
        import_gcm(sdb, region_dir, region_name)
        sdb.commit()

    # 8. Create indexes
    print("\n=== Creating indexes ===")
    sdb.executescript(INDEX_SQL)
    sdb.commit()

    # 9. Create FTS5 virtual table
    print("=== Creating FTS5 search index ===")
    try:
        sdb.execute("DROP TABLE IF EXISTS don_gia_fts")
        sdb.execute(
            "CREATE VIRTUAL TABLE don_gia_fts USING fts5(mhdg, tcv, tk, content=don_gia, content_rowid=id)"
        )
        sdb.execute(
            "INSERT INTO don_gia_fts(rowid, mhdg, tcv, tk) SELECT id, mhdg, tcv, tk FROM don_gia"
        )
        sdb.commit()
        count = sdb.execute("SELECT COUNT(*) FROM don_gia_fts").fetchone()[0]
        print(f"  FTS5 index: {count} rows")
    except Exception as e:
        print(f"  WARN FTS5: {e}")

    # 10. Print summary
    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE — Row counts:")
    print("=" * 60)
    for table in [
        "regulations", "regions", "cost_formula",
        "don_gia", "dinh_muc", "tu_dien_vat_tu",
        "gia_ca_may", "phu_luc_vua", "nhan_cong",
        "thong_tin", "gia_nhan_cong", "gia_ca_may_vung",
    ]:
        try:
            cnt = sdb.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
            print(f"  {table}: {cnt:,}")
        except Exception:
            print(f"  {table}: (not found)")

    # CVC tables
    for table in ["cvc_dm_bocxep", "cvc_dm_may", "cvc_dm_thucong",
                   "cvc_hs_diahinh", "cvc_hs_dodoc", "cvc_hs_loaiduong", "cvc_ma_may"]:
        try:
            cnt = sdb.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
            print(f"  {table}: {cnt}")
        except Exception:
            pass

    db_size = os.path.getsize(DB_OUT) / (1024 * 1024)
    print(f"\nDatabase size: {db_size:.1f} MB")
    print(f"Database path: {DB_OUT}")

    sdb.close()


if __name__ == "__main__":
    main()
