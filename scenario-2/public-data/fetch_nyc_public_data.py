#!/usr/bin/env python3
"""Download reproducible NYC public finance extracts for the health-benefits review.

Uses public Socrata SODA endpoints; no API token or third-party package is required.
The script intentionally does not infer actual health-insurance costs from agency-level
expense actuals. Object code 062 is extracted from the Expense Budget dataset as a
budget series only. Run:
    python3 scenario-2/public-data/fetch_nyc_public_data.py
"""
from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://data.cityofnewyork.us"
DATASETS = {
    "expense_budget_object_062": {
        "id": "mwzb-yiwb",
        "description": "Expense Budget rows for object code 062 (budget, not actual expenditure).",
        "where": "object_code = '062'",
        "order": "fiscal_year, publication_date",
    },
    "expense_actuals_agency": {
        "id": "7yay-m4ae",
        "description": "Agency-level expense actuals; not health-insurance-specific.",
        "where": None,
        "order": "fisc_yr, agy_cd",
    },
    "expense_actuals_by_funding": {
        "id": "nrik-v7ws",
        "description": "Agency actual expenditures by funding source; not health-insurance-specific.",
        "where": None,
        "order": "fisc_yr, agy_cd, fnding",
    },
    "additional_costs_allocation": {
        "id": "u42g-qjaj",
        "description": "Central additional-cost allocations including fringe benefits; inspect cost category before interpreting.",
        "where": None,
        "order": "fisc_yr, cst_cat, agy_cd",
    },
    "financial_plan_initiatives": {
        "id": "e64w-ctmw",
        "description": "OMB financial-plan baseline and initiatives; retain publication date and initiative type.",
        "where": None,
        "order": "pub_date, fiscal_year, init_type",
    },
}

USER_AGENT = "OSCEXAM-public-data-research/1.0 (reproducible public-record analysis)"


def get_json(url: str, retries: int = 4):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def get_metadata(dataset_id: str):
    return get_json(f"{BASE}/api/views/{dataset_id}.json")


def api_field_names(metadata):
    return {c.get("fieldName") for c in metadata.get("columns", []) if c.get("fieldName")}


def download_rows(dataset_id: str, where: str | None, order: str | None, page_size: int = 50000):
    rows = []
    offset = 0
    while True:
        params = {"$limit": str(page_size), "$offset": str(offset)}
        if where:
            params["$where"] = where
        if order:
            params["$order"] = order
        url = f"{BASE}/resource/{dataset_id}.json?{urllib.parse.urlencode(params)}"
        batch = get_json(url)
        if not isinstance(batch, list):
            raise RuntimeError(f"Unexpected API response for {dataset_id}: {batch}")
        rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size
    return rows


def write_csv(path: Path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    # Preserve a stable union of fields if the API returns sparse records.
    fields = list(dict.fromkeys(key for row in rows for key in row.keys()))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)



