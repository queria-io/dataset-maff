"""農林水産省の筆ポリゴンを都道府県ごとの Parquet にする。

「地域の農業を見て・知って・活かすDB」の筆ポリゴンデータのページにある、
都道府県ごとの分割 zip（MB0001_<公開年度>_<センサス年>_<都道府県>.zip.001, .002, …）を取る。
分割 zip はつなぐと 1 つの zip になり、中に FlatGeobuf が 1 つ入っている。
全国で zip が 5.4GB、FlatGeobuf が約 13GB あるので、都道府県ごとに
取る → つなぐ → 展開 → Parquet にする → zip と FlatGeobuf を消す、を順に回す。
Parquet と取得の記録が既にある都道府県は取り直さない。

取得の記録（source_file の行）は、分割ファイルごとの行と、つないだ zip の行（url は NULL）を
data/maff/fude/source_file.ndjson に書く。筆の行はつないだ zip の sha256 を指す。

出力: data/maff/fude/<都道府県コード>.parquet（形は WKB）、data/maff/fude/source_file.ndjson
"""

import hashlib
import json
import logging
import os
import re
import zipfile
from datetime import UTC, datetime
from itertools import groupby
from pathlib import Path

import duckdb

from shared.fetch import fetch, fetch_file, replacing, write_atomic

logger = logging.getLogger("pipelines")

PAGE_URL = "https://www.maff.go.jp/j/tokei/census/shuraku_data/2025/mb/index.html"
PART = re.compile(r'href="(https://[^"]+/MB0001_\d{4}_\d{4}_(\d{2})\.zip\.\d{3})"')
OUT = Path("data/maff/fude")
WORK = Path("data/maff/work")
SOURCE_FILES = OUT / "source_file.ndjson"


def list_parts(html: str) -> dict[str, list[str]]:
    """ページの HTML から、都道府県コードごとの分割 zip の URL（番号順）を返す。"""
    found = sorted({(m[2], m[1]) for m in PART.finditer(html)})
    return {pref: [url for _, url in parts] for pref, parts in groupby(found, key=lambda p: p[0])}


def selected(prefs: list[str]) -> list[str]:
    wanted = os.environ.get("MAFF_PREFECTURES")
    return [p for p in prefs if not wanted or p in wanted.split(",")]


def fetch_zip(urls: list[str], path: Path) -> tuple[Path, list[dict]]:
    """分割 zip を順に取ってつなぎ、1 つの zip にする。分割ファイルとつないだ zip の取得の記録を返す。"""
    part = path.with_suffix(".part.zip")
    records = []
    joined_hash = hashlib.sha256()
    with path.open("wb") as joined:
        for url in urls:
            record = fetch_file(url, part)
            records.append({"file": url.rsplit("/", 1)[1], "page_url": PAGE_URL, **record})
            with part.open("rb") as handle:
                while block := handle.read(1 << 20):
                    joined.write(block)
                    joined_hash.update(block)
            part.unlink()
    name = urls[0].rsplit("/", 1)[1].rsplit(".", 1)[0]
    records.append(
        {
            "file": name,
            "url": None,
            "page_url": PAGE_URL,
            "sha256": joined_hash.hexdigest(),
            "bytes": path.stat().st_size,
            "media_type": "application/zip",
            "retrieved_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "etag": None,
            "last_modified": None,
        }
    )
    return path, records


def read_records() -> dict[str, list[dict]]:
    """都道府県コード → その都道府県の取得の記録。"""
    if not SOURCE_FILES.exists():
        return {}
    rows = [json.loads(line) for line in SOURCE_FILES.read_text().splitlines()]
    return {pref: [r for r in rows if r["prefecture_code"] == pref] for pref in {r["prefecture_code"] for r in rows}}


def write_records(records: dict[str, list[dict]]) -> None:
    lines = "".join(json.dumps(r, ensure_ascii=False) + "\n" for pref in sorted(records) for r in records[pref])
    write_atomic(SOURCE_FILES, lines.encode())


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


def build_prefecture(pref: str, urls: list[str], records: dict[str, list[dict]]) -> None:
    path = OUT / f"{pref}.parquet"
    if path.exists() and pref in records:
        logger.info("  %s: 取得済み", pref)
        return
    WORK.mkdir(parents=True, exist_ok=True)
    archive, fetched = fetch_zip(urls, WORK / f"{pref}.zip")
    rows = write_parquet(extract_fgb(archive), path)
    records[pref] = [{"prefecture_code": pref, **r} for r in fetched]
    # 途中で止まっても、取り込んだ都道府県を次の実行で取り直さない
    write_records(records)
    logger.info("  %s: %d 区画（分割 %d）", pref, rows, len(urls))


def download_fude() -> None:
    parts = list_parts(fetch(PAGE_URL).decode("utf-8"))
    if len(parts) != 47:
        raise RuntimeError(f"都道府県の数が 47 ではない: {len(parts)}")
    OUT.mkdir(parents=True, exist_ok=True)
    records = read_records()
    for pref in selected(sorted(parts)):
        build_prefecture(pref, parts[pref], records)
