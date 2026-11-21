# NYC public-data extraction

This folder contains a reproducible, read-only data retrieval pipeline for the NYC/MLC health-benefits research.

## Run

From the repository root:

```bash
python3 scenario-2/public-data/fetch_nyc_public_data.py
```

No API key or third-party Python package is required. The script reads public Socrata SODA endpoints, saves raw CSV extracts, saves the dataset metadata used to identify fields, and writes a retrieval manifest with timestamps and row counts.

Optional output directory:

```bash
python3 scenario-2/public-data/fetch_nyc_public_data.py --outdir /tmp/nyc-health-data
```

## Dataset register

| Dataset | ID | Intended use | Important limitation |
|---|---|---|---|
| Expense Budget, object code 062 | `mwzb-yiwb` | Object-code 062 budget trend | Budget, not actual spending; publications restate the budget and must not be summed across snapshots. |
| Expense Actuals | `7yay-m4ae` | Agency-level actual expense context | Not health-insurance-specific; data are rounded to thousands. |
| Expense Actuals By Funding Source | `nrik-v7ws` | Funding composition of agency actuals | Agency-level, not health-insurance-specific. |
| Additional Costs Allocation | `u42g-qjaj` | Central allocations including fringe benefits | Fringe benefits are broader than health insurance. Inspect category, fiscal year and actual/plan flag. |
| Financial Plan Baseline & Initiatives By Funding | `e64w-ctmw` | Identify health-related budget initiatives and planned savings | Financial-plan estimates are not realized savings. Preserve publication date and initiative type. |

## Why the extraction is deliberately conservative

The public Expense Actuals dataset is agency summary-level. It cannot be used to claim an actual health-insurance object-code series. The Expense Budget dataset does expose object-code detail, but those amounts are budget estimates, not actuals. The Additional Costs Allocation dataset includes fringe benefits, but fringe benefits include more than health insurance.

Accordingly, the raw extracts are evidence inputs, not a pre-labeled “health savings” series. A valid savings test still requires reconciling the 2018 agreement's counterfactual baseline, plan rates and membership, utilization/claims, equalization offsets, HISF transfers/liabilities, and independent actuarial calculations.

## Key public endpoints

- Expense Budget: https://data.cityofnewyork.us/resource/mwzb-yiwb.json
- Expense Actuals: https://data.cityofnewyork.us/resource/7yay-m4ae.json
- Expense Actuals By Funding Source: https://data.cityofnewyork.us/resource/nrik-v7ws.json
- Additional Costs Allocation: https://data.cityofnewyork.us/resource/u42g-qjaj.json
- Financial Plan Baseline & Initiatives: https://data.cityofnewyork.us/resource/e64w-ctmw.json

The retrieval script also saves each endpoint's current metadata, which should be treated as the schema record for that run.