def write_object_062_annual(rows, outpath: Path):
    """Aggregate object-code 062 budget to one adopted-snapshot amount per FY.

    OMB's June publication tagged fiscal_year=Y contains the financial_plan_amount
    for FY Y. The API dataset repeats/revises snapshots, so keep the latest
    publication_date within each fiscal_year before summing.
    """
    if not rows:
        return
    required = {"fiscal_year", "publication_date", "financial_plan_amount"}
    missing = required.difference(rows[0].keys())
    if missing:
        raise RuntimeError(
            "Cannot create annual object-code 062 series; missing fields: "
            + ", ".join(sorted(missing))
        )
    latest = {}
    for row in rows:
        year = str(row.get("fiscal_year", ""))
        pub = str(row.get("publication_date", ""))
        if not year or not pub:
            continue
        if year not in latest or pub > latest[year]:
            latest[year] = pub
    totals = {}
    names = {}
    for row in rows:
        year = str(row.get("fiscal_year", ""))
        if not year or str(row.get("publication_date", "")) != latest.get(year):
            continue
        amount = row.get("financial_plan_amount")
        if amount in (None, ""):
            continue
        totals[year] = totals.get(year, 0.0) + float(amount)
        names[year] = row.get("object_code_name", "Object code 062")
    annual = [
        {
            "fiscal_year": year,
            "object_code": "062",
            "object_code_name": names.get(year, "Object code 062"),
            "adopted_budget_amount_usd": round(totals[year], 2),
            "publication_date": latest[year],
            "measure": "adopted budget; not actual expenditure",
        }
        for year in sorted(totals, key=int)
    ]
    write_csv(outpath, annual)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default="scenario-2/public-data/raw", help="Output directory")
    args = parser.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "api_root": BASE,
        "authentication": "No token used; public Socrata SODA endpoints",
        "datasets": {},
        "caveats": [
            "Expense Budget object code 062 is a budget series, not actual expenditures.",
            "Expense Actuals and Expense Actuals By Funding Source are agency-level aggregates, not health-insurance-specific.",
            "Additional Costs Allocation includes centrally allocated fringe-benefit costs; do not label the entire fringe category as health insurance.",
            "Financial-plan initiatives are plans/estimates and must not be described as realized savings without independent support.",
            "For the Expense Budget dataset, each publication restates the budget. Use one publication snapshot per fiscal year and inspect the year/amount field semantics before aggregation.",
        ],
    }

    for name, config in DATASETS.items():
        dataset_id = config["id"]
        print(f"Fetching metadata: {name} ({dataset_id})", flush=True)
        metadata = get_metadata(dataset_id)
        available = api_field_names(metadata)
        where = config["where"]
        if name == "expense_budget_object_062" and "object_code" not in available:
            raise RuntimeError("Expected object_code field was not present in Expense Budget metadata; refusing an unfiltered download.")
        if where and any(field not in available for field in ("object_code",)):
            raise RuntimeError(f"Filter references an unavailable field in {dataset_id}: {where}")

        print(f"Fetching rows: {name}", flush=True)
        rows = download_rows(dataset_id, where, config["order"])
        csv_path = outdir / f"{name}.csv"
        write_csv(csv_path, rows)
        metadata_path = outdir / f"{name}.metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        manifest["datasets"][name] = {
            "dataset_id": dataset_id,
            "title": metadata.get("name"),
            "description": config["description"],
            "rows_downloaded": len(rows),
            "csv": csv_path.name,
            "metadata": metadata_path.name,
            "fields": sorted(available),
            "source_url": f"{BASE}/resource/{dataset_id}.json",
            "where": where,
            "order": config["order"],
        }
        print(f"Saved {len(rows):,} rows -> {csv_path}", flush=True)

        if name == "expense_budget_object_062":
            annual_path = outdir / "object_062_adopted_budget_by_fy.csv"
            write_object_062_annual(rows, annual_path)
            manifest["datasets"][name]["annual_aggregation"] = {
                "csv": annual_path.name,
                "method": "latest publication_date within each fiscal_year; sum financial_plan_amount",
                "interpretation": "Adopted budget for the fiscal year named in fiscal_year; not actual spending",
            }

        if name == "financial_plan_initiatives":
            keywords = ("health", "medical", "insurance", "benefit", "stabilization", "medicare", "ppo", "prescription")
            matched = [
                row for row in rows
                if any(word in " ".join(str(value) for value in row.values()).lower() for word in keywords)
            ]
            matched_path = outdir / "financial_plan_health_related_initiatives.csv"
            write_csv(matched_path, matched)
            manifest["datasets"][name]["keyword_extract"] = {
                "csv": matched_path.name,
                "rows_downloaded": len(matched),
                "keywords": list(keywords),
                "note": "Search aid only; review initiative descriptions and do not treat planned amounts as realized savings.",
            }

    (outdir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Manifest written: {outdir / 'manifest.json'}")


if __name__ == "__main__":
    main()
