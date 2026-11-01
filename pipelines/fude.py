"""農林水産省の筆ポリゴンを都道府県ごとの Parquet にする。

「地域の農業を見て・知って・活かすDB」の筆ポリゴンデータのページにある、
都道府県ごとの分割 zip（MB0001_<公開年度>_<センサス年>_<都道府県>.zip.001, .002, …）を取る。
分割 zip はつなぐと 1 つの zip になり、中に FlatGeobuf が 1 つ入っている。
全国で zip が 5.4GB、FlatGeobuf が約 13GB あるので、都道府県ごとに
取る → つなぐ → 展開 → Parquet にする → zip と FlatGeobuf を消す、を順に回す。
Parquet が既にある都道府県は取り直さない。

出力: data/maff/fude/<都道府県コード>.parquet（形は WKB）
"""

import logging
import os
import re
import shutil
import zipfile
from itertools import groupby
from pathlib import Path

import duckdb

from shared.fetch import download, fetch, replacing

logger = logging.getLogger("pipelines")

PAGE_URL = "https://www.maff.go.jp/j/tokei/census/shuraku_data/2025/mb/index.html"
PART = re.compile(r'href="(https://[^"]+/MB0001_\d{4}_\d{4}_(\d{2})\.zip\.\d{3})"')
OUT = Path("data/maff/fude")
WORK = Path("data/maff/work")


def list_parts(html: str) -> dict[str, list[str]]:
    """ページの HTML から、都道府県コードごとの分割 zip の URL（番号順）を返す。"""
    found = sorted({(m[2], m[1]) for m in PART.finditer(html)})
    return {pref: [url for _, url in parts] for pref, parts in groupby(found, key=lambda p: p[0])}


def selected(prefs: list[str]) -> list[str]:
    wanted = os.environ.get("MAFF_PREFECTURES")
    return [p for p in prefs if not wanted or p in wanted.split(",")]


def fetch_zip(urls: list[str], path: Path) -> Path:
    """分割 zip を順に取ってつなぎ、1 つの zip にする。"""
    part = path.with_suffix(".part.zip")
    with path.open("wb") as joined:
        for url in urls:
            download(url, part)
            with part.open("rb") as handle:
                shutil.copyfileobj(handle, joined)
            part.unlink()
    return path


def extract_fgb(archive: Path) -> Path:
    with zipfile.ZipFile(archive) as z:
        name = next(n for n in z.namelist() if n.endswith(".fgb"))
        z.extract(name, archive.parent)
    archive.unlink()
    return archive.parent / name


def write_parquet(fgb: Path, path: Path) -> int:
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial")
    with replacing(path) as partial:
        con.execute(
            f"""
            COPY (
                SELECT polygon_uuid, land_type, issue_year, point_lng, point_lat, key,
                       st_aswkb(geom) AS geometry
                FROM st_read('{fgb.as_posix()}')
            ) TO '{partial.as_posix()}' (FORMAT parquet, COMPRESSION zstd)
            """
        )
    fgb.unlink()
    return con.execute(f"SELECT count(*) FROM '{path.as_posix()}'").fetchone()[0]


def build_prefecture(pref: str, urls: list[str]) -> None:
    path = OUT / f"{pref}.parquet"
    if path.exists():
        logger.info("  %s: 取得済み", pref)
        return
    WORK.mkdir(parents=True, exist_ok=True)
    rows = write_parquet(extract_fgb(fetch_zip(urls, WORK / f"{pref}.zip")), path)
    logger.info("  %s: %d 区画（分割 %d）", pref, rows, len(urls))


def download_fude() -> None:
    parts = list_parts(fetch(PAGE_URL).decode("utf-8"))
    if len(parts) != 47:
        raise RuntimeError(f"都道府県の数が 47 ではない: {len(parts)}")
    OUT.mkdir(parents=True, exist_ok=True)
    for pref in selected(sorted(parts)):
        build_prefecture(pref, parts[pref])
