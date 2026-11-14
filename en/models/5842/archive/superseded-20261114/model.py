"""Integral 5842 conditional house model. JPY million except shares and EPS.

No imports from guidance, market prices, screening or portfolio records.
FY26 P&L = actual H1 + modeled H2; FY26 forward cash schedule covers H2 only.
Later rows cover twelve months. Investment subsidiaries remain at fair value;
their investee sales and borrowing are not gross-consolidated into this model.
"""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def calculate(actuals, assumptions):
    a, p = copy.deepcopy(actuals), copy.deepcopy(assumptions)
    rows = []
    cash = a['cash_june26']
    investments = a['investment_assets_june26']
    principal_fv = a['principal_fv_june26']
    equity = a['parent_equity_june26']
    debt = a['borrowings_from_fv_subs_june26']
    uncalled_existing_gp = p['opening_uncalled_existing_gp_proxy']
    uncalled_new_gp = 0
    deferred_tax_liquidity_reserve = a['opening_deferred_tax_liability']
    carry_stock = a['unrealized_carry_june26'] * (1-p['carry_stock_haircut'])
    previous_old_fee_base = a['fee_aum_june26'] - a['fund_v_external_fee_base'] - a['re_external_fee_base']
    previous_new_fee_base = 0
    previous_receivables = a['receivables_june26']
    previous_advances = a['advances_june26']
    previous_fixed = (a['recurring_cost_h126']-a['da_h126']-p['variable_fee_cost_ratio']*(a['management_fee_h126']+a['support_fee_h126']))*2
    for i, year in enumerate([2026, 2027, 2028, 2029]):
        duration = .5 if i == 0 else 1
        old_fee_base = p['old_fee_base_end'][i]
        new_fee_base = p['new_fund_commitment_end'][i] * .98
        assert old_fee_base >= 0 and new_fee_base >= 0
        # Existing Fund V keeps commitment fees throughout 2025–29;
        # harvesting vintages run off at cost. No fees on the GP's 2% stake.
        average_fee_base = (previous_old_fee_base+old_fee_base)/2+a['fund_v_external_fee_base']+a['re_external_fee_base']
        # First close assumed midyear; later closes are spread through the year.
        average_new_fee_base = (previous_new_fee_base+new_fee_base)/2
        management_fees = (average_fee_base+average_new_fee_base)*p['management_fee_rate']*duration
        support_fees = a['support_fee_h126']*2*(1+p['support_growth'])**(year-2026)*duration
        fee_revenue = management_fees+support_fees
        fixed_cash_cost = previous_fixed*(1+p['fixed_cost_growth'])**duration
        fixed_cash_period = fixed_cash_cost*duration
        variable_cash_cost = fee_revenue*p['variable_fee_cost_ratio']
        da = (a['da_h126']*2+p['annual_asset_capex']/p['asset_life_years']*(year-2026))*duration
        recurring_cost = fixed_cash_period+variable_cash_cost+da
        fee_ebit = fee_revenue-recurring_cost
        carry = p['carry_realization'][i]
        if carry > carry_stock+1e-8:
            raise ValueError('Carry exceeds the remaining disclosed June stock; new accrual cannot be invented')
        carry_stock -= carry
        carry_bonus = carry*p['carry_bonus_ratio']
        principal_mark = principal_fv*p['principal_fv_return'][i]*duration
        # Disposal-specific tax bases are undisclosed. Reserve the full opening
        # DTL in liquidity stress, plus tax on any positive future mark.
        # The cash path is explicitly before that unallocated settlement.
        deferred_tax_liquidity_reserve += max(0,principal_mark)*p['tax_rate']
        principal_dividend = a['dividends_h126']*2*duration
        other_operating = a['other_income_h126']*2*duration
        operating_income = fee_ebit+carry-carry_bonus+principal_mark+principal_dividend+other_operating
        interest_income = cash*p['cash_interest_rate']*duration
        debt_repayment = debt if i == 0 else 0
        # Opening temporary intercompany funding is conservatively all repaid in H2.
        finance_cost = (debt-debt_repayment/2)*p['borrowing_rate']*duration + p['lease_interest_annual']*duration
        pbt = operating_income+interest_income-finance_cost
        tax = pbt*p['tax_rate'] # loss tax credit is tested separately, not a cash refund
        # Observed H1 NCI relates to RE/other profits; bounded financial proxy.
        nci = a['nci_h126']*2*duration*(1+p['nci_growth'])**(year-2026)
        parent_profit = pbt-tax-nci
        shares = a['basic_shares']*(1+p['annual_share_dilution'])**(year-2026)
        diluted_shares = shares+a['option_incremental_shares']
        # Fee-only normalization excludes carry, marks, dividends and cash interest,
        # retains funding costs, and allocates NCI against fees conservatively.
        fee_parent_profit = (fee_ebit-finance_cost)*(1-p['tax_rate'])-nci
        gp_calls_existing = p['existing_gp_calls'][i]
        if gp_calls_existing > uncalled_existing_gp+1e-8:
            raise ValueError('Existing GP calls exceed assumed uncalled commitment')
        uncalled_existing_gp -= gp_calls_existing
        new_commitment = max(0,p['new_fund_commitment_end'][i]-(0 if i==0 else p['new_fund_commitment_end'][i-1]))*.02
        new_gp_call = new_commitment*p['new_gp_first_year_call_fraction']+uncalled_new_gp*p['new_gp_subsequent_call_fraction']
        uncalled_new_gp += new_commitment-new_gp_call
        gp_calls = gp_calls_existing+new_gp_call
        principal_calls = p['principal_calls'][i]
        investment_calls = gp_calls+principal_calls
        distributions = p['investment_capital_return'][i]
        principal_return = p['principal_capital_return'][i]
        if not 0 <= principal_return <= distributions:
            raise ValueError('Principal capital return must be a subset of investment distributions')
        if principal_return > principal_fv+principal_calls:
            raise ValueError('Principal capital return exceeds its carrying assets')
        if distributions > investments+investment_calls:
            raise ValueError('Investment distributions exceed carrying assets')
        investments += investment_calls-distributions+principal_mark
        principal_fv = max(0, principal_fv+principal_mark+principal_calls-principal_return)
        ending_receivables = fee_revenue/duration*p['fee_receivable_days']/365+carry*p['carry_receivable_fraction']
        ending_advances = management_fees/duration*p['advance_months']/12
        working_capital_use = ending_receivables-previous_receivables-(ending_advances-previous_advances)
        capex = p['annual_asset_capex']*duration
        dividend_cash = (a['h226_dividend_cash'] if i==0 else equity*p['dividend_doe'])
        opening_cash = cash
        # H1 carry cash already in opening cash. June UCAT is not cash.
        # Opening tax payable is paid in H2 in addition to current modeled tax.
        tax_payable_settlement = a['tax_payable_june26'] if i==0 else 0
        cash_tax=max(0,(pbt-principal_mark)*p['tax_rate'])
        cash_tax_adjustment=cash_tax-tax
        # Cash is consolidated: NCI profit stays inside the group absent a modeled
        # minority distribution. Negative tax expense is not a cash refund.
        cf_before_funding = parent_profit+nci+da-principal_mark-working_capital_use-investment_calls+distributions-capex-dividend_cash-tax_payable_settlement-p['lease_principal_annual']*duration-cash_tax_adjustment
        cash_before_new_debt = cash+cf_before_funding-debt_repayment
        new_borrowing = max(0,p['minimum_cash']-cash_before_new_debt)
        new_interest = new_borrowing*p['borrowing_rate']*duration/2
        # Borrowings cost cash in the draw year and reduce earnings after tax.
        if new_borrowing:
            shortfall = new_borrowing
            interest_factor = p['borrowing_rate']*duration/2
            cash_tax_before_interest = cash_tax
            taxable_profit_before_interest = max(0,pbt-principal_mark)
            candidate = shortfall/(1-interest_factor*(1-p['tax_rate']))
            if candidate*interest_factor <= taxable_profit_before_interest:
                new_borrowing = candidate
            else:
                # Interest tax relief is capped by existing taxable profit;
                # an accounting loss credit cannot finance a cash deficit.
                new_borrowing = (shortfall-cash_tax_before_interest)/(1-interest_factor)
            new_interest = new_borrowing*interest_factor
            cash_tax = max(0,(pbt-principal_mark-new_interest)*p['tax_rate'])
            parent_profit -= new_interest*(1-p['tax_rate'])
            fee_parent_profit -= new_interest*(1-p['tax_rate'])
            pbt -= new_interest
            tax -= new_interest*p['tax_rate']
            finance_cost += new_interest
            cf_before_funding -= new_interest-(cash_tax_before_interest-cash_tax)
        cash = opening_cash+cf_before_funding-debt_repayment+new_borrowing
        debt += new_borrowing-debt_repayment
        equity += parent_profit-dividend_cash
        full_parent_profit = parent_profit+(a['parent_profit_h126'] if i==0 else 0)
        full_fee_profit = fee_parent_profit+((a['fee_ebit_h126']-a['finance_cost_h126'])*(1-p['tax_rate'])-a['nci_h126'] if i==0 else 0)
        full_fee_revenue = fee_revenue+(a['management_fee_h126']+a['support_fee_h126'] if i==0 else 0)
        full_ebit = operating_income+(a['operating_income_h126'] if i==0 else 0)
        r = dict(year=year,fiscal_end=f'{year}-12-31',forward_cash_period='H2 only' if i==0 else 'full year',
            management_fees=management_fees+(a['management_fee_h126'] if i==0 else 0),support_fees=support_fees+(a['support_fee_h126'] if i==0 else 0),
            fee_revenue=full_fee_revenue,fee_aum_end=old_fee_base+a['fund_v_external_fee_base']+a['re_external_fee_base']+new_fee_base,
            new_fund_commitments=p['new_fund_commitment_end'][i],recurring_cost=recurring_cost+(a['recurring_cost_h126'] if i==0 else 0),
            fee_ebit=fee_ebit+(a['fee_ebit_h126'] if i==0 else 0),realized_carry=carry+(a['carry_h126'] if i==0 else 0),
            forward_carry_bonus=carry_bonus,remaining_june_carry=carry_stock,forward_principal_mark=principal_mark,
            operating_income=full_ebit,parent_profit=full_parent_profit,basic_shares=shares,diluted_shares=diluted_shares,
            basic_eps=full_parent_profit*1e6/shares,diluted_eps=full_parent_profit*1e6/diluted_shares,
            recurring_fee_parent_profit=full_fee_profit,recurring_fee_eps=full_fee_profit*1e6/shares,
            forward_pbt=pbt,forward_tax=tax,forward_cash_tax=cash_tax,forward_nci=nci,forward_finance_cost=finance_cost,
            forward_fixed_cash_cost=fixed_cash_period,forward_variable_cash_cost=variable_cash_cost,forward_da=da,
            forward_gp_calls=gp_calls,forward_principal_calls=principal_calls,forward_investment_calls=investment_calls,
            uncalled_existing_gp_proxy=uncalled_existing_gp,uncalled_new_gp=uncalled_new_gp,
            cash_after_full_remaining_gp_calls=cash-uncalled_existing_gp-uncalled_new_gp,
            deferred_tax_liquidity_reserve=deferred_tax_liquidity_reserve,
            cash_after_full_gp_and_deferred_tax_settlement=cash-uncalled_existing_gp-uncalled_new_gp-deferred_tax_liquidity_reserve,
            forward_principal_capital_return=principal_return,forward_investment_capital_return=distributions,forward_capex=capex,
            forward_working_capital_use=working_capital_use,forward_parent_dividend=dividend_cash,
            opening_cash=opening_cash,forward_cash_flow_before_funding=cf_before_funding,
            forward_debt_repayment=debt_repayment,forward_new_borrowing=new_borrowing,cash=cash,debt=debt,
            parent_equity=equity,investment_assets=investments,principal_fv=principal_fv,
            ending_receivables=ending_receivables,ending_advances=ending_advances,
            cash_inclusive_return_on_opening_parent_equity=parent_profit/(equity-parent_profit+dividend_cash)/duration)
        rows.append(r)
        previous_old_fee_base=old_fee_base
        previous_new_fee_base=new_fee_base
        previous_receivables=ending_receivables
        previous_advances=ending_advances
        previous_fixed=fixed_cash_cost
    return rows

def run_all(directory=ROOT):
    actuals=json.loads((directory/'actuals.json').read_text(encoding='utf-8'))
    assumptions=json.loads((directory/'assumptions.json').read_text(encoding='utf-8'))
    return {name:calculate(actuals,case) for name,case in assumptions.items()}

if __name__=='__main__':
    print(json.dumps(run_all(),indent=2))
