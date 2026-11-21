# Scenario 1 — Three-Year Fringe Benefits Analysis

## Objective

Prepare a decision-ready pivot-style summary of City fringe-benefit spending by the three-digit object code for the three fiscal years ending in FY 2021. The intended audience understands major fringe-benefit categories but may not know the City's object-code numbering.

## Required source workbook

Save the supplied workbook as `source_data.xlsx` in this directory. It should contain:
- The transaction-level data for the three fiscal years.
- The `Reference` tab mapping three-digit object codes to descriptions.

The prompt identifies the object code as column H. The script defaults to Excel column H for object code, and attempts to identify the fiscal-year, amount, and closing-class columns by header. If those headers are unusual, pass their exact names as command-line options.

## Definition of spending

Include only the three closing-class groupings specified in the assignment:
- Encumbrances (noting that they lapse at fiscal year-end)
- Accruals
- Cash expenses

The script includes rows matching those classes, sums the supplied expenditure amount as recorded, and retains the closing-class detail in the supporting data. It does not net, annualize, or otherwise alter amounts. Confirm that the source's sign convention represents expenditures as positive values; if not, resolve that before presenting results.

## Growth calculations

For each object-code category and the total:
- FY-over-FY growth = (current-year spending / prior-year spending) − 1.
- Annual average growth rate across FY 2019–FY 2021 = two-year CAGR = (FY 2021 / FY 2019)^(1/2) − 1.

CAGR is used as the annualized rate over the two intervals between three fiscal-year observations. If the FY 2019 base is zero or negative, CAGR is shown as not meaningful rather than forcing a misleading percentage. Year-over-year rates are also shown separately so that a one-year spike is visible.

## Run

From the repository root:

```bash
python -m pip install -r requirements.txt
python scenario-1/build_analysis.py scenario-1/source_data.xlsx --output scenario-1/fringe_benefits_analysis.xlsx
```

If the source headers are not detected automatically:

```bash
python scenario-1/build_analysis.py scenario-1/source_data.xlsx \
  --fy-col "Fiscal Year" \
  --amount-col "Amount" \
  --class-col "Closing Class" \
  --object-col H \
  --output scenario-1/fringe_benefits_analysis.xlsx
```

The object-code argument may be an exact header or an Excel column letter such as H.

## Workbook output

The generated workbook contains:
1. **Pivot Summary** — object-code description rows and fiscal-year spending columns, with a grand total.
2. **Growth Rates** — annual dollar and percentage changes, plus FY 2019–FY 2021 CAGR.
3. **Data QA** — source row counts, included/excluded closing classes, unmapped object codes, fiscal years, and reconciliation checks.
4. **Included Detail** — source rows retained for the calculation.
5. **Reference** — the supplied object-code mapping.

The summary is a reproducible pivot-style aggregation rather than a native Excel PivotTable object. It is a stable, refreshable summary suitable for briefing and review.

## Key-finding paragraph — completion template

Replace the bracketed fields only after running the source data:

> City fringe-benefit spending across the three fiscal years increased from **$[FY19]** in FY 2019 to **$[FY21]** in FY 2021, an annualized growth rate of **[X]%**. The largest spending category was **[category]**, which accounted for **[X]%** of FY 2021 spending and changed by **[X]%** over the period. The most significant movement occurred in **[category/year]**, where spending changed by **$[X] ([X]%)**. These results include encumbrances, accruals, and cash expenses as directed; because encumbrances lapse at year-end, the figures should be understood as the City's defined spending measure rather than cash disbursements alone. The principal items for follow-up are **[unusual trend / classification / one-time item]**.

## Review checks before briefing

- Confirm the three fiscal years are exactly FY 2019, FY 2020, and FY 2021 (or update the CAGR interpretation if the source years differ).
- Reconcile the pivot grand total to the included detail total for each year.
- Confirm all object codes map to the Reference tab; investigate any unmapped code rather than silently dropping it.
- Confirm all three closing classes are included and other classes are excluded.
- Inspect large year-over-year changes for one-time accruals, encumbrance timing, reclassifications, and changes in employee/retiree benefit costs.
- Distinguish nominal spending growth from per-employee or inflation-adjusted growth; the assignment asks for total spending, not a normalized measure.
