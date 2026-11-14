# f-code (9211): conditional JII research model

Research cutoff: 4 November 2026. Fiscal year ends in December.
This independent rough estimate is conditional, with low confidence in undisclosed
seller-payment mapping and exercise timing. It is separate from the 27 October 2026
article's comparison based on FY12/26 company guidance of EPS JPY155.62 and its
illustrative 10x valuation. That article valuation is not an output of this model.

Amounts are JPY million except per-share amounts and absolute share counts.
Recurring basic EPS excludes unforecast seller-liability revaluation gains and
impairment; remaining operating expenses are retained. This differs from reported
IFRS profit and company guidance. FY12/26 combines actual H1 with estimated H2 for
sales/profit; forward cash-flow, capex, seller-payment and funding columns in the
first year cover H2 only. Subsequent rows cover full years. Closing cash/debt are
year-end balances. No future acquisitions, compensation recovery or new customer
advance receipts are assumed.

## Files and reproduction

Run `python reproduce.py` in this directory, using Python 3.9 or later. No packages
or network access are required. It checks exact annual output equality in three
scenarios (12 rows) and reproduces seven sensitivities. `model.py` preserves the
reviewed calculation function. `actuals.json`, `assumptions.json`, `forecast.json`,
`annual_forecast.csv`, `sensitivities.json` and `source_register.json` expose the
inputs, outputs and sources. Change a copy of the assumptions to explore a new
case; the saved forecast remains the dated reference. `lineage.json` records the
original reviewed authority and public-file hashes. No private screening method
or portfolio-construction rules are included.

## Main limitations

Actual put-to-entity mapping, strike formulas and exercise dates are undisclosed.
The model's seller cash prices, coverage and timing are JII assumptions, not terms.
Observed put present value JPY3,715.008m and earnout fair value JPY1,419.910m anchor
conditional payments, not contractual caps. The Roombox extra price is uncapped.
Partial-period subsidiary earnings annualization is a weak proxy. A separate
JPY750m AI ONE payment is treated conservatively as additional cash and tested as
already included. Opening customer advances require delivery/refunds; they are
not received twice. Refinancing and equity issuance are conditional and uncommitted.
The full model retains adverse operating, seller-cost, delivery and funding cases.

Source links and precise locators are in source_register.json. Primary documents
remain hosted by the issuer, JPX and FSA. Numerical source facts and issuer-specific
house assumptions are retained; internal workflow metadata is omitted.
