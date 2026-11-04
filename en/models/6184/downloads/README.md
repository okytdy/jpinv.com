# Kamakura Shinsho (6184) — JII forecast model

Research cutoff and revision: 4 November 2026. Fiscal years end31January.
All amounts are JPYmillions unless a field says EPS, shares or percent.

## Use the model

Open annual_forecast.csv for all twelve scenario/year rows. business_forecast.csv contains the seven issuer business categories and their explicit scope/reconciliation line. cash_forecast.csv starts with forecast H2FY1/27, then full years; annual_forecast.csv contains full fiscal-year CFO, including reported H1.

Run `python model.py` with Python3 (standard library only) to regenerate forecast.json. The earnings engine reads only actuals.json and assumptions.json. comparators.json is isolated and does not drive it. All unrounded numerical records, cost/tax/share/capital bridges and sensitivities are in forecast.json. valuation.json contains the separately calculated illustrative P/E valuation; revision_bridge.json reconciles the original and revised EPS. Source originals are available through the named URLs and archive hashes in source_register.json.

## What changed

The original seven-business research survives. FY1/27 now locks the actual first half and models the remaining half separately, avoiding unsupported acceleration in graves, funerals, inheritance and Other. Personnel, advertising and other expenses start from reported cost categories. They replace the old shared-cost figure calibrated to a chosen operating profit. Capitalized software/PPE/prepaids now feed asset-cohort depreciation and cash investment. Taxes and nonparent claims are explicit.

Original FY1/30 basic EPS46.91 becomes46.72; the November3 aggregate rewrite (33.88) was not retained. Lower revised OP is largely offset by replacing the old4% group-profit minority deduction with separate source-grounded entity exposures. This is a method repair, not a new adverse issuer results announcement. The original article model is retained in original_article_model_2026-10-30.json as historical evidence.

## Sources and limitations

The company has one statutory segment. Management business categories are not statutory segments or fully allocated segment profits; original disclosed categories have a known prior-H1 scope/reconciliation difference. No invented units, fees, market shares, incremental cross-use sales or future M&A are added. Staff and other-cost elasticities are house assumptions, with sensitivities for full activity responsiveness. Future cash is consolidated and not all freely distributable. Working-capital/provision balances and entity profit/PPA/fiscal-date gaps remain uncertain. Full identified option dilution is an economic overhang scenario, not GAAP diluted EPS. No future option exercise cash is assumed.

The article's18/20/22x P/E,10% annual discount and20yen annual dividend assumptions are retained to isolate the forecast revision. They are illustrative JII choices, not newly observed peer valuations. The three-year horizon describes the calculation, not an expected date for the market price to attain an estimate. Future leases retain a comparable after-rent basis because the issuer's FY1/29 accounting-transition effect is unquantified.
