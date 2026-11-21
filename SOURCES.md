# Sources, definitions, and assumptions

## Scenario 1 — Fringe benefits

- Primary source: the three-year City transaction workbook referenced in the assignment, including its `Reference` tab. **Not yet received in this conversation.**
- Object code: three-digit code in source column H, per the assignment.
- Spending measure: include encumbrances, accruals, and cash expenses. Encumbrances lapse at fiscal year-end; do not describe the resulting total as cash paid.
- Growth: report year-over-year growth and two-year CAGR from the first to third year. CAGR is undefined for a zero or negative starting amount; flag those cases.

## Scenario 2 — Health Benefits Agreement

- City of New York Office of Labor Relations, letter agreement dated June 28, 2018, *Health Benefits Agreement — Fiscal Years 2019–2021*: https://www.nyc.gov/assets/olr/downloads/pdf/collectivebargaining/health-benefits-agreement-fiscal-years-2019-2021.pdf
- New York City Comptroller, *Audit of the Financial and Operating Practices of the Joint Health Insurance Stabilization Fund*, FK24-070A, December 30, 2025: https://comptroller.nyc.gov/wp-content/uploads/documents/FK24-070A.pdf
- New York City Comptroller, *Health Care Costs: The Hidden Risks in the Financial Plan*, Fiscal Note 3-2025, June 2025: https://comptroller.nyc.gov/wp-content/uploads/documents/fn_hidden_risks_final.pdf
- New York City Comptroller, *Annual Comprehensive Financial Report for Fiscal Years Ended June 30, 2026 and 2025*, issued October 30, 2026: https://comptroller.nyc.gov/wp-content/uploads/documents/ACFR-2026.pdf
- New York City Comptroller, *Annual State of the City's Economy and Finances 2025*, December 15, 2025: https://comptroller.nyc.gov/reports/annual-state-of-the-citys-economy-and-finances-2025/

### Interpretation

The 2018 HBA's $600 million recurring annual savings commitment, the separate Medicare Advantage initiative projected at $600 million annually, and the later NYCE PPO savings projection (up to $900 million–$1 billion annually) are distinct figures and must not be conflated.

The December 2025 audit's statement that recurring savings were not independently verified refers specifically to the $303.5 million recurring savings commitment under the **2014** agreement. It does not provide a definitive independent actuarial determination that the **2018** agreement's $600 million recurring commitment was missed. The audit does identify HISF insolvency, unreported liabilities, and offsets that eroded the Fund; these are important evidence about the accounting and sustainability of the overall arrangement.

The FY 2026 ACFR records a $937 million write-down of HISF receivables accrued in FY 2020–FY 2022, $969 million in accrued payments to covered entities at year-end, and health insurance costs $1.542 billion above the FY 2026 Adopted Budget (including the receivable write-down). Excluding that write-down, costs were still $605 million (6.2%) above budget.

## Interview responses

The sample responses are based on the candidate's résumé, including education, Town of Riverhead service, Bristol Fish and Game financial administration, Stony Brook University Hospital forecasting, temporary New York State Comptroller work, current operations management, and the Riverhead public-budget project. They are drafts for review, not independent verification of the résumé.


## NYC public APIs and datasets — reproducible extraction

- NYC Open Data, Expense Budget (dataset `mwzb-yiwb`): https://data.cityofnewyork.us/City-Government/Expense-Budget/mwzb-yiwb — object-code budget detail. Object code 062 is extracted as a budget series only; it is not actual spending.
- NYC Open Data, Expense Actuals (dataset `7yay-m4ae`): https://data.cityofnewyork.us/City-Government/Expense-Actuals/7yay-m4ae — agency summary actuals, rounded to thousands; not health-insurance-specific.
- NYC Open Data, Expense Actuals By Funding Source (dataset `nrik-v7ws`): https://data.cityofnewyork.us/City-Government/Expense-Actuals-By-Funding-Source/nrik-v7ws — agency-level funding mix; not health-insurance-specific.
- NYC Open Data, Additional Costs Allocation (dataset `u42g-qjaj`): https://data.cityofnewyork.us/City-Government/Additional-Costs-Allocation/u42g-qjaj — includes centrally allocated fringe-benefit costs; fringe benefits are broader than health insurance.
- NYC Open Data, Financial Plan Baseline & Initiatives By Funding (dataset `e64w-ctmw`): https://data.cityofnewyork.us/City-Government/Financial-Plan-Baseline-Initiatives-By-Funding/e64w-ctmw — plan initiatives and estimates, not realized savings.
- Retrieval code and methodology: [scenario-2/public-data/README.md](scenario-2/public-data/README.md) and [fetch_nyc_public_data.py](scenario-2/public-data/fetch_nyc_public_data.py).

The public Open Data API does not by itself provide a complete actual health-insurance object-code series. Do not substitute agency-level expense totals or total fringe benefits for health-insurance actuals. Keep budget, actual expenditure, actuarial savings claims, equalization offsets, and HISF balances as separate measures.
