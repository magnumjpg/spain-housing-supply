"""Download and cache the public source data.

Usage:
    python src/download_data.py [--force]

All files are cached under data/raw/. A manifest with URL, size, sha256 and
download timestamp is written to data/raw/manifest.json. Re-running without
--force is a no-op, so the analysis pipeline works offline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from config import RAW, SIU, URLS, USER_AGENT

MANIFEST = RAW / "manifest.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path, force: bool = False) -> Path:
    if dest.exists() and dest.stat().st_size > 0 and not force:
        print(f"  cached  {dest.name} ({dest.stat().st_size:,} bytes)")
        return dest
    print(f"  get     {url}")
    headers = {"User-Agent": USER_AGENT}
    with requests.get(url, headers=headers, stream=True, timeout=180) as r:
        r.raise_for_status()
        tmp = dest.with_suffix(dest.suffix + ".part")
        with tmp.open("wb") as fh:
            for chunk in r.iter_content(1 << 20):
                fh.write(chunk)
        tmp.replace(dest)
    print(f"  saved   {dest.name} ({dest.stat().st_size:,} bytes)")
    return dest


def fetch_ua_codes(force: bool = False) -> Path:
    """Municipality names -> 5-digit INE codes.

    The CSV download of table 69330 has names but no codes. The Tempus JSON
    carries the code in the metadata; we cache a small lookup table.
    """
    dest = RAW / "ua_municipality_codes.csv"
    if dest.exists() and not force:
        print(f"  cached  {dest.name}")
        return dest
    print("  get     INE Tempus metadata (municipality codes)")
    r = requests.get(URLS["ua_codes_json"], headers={"User-Agent": USER_AGENT}, timeout=180)
    r.raise_for_status()
    rows = []
    for rec in r.json():
        md = {m["T3_Variable"]: m for m in rec.get("MetaData", [])}
        t = md.get("Municipios")
        if t:
            rows.append({"name": t["Nombre"], "tempus_code": t["Codigo"]})
    df = pd.DataFrame(rows).drop_duplicates()
    df.to_csv(dest, index=False, encoding="utf-8")
    print(f"  saved   {dest.name} ({len(df)} rows)")
    return dest


def extract_siu(zip_path: Path, force: bool = False) -> None:
    needed = {"clases_suelo_mun.xlsx", "areas_desarrollo_mun.xlsx", "plan_mun.xlsx"}
    if not force and all((SIU / n).exists() for n in needed):
        print("  cached  SIU workbooks")
        return
    print("  unzip   SIU alphanumeric workbook")
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.namelist():
            name = Path(member).name
            if name.endswith(".xlsx"):
                with zf.open(member) as src, (SIU / name).open("wb") as dst:
                    dst.write(src.read())


def main(force: bool = False) -> int:
    print("Downloading public data")
    files = {}
    files["siu_zip"] = download(URLS["siu_zip"], RAW / "siu_alpha.zip", force)
    extract_siu(files["siu_zip"], force)

    for key in ("ua_69330", "ipva_59060", "dpop_29005"):
        files[key] = download(URLS[key], RAW / f"{key}.csv", force)

    # SERPAVI is a 71 MB multi-sheet workbook; only the 2024 municipality sheet
    # is used, but the whole file is kept so the provenance is a single object.
    files["serpavi"] = download(URLS["serpavi"], RAW / "serpavi_2011_2024.xlsx", force)

    files["ua_codes"] = fetch_ua_codes(force)

    # Comparative chapter. The Eurostat queries are filtered at the API so the
    # cached files stay small; the filters are part of the URL in config.py.
    comparative_files = {
        "oecd_house_prices": "oecd_house_prices.csv",
        "eurostat_permits": "eurostat_permits.json",
        "eurostat_population": "eurostat_population.json",
        "eurostat_urban_audit": "eurostat_urban_audit.json",
    }
    for key, filename in comparative_files.items():
        files[key] = download(URLS[key], RAW / filename, force)

    manifest = {}
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for key, path in files.items():
        manifest[key] = {
            "path": str(path.relative_to(RAW.parent.parent)),
            "url": URLS.get(key, URLS["ua_codes_json"] if key == "ua_codes" else ""),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "downloaded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    for name in sorted(p.name for p in SIU.glob("*.xlsx")):
        path = SIU / name
        manifest[f"siu_{name}"] = {
            "path": str(path.relative_to(RAW.parent.parent)),
            "url": URLS["siu_zip"],
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "downloaded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Manifest written to {MANIFEST}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="re-download even if cached")
    args = ap.parse_args()
    sys.exit(main(force=args.force))
