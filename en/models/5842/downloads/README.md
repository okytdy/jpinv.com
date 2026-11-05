# Integral Group (5842): dated conditional earnings model

Research cutoff: 5 November 2026. Fiscal year ends 31 December. Amounts are
JPY million, except absolute shares and per-share figures. This is independent
JII research. No market price, valuation target or portfolio rule drives it.

The fee business faces older-fund runoff before a successor contributes. The
base assumes a successor starts earning fees halfway through 2029, at the same
JPY250bn commitment size as Fund V. **No successor has been announced in the
verified sources.** Its size and timing are analyst assumptions, not a pipeline
or commitment. Fund V began investing in January2025; disclosed investment
periods are approximately five years. Four-to-five-year prior fund-vintage
spacing and more than40% Fund V deployment by June2026 motivate the timing
range. A 2029 close is conditional, not inevitable.

`recurring_fee_eps` is management/support fees less recurring costs, gross
funding costs, tax and a conservative NCI proxy. It excludes carried interest,
investment valuation gains, dividends and cash interest. `basic_eps` includes
the explicitly modeled carry and valuation outcomes. Carry is ordinary to this
business over its life, but its accounting recognition is irregular; the
fee-only series must not be read as total expected earnings.

The model caps all future carry receipts at the disclosed June2026 pre-tax
unrealized balance of JPY22bn (FundII0.7bn,III3.9bn,IV17.4bn), already net of
director/employee GP interests. It does not add fresh carry accrual or extrapolate
H1 realized carry of JPY10.983bn. New recognition requires the contractual
8% hurdle and low clawback risk. The realization schedule is a low-confidence
financial proxy, not an exit-by-exit forecast. Annual actual receipts could
be zero or exceed the modeled schedule. A separate6% cash bonus cost is charged
on future carry, anchored to H1 one-off costs of654m (which also include other
items); this is an assumption, not a disclosed contractual payout rate.

FY2026 P&L is actual H1 plus modeled H2. FY2026 forward funding columns are H2
only; FY2027–29 are full years. Opening consolidated cash already includes H1
cash carry and subsidiary funding. The model repays all JPY10.001bn of June
loans from fair-valued subsidiaries in H2 and settles opening tax payable of
4.297bn. Unrealized carry is never liquid cash. Investment capital returns are
at carrying value; gains are modeled separately. Principal investment flows
are subsets of the full investment-asset roll. Both existing/new GP obligations
roll forward, and remaining uncalled obligations are exposed with an immediate
full-call cash stress. The opening existing GP obligation of3.470bn is an
undisclosed-balance proxy: FundV's2% stake less40% deployed, plus all RE FundI's
2% stake; actual draw ratios can differ. There is no committed borrowing line.

Cash is consolidated, parent earnings exclude NCI, and NCI profits stay in group
cash absent distributions. The NCI proxy scales observed H1 profit22m rather
than inventing entity forecasts. Its EPS effect is small but source allocation
is incomplete. No new buyback or share issuance is assumed; diluted EPS retains
the disclosed784,484 option-share increment. Cash-inclusive return on opening
parent equity is a financing/asset-management diagnostic, not industrial ROCE.
Unrealized principal marks enter accounting tax and deferred tax; they create
no immediate cash tax deduction or payment. Loss tax credits are not cash refunds.
The annual `cash` path is **before unallocated cash settlement of tax on opening
embedded investment gains**. Disposals at carrying value create no new P&L gain
but can crystallize that tax. Exact entity tax bases and disposal timing are
undisclosed. A separate combined liquidity stress deducts the entire disclosed
opening deferred tax liability of JPY11.200bn, plus tax on every positive future
principal mark, together with all remaining GP commitments. Base FY2029 cash
after that maximum reserve is JPY24.730bn, versus38.930bn before the reserve and
GP calls. This is a bounded funding stress, not an assertion that all deferred
tax becomes due by2029 or that disposals are tax-free. No remaining liability
is counted as free cash in the combined stress.

September16 Oliver's partial IPO exit is verified: the issuer expected an
immaterial FY2026 earnings effect because investments were already marked
quarterly. No incremental IPO gain is invented. October1 transfers to wholly
owned group subsidiaries change the legal structure, with no new outside
ownership inferred.

## Reproduction and files

Run `python reproduce.py` in this folder using Python3.9+; no packages or network
are needed. It checks12 annual rows, cash/investment/commitment conservation,
carry limits, missing-input rejection, guidance independence and causal
sensitivities. `model.py` is the calculation engine; `actuals.json` and
`assumptions.json` are its only inputs. `forecast.json`, `annual_forecast.csv`
and `sensitivities.json` are dated outputs. `source_register.json` and
`assumption_register.json` provide locators, anchors, ranges and falsifiers.
`guidance_comparator.json` is read only after the independent case is frozen.
The archive contains no credentials, local account data or internal selection
method. Edit a copy of the assumptions to explore alternatives; keep the dated
saved forecast intact as the comparison reference.

## Prior work and principal limitations

The October15 published article used JPY2.909bn FY2026 company reference
recurring pre-tax profit and economic net worth for a reverse-valuation
comparison. It contained no full FY2026–29 EPS forecast. All historical report
files and figures are preserved. This dated model replaces the earlier
comparison as the forward-earnings research reference, without rewriting its
historical publication or treating a change of earnings definition as growth.

The base uses the disclosed1.85–2.0% fee range's1.95% midpoint, applied to
average fee-paying capital. H1's actual fee yield is slightly higher than this
simple proxy, reflecting timing/mix or catch-up charges that are not split in
the available data; it is retained as actual, not calibrated away. Older-fund
runoff, staff costs, successor fundraising, carry recognition and GP calls are
bounded house assumptions. RE FundI fees remain at the current commitment base;
no unannounced RE successor, future GlobalTech fees or principal valuation
appreciation is needed in the base. Current-year costs could exceed the house
estimate: the company's recurring-cost reference is higher. The cost sensitivity
and separate comparator show the consequence. Latest verified reported period
is June2026; this package is a pre-Q3 baseline and should be refreshed when
subsequent results are released. Confidence is low because carry timing and
successor fundraising are undisclosed.
