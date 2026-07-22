#!/usr/bin/env python3
"""Build the Import Localization Atlas country datasets.

The expensive BACI scan and aggregation runs in DuckDB; pandas is used only for
the much smaller country-level scoring pass. BACI values are thousands of USD.
The published methodology uses the 2022-2023 mean of reported positive flows,
so a year with no BACI row remains missing rather than being imputed as zero.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any, Iterable

import duckdb
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DEFAULT_YEARS = (2022, 2023)
MIN_CHINA_USD = 200_000_000
MIN_PRODUCTS = 30
MATERIAL_USD = 5_000_000
DEFAULT_WEIGHTS = np.array([0.417, 0.250, 0.333], dtype=float)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baci-dir", type=Path, default=ROOT / "baci")
    parser.add_argument("--support-dir", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs" / "data")
    parser.add_argument("--index-file", type=Path, default=ROOT / "docs" / "index.json")
    parser.add_argument("--years", type=int, nargs="+", default=list(DEFAULT_YEARS))
    parser.add_argument(
        "--countries",
        nargs="+",
        metavar="ISO3",
        help="build only these ISO3 countries (useful for parity checks)",
    )
    parser.add_argument("--min-china-usd", type=float, default=MIN_CHINA_USD)
    return parser.parse_args()


def _one_match(directory: Path, pattern: str, label: str) -> Path:
    matches = sorted(directory.glob(pattern))
    if len(matches) != 1:
        raise FileNotFoundError(
            f"Expected exactly one {label} matching {directory / pattern}; found {len(matches)}"
        )
    return matches[0]


def ensure_baci_files(baci_dir: Path, years: Iterable[int]) -> list[Path]:
    """Return annual BACI files, extracting only required members when needed."""
    baci_dir.mkdir(parents=True, exist_ok=True)
    years = list(dict.fromkeys(years))
    files: list[Path] = []
    missing: list[int] = []
    for year in years:
        matches = sorted(baci_dir.glob(f"BACI_HS22_Y{year}_V*.csv"))
        if len(matches) == 1:
            files.append(matches[0])
        elif matches:
            raise FileExistsError(f"Multiple BACI files found for {year}: {matches}")
        else:
            missing.append(year)

    if missing:
        archive = _one_match(baci_dir, "BACI_HS22_V*.zip", "BACI archive")
        print(f"Extracting BACI years {', '.join(map(str, missing))} from {archive.name}...")
        with zipfile.ZipFile(archive) as source:
            members = {Path(name).name: name for name in source.namelist()}
            for year in missing:
                candidates = [name for name in members if name.startswith(f"BACI_HS22_Y{year}_V")]
                if len(candidates) != 1:
                    raise FileNotFoundError(
                        f"Expected one BACI CSV for {year} in {archive}; found {len(candidates)}"
                    )
                basename = candidates[0]
                target = baci_dir / basename
                with source.open(members[basename]) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)

        return ensure_baci_files(baci_dir, years)

    by_year = {int(path.name.split("_Y", 1)[1][:4]): path for path in files}
    return [by_year[year] for year in years]


def load_country_reference(baci_dir: Path) -> tuple[int, dict[int, str], dict[int, str]]:
    path = _one_match(baci_dir, "country_codes_V*.csv", "country-code file")
    countries = pd.read_csv(path)
    countries.columns = [str(column).lower() for column in countries.columns]
    iso_column = (
        "country_iso3"
        if "country_iso3" in countries
        else next(column for column in countries if "iso3" in column)
    )
    name_column = (
        "country_name"
        if "country_name" in countries
        else next(column for column in countries if "name" in column)
    )
    code_column = (
        "country_code"
        if "country_code" in countries
        else countries.columns[0]
    )
    countries[code_column] = pd.to_numeric(countries[code_column], errors="raise").astype(int)
    countries[iso_column] = countries[iso_column].astype("string")
    china = countries.loc[countries[iso_column] == "CHN", code_column]
    if len(china) != 1:
        raise ValueError(f"Expected one CHN row in {path}; found {len(china)}")
    code_to_iso = dict(zip(countries[code_column], countries[iso_column]))
    code_to_name = dict(zip(countries[code_column], countries[name_column]))
    return int(china.iloc[0]), code_to_iso, code_to_name


def aggregate_trade(files: list[Path], china_code: int) -> pd.DataFrame:
    """Aggregate annual world/China flows with the published missing-year semantics."""
    started = time.perf_counter()
    connection = duckdb.connect()
    connection.execute("SET preserve_insertion_order = false")
    relation = connection.read_csv(
        [str(path) for path in files],
        header=True,
        columns={
            "t": "INTEGER",
            "i": "INTEGER",
            "j": "INTEGER",
            "k": "VARCHAR",
            "v": "DOUBLE",
            "q": "DOUBLE",
        },
    )
    relation.create_view("baci_flows")
    query = """
        WITH annual AS (
            SELECT
                t,
                j,
                CAST(k AS INTEGER) AS k,
                SUM(v) AS world_value,
                SUM(v) FILTER (WHERE i = ?) AS china_value
            FROM baci_flows
            GROUP BY t, j, k
        )
        SELECT
            j,
            k,
            GREATEST(AVG(world_value), COALESCE(AVG(china_value), 0.0)) * 1000.0
                AS M_world,
            COALESCE(AVG(china_value), 0.0) * 1000.0 AS M_china
        FROM annual
        GROUP BY j, k
        ORDER BY j, k
    """
    result = connection.execute(query, [china_code]).fetch_df()
    connection.close()
    print(
        f"DuckDB aggregated {sum(path.stat().st_size for path in files) / 1e6:,.0f} MB "
        f"into {len(result):,} importer-product rows in {time.perf_counter() - started:,.1f}s"
    )
    result["j"] = result["j"].astype("int32")
    result["k"] = result["k"].astype("int32")
    result["hs6"] = result["k"].astype(str).str.zfill(6)
    return result


def _require_unique(frame: pd.DataFrame, key: str, label: str) -> None:
    duplicates = frame.loc[frame[key].duplicated(), key].head().tolist()
    if duplicates:
        raise ValueError(f"Duplicate {label} keys in {key}: {duplicates}")


def add_product_reference(trade: pd.DataFrame, support_dir: Path) -> pd.DataFrame:
    pci = pd.read_csv(support_dir / "pci_hs6.csv", dtype={"hs6": str})
    pci4 = pd.read_csv(support_dir / "pci_hs4_fallback.csv", dtype={"hs4": str})
    codes = pd.read_csv(support_dir / "hs6_codes.csv", dtype=str)
    required = {
        "pci_hs6.csv": (pci, {"hs6", "pci", "product_name"}),
        "pci_hs4_fallback.csv": (pci4, {"hs4", "pci_hs4"}),
        "hs6_codes.csv": (codes, {"hs6", "chapter", "desc"}),
    }
    for label, (frame, columns) in required.items():
        missing = columns.difference(frame.columns)
        if missing:
            raise ValueError(f"{label} is missing columns: {sorted(missing)}")

    pci["hs6"] = pci["hs6"].str.zfill(6)
    pci4["hs4"] = pci4["hs4"].str.zfill(4)
    codes["hs6"] = codes["hs6"].str.zfill(6)
    _require_unique(pci, "hs6", "PCI HS6")
    _require_unique(pci4, "hs4", "PCI HS4")
    _require_unique(codes, "hs6", "HS2022")
    pci["pci"] = pd.to_numeric(pci["pci"], errors="raise")
    pci4["pci_hs4"] = pd.to_numeric(pci4["pci_hs4"], errors="raise")
    codes["desc"] = codes["desc"].str.replace(r"^[0-9]+ - ", "", regex=True)

    pci_map = pci.set_index("hs6")["pci"]
    pci_name_map = pci.set_index("hs6")["product_name"]
    pci4_map = pci4.set_index("hs4")["pci_hs4"]
    code_index = codes.set_index("hs6")

    result = trade.copy()
    exact_pci = result["hs6"].map(pci_map)
    fallback_pci = result["hs6"].str[:4].map(pci4_map)
    result["PCI"] = exact_pci.fillna(fallback_pci)
    result["pci_source"] = np.select(
        [exact_pci.notna(), fallback_pci.notna()], [6, 4], default=0
    ).astype("int8")
    # Labels must follow the data's HS2022 vintage. OEC names are only a last-resort
    # fallback where the HS2022 reference lacks a description.
    result["name"] = result["hs6"].map(code_index["desc"]).fillna(
        result["hs6"].map(pci_name_map)
    )
    result["name"] = result["name"].fillna(result["hs6"])
    result["chapter"] = result["hs6"].map(code_index["chapter"]).fillna(
        result["hs6"].str[:2]
    )
    return result


def winsorize(series: pd.Series) -> pd.Series:
    """Clip non-null observations at the linear 1st/99th percentiles."""
    if not series.notna().any():
        return series.astype(float)
    lower, upper = series.quantile([0.01, 0.99]).tolist()
    return series.clip(lower, upper)


def minmax_100(series: pd.Series) -> pd.Series:
    """Min-max normalize to 0-100; map a constant non-null series to its midpoint."""
    valid = series.dropna()
    if valid.empty:
        return pd.Series(np.nan, index=series.index, dtype=float)
    lower, upper = valid.min(), valid.max()
    if not math.isfinite(lower) or not math.isfinite(upper):
        raise ValueError("Cannot normalize a series containing non-finite values")
    if upper <= lower:
        return pd.Series(np.where(series.notna(), 50.0, np.nan), index=series.index)
    return 100.0 * (series - lower) / (upper - lower)


def score_country(frame: pd.DataFrame) -> pd.DataFrame:
    """Apply country-relative winsorization, normalization, and composite scoring."""
    result = frame.copy()
    with np.errstate(divide="ignore", invalid="ignore"):
        result["D"] = np.where(
            result["M_world"] > 0,
            result["M_china"] / result["M_world"],
            np.nan,
        )
    result["D"] = result["D"].clip(0.0, 1.0)
    result["logM"] = np.log10(result["M_china"].clip(lower=1.0))
    result["zD"] = minmax_100(winsorize(result["D"]))
    result["zS"] = minmax_100(winsorize(result["logM"]))
    result["zC"] = minmax_100(winsorize(result["PCI"]))

    indicators = result[["zD", "zS", "zC"]].to_numpy(dtype=float)
    present = ~np.isnan(indicators)
    denominator = present @ DEFAULT_WEIGHTS
    numerator = np.nan_to_num(indicators, nan=0.0) @ DEFAULT_WEIGHTS
    result["CPS"] = np.divide(
        numerator,
        denominator,
        out=np.full_like(numerator, np.nan),
        where=denominator > 0,
    )
    result["EXP"] = 0.6 * result["zD"] + 0.4 * result["zS"]
    result["SOPH"] = result["zC"]
    return result


def _rounded(value: Any, digits: int) -> float | None:
    return None if pd.isna(value) else round(float(value), digits)


def make_records(frame: pd.DataFrame) -> list[list[Any]]:
    """Serialize compact records; fields 0-11 retain the published schema.

    Fields 12-14 add precise world imports ($m), PCI bridge source (6, 4, or 0),
    and precise China imports ($m). The original display field at index 3 stays
    unchanged so published scores and values remain backward-compatible.
    """
    columns = [
        "hs6",
        "name",
        "chapter",
        "M_china",
        "D",
        "PCI",
        "zD",
        "zS",
        "zC",
        "EXP",
        "SOPH",
        "M_world",
        "pci_source",
    ]
    records: list[list[Any]] = []
    for row in frame[columns].itertuples(index=False, name=None):
        (
            hs6,
            name,
            chapter,
            china_value,
            dependence,
            pci,
            z_dependence,
            z_scale,
            z_complexity,
            exposure,
            sophistication,
            world_value,
            pci_source,
        ) = row
        records.append(
            [
                hs6,
                str(name),
                str(chapter).zfill(2),
                _rounded(china_value / 1e6, 1),
                _rounded(dependence * 100.0, 1),
                _rounded(pci, 2),
                _rounded(z_dependence, 3),
                _rounded(z_scale, 3),
                _rounded(z_complexity, 3),
                _rounded(exposure, 3),
                _rounded(sophistication, 3),
                1 if china_value > MATERIAL_USD else 0,
                _rounded(world_value / 1e6, 6),
                int(pci_source),
                _rounded(china_value / 1e6, 6),
            ]
        )
    return records


def write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            os.fchmod(handle.fileno(), 0o644)
            json.dump(
                payload,
                handle,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            )
            handle.write("\n")
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def build_datasets(
    trade: pd.DataFrame,
    code_to_iso: dict[int, str],
    code_to_name: dict[int, str],
    output_dir: Path,
    selected_countries: set[str] | None,
    min_china_usd: float,
) -> list[dict[str, Any]]:
    index: list[dict[str, Any]] = []
    started = time.perf_counter()
    for importer, country_frame in trade.groupby("j", sort=True):
        iso_value = code_to_iso.get(int(importer))
        if not isinstance(iso_value, str) or pd.isna(iso_value):
            continue
        iso = str(iso_value).upper()
        if selected_countries is not None and iso not in selected_countries:
            continue
        china_total = float(country_frame["M_china"].sum())
        if china_total < min_china_usd:
            continue
        products = country_frame.loc[country_frame["M_china"] > 0].copy()
        if len(products) < MIN_PRODUCTS:
            continue

        products = score_country(products).sort_values(
            ["CPS", "hs6"], ascending=[False, True], kind="mergesort"
        )
        records = make_records(products)
        write_json_atomic(output_dir / f"{iso}.json", records)
        # The browser classifies the compact, three-decimal serialized values.
        # Derive the index count from those same values so a 59.9996 value that
        # serializes to 60.000 cannot make the index and tool disagree.
        n_localize = sum(
            record[9] is not None
            and record[9] >= 60.0
            and record[10] is not None
            and record[10] >= 60.0
            for record in records
        )
        missing_complexity = products["SOPH"].isna()
        world_total = float(country_frame["M_world"].sum())
        pci_coverage = 100.0 * float(products["PCI"].notna().mean())
        name_value = code_to_name.get(int(importer), iso)
        name = iso if pd.isna(name_value) else str(name_value)
        index.append(
            {
                "iso": iso,
                "name": name,
                "china_bn": round(china_total / 1e9, 2),
                "n": len(products),
                "nA": n_localize,
                "nU": int(missing_complexity.sum()),
                "share": round(100.0 * china_total / world_total) if world_total > 0 else None,
                "pci_coverage": round(pci_coverage, 1),
            }
        )

    index.sort(key=lambda item: (-item["china_bn"], item["iso"]))
    print(f"Scored and wrote {len(index)} countries in {time.perf_counter() - started:,.1f}s")
    return index


def main() -> None:
    args = parse_args()
    if len(args.years) < 1:
        raise ValueError("At least one BACI year is required")
    selected = {iso.upper() for iso in args.countries} if args.countries else None
    started = time.perf_counter()
    files = ensure_baci_files(args.baci_dir, args.years)
    china_code, code_to_iso, code_to_name = load_country_reference(args.baci_dir)
    print(f"China BACI code: {china_code}; years: {', '.join(map(str, args.years))}")
    trade = aggregate_trade(files, china_code)
    trade = add_product_reference(trade, args.support_dir)
    index = build_datasets(
        trade,
        code_to_iso,
        code_to_name,
        args.output_dir,
        selected,
        args.min_china_usd,
    )
    if selected:
        missing = selected.difference(item["iso"] for item in index)
        if missing:
            raise ValueError(f"Requested countries were not eligible or found: {sorted(missing)}")
    write_json_atomic(args.index_file, index)
    top = ", ".join(f"{item['iso']}({item['china_bn']:.0f}b)" for item in index[:8])
    print(
        f"Wrote {len(index)} country files and {args.index_file}. Top: {top}. "
        f"Total time {time.perf_counter() - started:,.1f}s"
    )


if __name__ == "__main__":
    main()
