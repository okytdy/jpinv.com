# HAMAKYOREX (9037) — JII model

Research cutoff: 5 November 2026. Public model version: 1.0. Fiscal years end March. Forecasts are dated independent JII estimates, not management guidance. The overview is https://jpinv.com/en/models/9037/ .

Run `python earnings_model.py` with Python 3; only the standard library is required. It reads actuals.json and assumptions.json, then regenerates model_output.json, annual_cases.csv, validation.json and model_summary.md. forecast.json is a byte-identical reader alias for the reviewed model_output.json; annual_forecast.csv is the readable base-case annual table. The engine retains bear/base/bull cases, segment economics, sensitivities, funding and EPS bridges.

Amounts in the executable/full dataset are JPY million, absolute shares and yen EPS. The readable annual CSV uses JPY billion, percentages and yen EPS. Actual financial periods and public primary-source URLs are in actuals.json and source_register.json; the detailed assumptions and source passages are in assumption_register.md.

FY3/27 earnings are full-year estimates combining reported H1 and estimated H2. FY3/27 cash capex, CFO and FCF cover October 2026–March 2027 only: the latest H1 release did not include a cash-flow statement. FY3/28–30 cash flows cover full fiscal years. Closing cash and bank debt are fiscal year-end balances. Forecast available cash begins from gross cash/deposits less an assumed JPY1.721bn unavailable-time-deposit proxy; it is not directly comparable with actual gross cash/deposits.

Recurring EPS uses basic weighted shares. Constant pre-adoption lease economics are retained: operating rents remain operating costs, while finance-lease principal is separately funded. These are not precise statutory EPS forecasts after the new lease standard takes effect. Reported FY3/26 basic EPS144.83 is distinct from the estimated normalized135.01 and the FY3/27E baseline138.16. The FY3/27E–30E EPS CAGR spans exactly three years.

Three full forecast years FY3/28–30 generate JPY18.919395bn FCF after cash capex and finance-lease principal, before parent/minority dividends, acquisitions and bank repayments. FCF is a flow, not a closing cash balance. At30September2026 bank borrowings41.527bn less gross cash/deposits26.132bn imply15.395bn net bank debt, excluding leases. September lease obligations are not separately subtotaled; the March2026 reported6.702bn remains a dated funding proxy.

No future unannounced M&A earnings/cash, relay fees or subsidy income is assumed. Contract prices, customer churn/new work, cost productivity, capex split and minority claims include explicitly identified financial proxies. Conditional scenario bounds are not statistical confidence intervals. The assumptions and funding needs may differ materially from actual results.

This package contains only public issuer/JII model material. No private client research, portfolio construction or internal screening records are included. SHA256SUMS.json binds all bundled files. The original reviewed model-output SHA256 is8af6c2992c8dffa2451bad25b4ece914f54e55f0d47e93eabfada4e9c8ea25ea.
