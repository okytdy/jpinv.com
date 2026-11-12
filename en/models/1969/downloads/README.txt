JII HVAC forecast model — 12 November 2026

Three companies: Takasago Thermal Engineering (1969), Dai-Dan (1980), and Nihon Dengi (1723).
Fiscal years end in March. FY3/27 uses company guidance; FY3/28–30 are the article's JII forecasts.

Contents
- annual_forecasts_all_companies.csv: the original 12 annual forecast rows used by the article.
- forecast.json: full numerical inputs, annual outputs and named primary sources.
- model.py: the revenue × operating-margin → operating-profit → net-income → EPS calculation.
- valuation_2026-11-12.csv: the article's dated enterprise-value calculations.

Run python model.py > reproduced_forecasts.csv. Revenue and profit are in billions of yen; shares are in millions; EPS is yen per share.
The model holds guidance-implied weighted shares and net-income/OP conversion constant. Annual company guidance and JII estimates are identified in the CSV basis column.
