# OSCEXAM — Municipal Financial Analyst Assessment

Private working portfolio for the senior municipal financial analyst assessment.

## Contents

- [Scenario 1 — Fringe Benefits](scenario-1/README.md): methodology and reproducible Excel workbook builder for the three-year object-code pivot analysis.
- [Scenario 2 — Health Benefits Agreement](scenario-2/briefing.md): concise executive briefing on the NYC/MLC FY 2019–2021 agreement.
- [Written Interview Responses](interview/written-responses.md): sample responses grounded in the candidate's documented experience.
- [Sources and assumptions](SOURCES.md): source links, analytical definitions, and limitations.

## Status

**Scenario 1 calculations are pending the original City workbook.** The prompt refers to a three-year spreadsheet with a Reference tab, but that source workbook was not attached to the materials available for this repository. No spending totals, growth rates, or object-code descriptions have been fabricated. Add the original workbook as `scenario-1/source_data.xlsx` (do not commit confidential or restricted data), then run the builder described in the Scenario 1 README.

## Reproducibility

The Scenario 1 script uses Python, pandas, and openpyxl. It produces a formatted Excel workbook with annual spending by object-code category, year-over-year growth, two-year CAGR, data-quality checks, and supporting detail.

## Confidentiality

This repository is private. Keep source financial records and any non-public employment or interview materials private. Before sharing the assessment, review the final workbook and remove any information not intended for the recipient.
