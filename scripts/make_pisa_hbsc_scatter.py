"""
Example pipeline for the KI4Forsking slide: PISA vs HBSC composites (European countries).

PISA 2022 mean scores are downloaded from Our World in Data (OECD PISA source).

HBSC: the 2021/22 international microdata are embargoed until 2026; open microdata exist
for 2017/18 via UiB after registration. For a quick, citable aggregate path, export country
means from the HBSC Data Browser (https://data-browser.hbsc.org) for the same three domains,
fill in ``data/hbsc_composite_europe.csv`` (ISO 3166-1 alpha-3, four columns, no fabricated
values), then run this script.

Dependencies: pip install pandas matplotlib
"""

from __future__ import annotations

import argparse
import io
import urllib.request
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

OWID_PISA_COMBINED = (
    "https://ourworldindata.org/grapher/"
    "average-performance-of-15-year-olds-in-mathematics-reading-and-science.csv"
)

# European ISO3 codes (broad: EU members, EEA, UK, CH; excludes microstates not in PISA/HBSC)
EUROPE_ISO3 = frozenset(
    {
        "ALB",
        "AND",
        "AUT",
        "BEL",
        "BGR",
        "BIH",
        "BLR",
        "CHE",
        "CYP",
        "CZE",
        "DEU",
        "DNK",
        "ESP",
        "EST",
        "FIN",
        "FRA",
        "GBR",
        "GRC",
        "HRV",
        "HUN",
        "IRL",
        "ISL",
        "ITA",
        "LTU",
        "LUX",
        "LVA",
        "MDA",
        "MKD",
        "MLT",
        "MNE",
        "NLD",
        "NOR",
        "POL",
        "PRT",
        "ROU",
        "SRB",
        "SVK",
        "SVN",
        "SWE",
        "UKR",
    }
)

NORDIC_ISO3 = frozenset({"DNK", "FIN", "ISL", "NOR", "SWE"})

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HBSC = REPO_ROOT / "data" / "hbsc_composite_europe.csv"
DEFAULT_FIG = REPO_ROOT / "figures" / "pisa_hbsc_composite_scatter.png"


def fetch_owid_csv(url: str) -> pd.DataFrame:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
    return pd.read_csv(io.BytesIO(raw))


def load_pisa_europe() -> pd.DataFrame:
    df = fetch_owid_csv(OWID_PISA_COMBINED)
    df = df.rename(columns={"Entity": "country", "Code": "alpha3"})
    df = df[df["Year"] == 2022].dropna(subset=["alpha3"])
    df = df[df["alpha3"].isin(EUROPE_ISO3)]
    df["pisa_composite"] = df[["Mathematics", "Science", "Reading"]].mean(axis=1)
    return df[["country", "alpha3", "pisa_composite"]]


def load_hbsc(path: Path) -> pd.DataFrame:
    """
    Expected columns: alpha3, life_satisfaction, who5_wellbeing, self_efficacy
    (country-level means; self_efficacy can be the mean of the two mandatory items.)
    """
    df = pd.read_csv(path)
    need = {"alpha3", "life_satisfaction", "who5_wellbeing", "self_efficacy"}
    missing = need - set(df.columns)
    if missing:
        raise ValueError(f"{path} missing columns: {sorted(missing)}")
    df = df.dropna(subset=list(need))
    if df.empty:
        raise ValueError(
            f"{path} has no complete rows. Add country means from the HBSC Data Browser "
            "(or open 2017/18 microdata) before plotting."
        )
    cols = ["life_satisfaction", "who5_wellbeing", "self_efficacy"]
    if len(df) < 2:
        df["hbsc_composite"] = df[cols].mean(axis=1)
    else:
        z = (df[cols] - df[cols].mean()) / df[cols].std(ddof=0)
        df["hbsc_composite"] = z.mean(axis=1)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--hbsc-csv",
        type=Path,
        default=DEFAULT_HBSC,
        help="CSV of HBSC country means (see module docstring).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_FIG,
        help="Output PNG path.",
    )
    args = parser.parse_args()

    pisa = load_pisa_europe()
    if not args.hbsc_csv.is_file():
        raise FileNotFoundError(
            f"Missing {args.hbsc_csv}. Export means from the HBSC Data Browser into this file."
        )
    hbsc = load_hbsc(args.hbsc_csv)
    merged = pisa.merge(hbsc, on="alpha3", how="inner")
    if merged.empty:
        raise ValueError(
            "No overlapping ISO3 codes between PISA and HBSC tables. "
            "Check that alpha3 uses standard codes (e.g. GBR not ENG)."
        )

    fig, ax = plt.subplots(figsize=(8, 6))
    other = merged[~merged["alpha3"].isin(NORDIC_ISO3)]
    nord = merged[merged["alpha3"].isin(NORDIC_ISO3)]

    ax.scatter(
        other["hbsc_composite"],
        other["pisa_composite"],
        c="#4c72b0",
        s=42,
        alpha=0.85,
        edgecolors="white",
        linewidths=0.4,
        label="Other Europe",
    )
    ax.scatter(
        nord["hbsc_composite"],
        nord["pisa_composite"],
        c="#c44e52",
        s=72,
        alpha=0.95,
        edgecolors="white",
        linewidths=0.5,
        label="Nordic",
    )
    for _, row in nord.iterrows():
        ax.annotate(
            row["country"],
            (row["hbsc_composite"], row["pisa_composite"]),
            textcoords="offset points",
            xytext=(6, 4),
            fontsize=8,
        )

    ax.set_xlabel(
        "HBSC composite (mean of z-scores: life satisfaction, WHO-5, self-efficacy)"
    )
    ax.set_ylabel("PISA 2022 composite (mean of mathematics, science, reading)")
    ax.set_title("European countries: adolescent well-being vs student achievement")
    ax.legend(loc="best", framealpha=0.9)
    ax.grid(True, linestyle=":", alpha=0.5)
    fig.tight_layout()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=150)
    plt.close(fig)
    print(f"Wrote {args.output} ({len(merged)} countries).")


if __name__ == "__main__":
    main()
