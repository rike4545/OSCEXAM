#!/usr/bin/env python3
"""Build a reproducible fringe-benefit pivot-style workbook from the City's source XLSX."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


INCLUDED_CLASS_TERMS = {
    "encumbrance",
    "encumbrances",
    "accrual",
    "accruals",
    "cash expense",
    "cash expenses",
}
REFERENCE_SHEET_CANDIDATES = ("Reference", "reference")


def norm(value: object) -> str:
    return re.sub(r"\s+", " ", str(value).strip().lower())


def excel_col_index(letter: str) -> int:
    """Convert Excel column letters (A, H, AA) to a zero-based index."""
    result = 0
    for char in letter.upper():
        if not ("A" <= char <= "Z"):
            raise ValueError(f"Invalid Excel column letter: {letter}")
        result = result * 26 + ord(char) - ord("A") + 1
    return result - 1


def resolve_column(df: pd.DataFrame, requested: str | None, role: str,
                   candidates: tuple[str, ...], default_letter: str | None = None) -> str:
    if requested:
        if requested in df.columns:
            return requested
        if re.fullmatch(r"[A-Za-z]+", requested):
            idx = excel_col_index(requested)
            if idx < len(df.columns):
                return str(df.columns[idx])
        raise ValueError(f"Could not resolve {role} column {requested!r}. Available: {list(df.columns)}")

    normalized = {norm(c): c for c in df.columns}
    for candidate in candidates:
        if norm(candidate) in normalized:
            return str(normalized[norm(candidate)])
    if default_letter:
        idx = excel_col_index(default_letter)
        if idx < len(df.columns):
            return str(df.columns[idx])
    raise ValueError(
        f"Could not identify {role} column. Pass it explicitly. Available: {list(df.columns)}"
    )


def find_reference_sheet(xls: pd.ExcelFile) -> str:
    for candidate in REFERENCE_SHEET_CANDIDATES:
        if candidate in xls.sheet_names:
            return candidate
    for name in xls.sheet_names:
        if norm(name) == "reference":
            return name
    raise ValueError("Workbook must contain a sheet named 'Reference'.")


def build(input_path: Path, output_path: Path, sheet: str | None,
          fy_arg: str | None, amount_arg: str | None,
          class_arg: str | None, object_arg: str | None) -> None:
    xls = pd.ExcelFile(input_path)
    data_sheet = sheet or next((s for s in xls.sheet_names if norm(s) != "reference"), xls.sheet_names[0])
    raw = pd.read_excel(input_path, sheet_name=data_sheet)
    reference_sheet = find_reference_sheet(xls)
    reference = pd.read_excel(input_path, sheet_name=reference_sheet)

    fy_col = resolve_column(
        raw, fy_arg, "fiscal year",
        ("Fiscal Year", "Fiscal Year Code", "FY", "Year"), None
    )
    amount_col = resolve_column(
        raw, amount_arg, "amount",
        ("Amount", "Transaction Amount", "Accounting Amount", "Actual Amount", "Debit Amount"), None
    )
    class_col = resolve_column(
        raw, class_arg, "closing class",
        ("Closing Class", "Closing Class Description", "Closing Class Name", "Class"), None
    )
    object_col = resolve_column(
        raw, object_arg, "object code",
        ("Object Code", "Object", "Obj Code"), "H"
    )

    # Resolve the two reference fields conservatively; do not guess if ambiguous.
    ref_cols = list(reference.columns)
    code_candidates = [c for c in ref_cols if norm(c) in {"object code", "object", "obj code", "code"}]
    desc_candidates = [c for c in ref_cols if norm(c) in {"description", "object description", "object code description", "name"}]
    if not code_candidates or not desc_candidates:
        raise ValueError(
            "Reference tab needs recognizable object-code and description headers. "
            f"Found: {ref_cols}"
        )
    ref_code, ref_desc = code_candidates[0], desc_candidates[0]

    data = raw.copy()
    data["_object_code"] = data[object_col].astype(str).str.extract(r"(\d{3})", expand=False)
    data["_fiscal_year"] = data[fy_col].astype(str).str.extract(r"(20\d{2})", expand=False)
    data["_amount"] = pd.to_numeric(data[amount_col], errors="coerce")
    data["_closing_class_norm"] = data[class_col].map(norm)

    if data["_amount"].isna().any():
        bad = int(data["_amount"].isna().sum())
        raise ValueError(f"{bad} rows have blank or non-numeric amounts in {amount_col!r}. Resolve before analysis.")
    if data["_object_code"].isna().any():
        bad = int(data["_object_code"].isna().sum())
        raise ValueError(f"{bad} rows do not contain a three-digit object code in {object_col!r}.")
    if data["_fiscal_year"].isna().any():
        bad = int(data["_fiscal_year"].isna().sum())
        raise ValueError(f"{bad} rows do not contain a four-digit fiscal year in {fy_col!r}.")

    include = data["_closing_class_norm"].isin(INCLUDED_CLASS_TERMS)
    included = data.loc[include].copy()
    excluded = data.loc[~include].copy()
    if included.empty:
        classes = sorted(data[class_col].dropna().astype(str).unique().tolist())
        raise ValueError(f"No rows matched the three required closing classes. Source values: {classes}")

    years = sorted(included["_fiscal_year"].unique())
    if len(years) != 3:
        raise ValueError(f"Expected exactly three fiscal years; found {years}.")
    if years[-1] != "2021":
        print(f"WARNING: latest year is {years[-1]}, not FY 2021.", file=sys.stderr)

    reference["_object_code"] = reference[ref_code].astype(str).str.extract(r"(\d{3})", expand=False)
    reference["_description"] = reference[ref_desc].astype(str).str.strip()
    ref_map = (
        reference.dropna(subset=["_object_code"])
        .drop_duplicates("_object_code")
        .set_index("_object_code")["_description"]
        .to_dict()
    )
    included["_description"] = included["_object_code"].map(ref_map).fillna("UNMAPPED — REVIEW")
    unmapped = sorted(included.loc[included["_description"] == "UNMAPPED — REVIEW", "_object_code"].unique())

    pivot = included.pivot_table(
        index=["_object_code", "_description"],
        columns="_fiscal_year",
        values="_amount",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()
    for year in years:
        if year not in pivot.columns:
            pivot[year] = 0
    pivot = pivot[["_object_code", "_description", *years]].sort_values(["_object_code"])
    pivot = pivot.rename(columns={"_object_code": "Object Code", "_description": "Fringe Benefit Category"})
    pivot["Three-Year Total"] = pivot[years].sum(axis=1)

    total_row = {"Object Code": "", "Fringe Benefit Category": "TOTAL"}
    total_row.update({year: pivot[year].sum() for year in years})
    total_row["Three-Year Total"] = sum(total_row[y] for y in years)
    pivot = pd.concat([pivot, pd.DataFrame([total_row])], ignore_index=True)

    growth_rows = []
    for _, row in pivot.iterrows():
        label = "TOTAL" if row["Fringe Benefit Category"] == "TOTAL" else f'{row["Object Code"]} — {row["Fringe Benefit Category"]}'
        vals = [float(row[y]) for y in years]
        growth_rows.append({
            "Object Code / Category": label,
            f"{years[0]} Spending": vals[0],
            f"{years[1]} Spending": vals[1],
            f"{years[2]} Spending": vals[2],
            f"{years[1]} $ Change": vals[1] - vals[0],
            f"{years[1]} YoY Growth": (vals[1] / vals[0] - 1) if vals[0] else None,
            f"{years[2]} $ Change": vals[2] - vals[1],
            f"{years[2]} YoY Growth": (vals[2] / vals[1] - 1) if vals[1] else None,
            "FY19–FY21 CAGR": ((vals[2] / vals[0]) ** (1 / 2) - 1) if vals[0] > 0 and vals[2] >= 0 else None,
        })
    growth = pd.DataFrame(growth_rows)

    qa = pd.DataFrame([
        ("Source file", str(input_path)),
        ("Transaction sheet", data_sheet),
        ("Reference sheet", reference_sheet),
        ("Fiscal years included", ", ".join(years)),
        ("Source rows", len(raw)),
        ("Included rows (encumbrances, accruals, cash expenses)", len(included)),
        ("Excluded rows (other closing classes)", len(excluded)),
        ("Included spending total", included["_amount"].sum()),
        ("Unmapped object codes", ", ".join(unmapped) if unmapped else "None"),
        ("Source closing-class values", "; ".join(sorted(data[class_col].dropna().astype(str).unique()))),
        ("Reconciliation", "Pivot grand total equals included-detail sum by construction; validate each year below."),
    ], columns=["Check", "Result"])
    year_recon = included.groupby("_fiscal_year")["_amount"].sum().rename("Included Detail Total").to_frame()
    pivot_recon = included.pivot_table(index="_fiscal_year", values="_amount", aggfunc="sum").rename(columns={"_amount": "Pivot Total"})
    recon = year_recon.join(pivot_recon, how="outer").reset_index().rename(columns={"_fiscal_year": "Fiscal Year"})
    recon["Difference"] = recon["Included Detail Total"] - recon["Pivot Total"]

    detail = included.drop(columns=["_closing_class_norm"])
    detail = detail.rename(columns={
        "_object_code": "Parsed Object Code",
        "_fiscal_year": "Parsed Fiscal Year",
        "_amount": "Parsed Amount",
        "_description": "Reference Description",
    })

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        pivot.to_excel(writer, sheet_name="Pivot Summary", index=False)
        growth.to_excel(writer, sheet_name="Growth Rates", index=False)
        qa.to_excel(writer, sheet_name="Data QA", index=False)
        recon.to_excel(writer, sheet_name="Reconciliation", index=False)
        detail.to_excel(writer, sheet_name="Included Detail", index=False)
        reference.to_excel(writer, sheet_name="Reference", index=False)
        excluded.to_excel(writer, sheet_name="Excluded Classes", index=False)

        wb = writer.book
        for ws in wb.worksheets:
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for cell in ws[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="263B53")
                cell.alignment = Alignment(wrap_text=True, vertical="center")
            ws.row_dimensions[1].height = 30
            for col_cells in ws.columns:
                letter = get_column_letter(col_cells[0].column)
                max_len = max((len(str(c.value)) if c.value is not None else 0) for c in col_cells[:200])
                ws.column_dimensions[letter].width = min(max(max_len + 2, 12), 48)
            for row in ws.iter_rows(min_row=2):
                for cell in row:
                    if isinstance(cell.value, float):
                        cell.number_format = '#,##0.00;[Red](#,##0.00);-'
        for ws_name in ("Growth Rates",):
            ws = wb[ws_name]
            for row in ws.iter_rows(min_row=2):
                for cell in row:
                    if "Growth" in str(ws.cell(1, cell.column).value) or "CAGR" in str(ws.cell(1, cell.column).value):
                        cell.number_format = "0.0%;[Red](0.0%);-"

    print(f"Created {output_path}")
    print(f"Included {len(included):,} of {len(raw):,} rows across FY {', '.join(years)}.")
    if unmapped:
        print("REVIEW REQUIRED — unmapped object codes: " + ", ".join(unmapped))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Source City workbook (.xlsx)")
    parser.add_argument("--output", type=Path, default=Path("fringe_benefits_analysis.xlsx"))
    parser.add_argument("--sheet", help="Transaction sheet name; defaults to first non-Reference sheet")
    parser.add_argument("--fy-col", help="Fiscal-year column header or Excel column letter")
    parser.add_argument("--amount-col", help="Spending amount column header or Excel column letter")
    parser.add_argument("--class-col", help="Closing-class column header or Excel column letter")
    parser.add_argument("--object-col", default="H", help="Object-code column header or Excel column letter (default: H)")
    args = parser.parse_args()
    build(args.input, args.output, args.sheet, args.fy_col, args.amount_col, args.class_col, args.object_col)


if __name__ == "__main__":
    main()
