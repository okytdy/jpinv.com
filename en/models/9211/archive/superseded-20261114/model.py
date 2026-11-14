"""f-code: conditional earnings, ownership claims and cash funding. Amounts JPY million."""
import copy

def calculate(a, cfg, case):
    scale = a['scope_adjusted_revenue_annual_runrate'] / (a['known_H1_sales'] * 2)
    sales = a['scope_adjusted_revenue_annual_runrate']
    cashpool = (a['known_H1_sales'] - a['known_H1_core_OP'] - a['known_H1_DA']) * 2 * scale
    var = cashpool * cfg['variable_cash_cost_share']
    fixed = cashpool - var
    cash = a['opening_cash']
    debt = a['bank_bond_debt']
    shares = a['shares_current']
    cohorts = copy.deepcopy(a['nci_cohorts'])
    paidput = 0
    paidearn = 0
    contract = a['contract_liabilities']
    assetcohorts = []
    rows = []
    receivables = a['receivables']
    payables = a['payables']
    initial_credit_runrate = a['scope_adjusted_revenue_annual_runrate'] - a['contract_liabilities']
    covered_anchor = sum((c['outside_profit_anchor_annual'] * c['put_covered_fraction_house'] for c in cohorts))
    for c in cohorts:
        c['current_outside_claim'] = c['outside_profit_anchor_annual']
    for i, end in enumerate(a['periods']):
        fraction = 0.5 if i == 0 else 1
        openingpaid = paidput
        exercise = cfg['put_exercise_fraction_of_original_covered_pool'][case][i]
        paidput = min(1, paidput + exercise)
        earnfraction = cfg['earnout_cash_fraction'][case][i]
        paidearn = min(1, paidearn + earnfraction)
        g = cfg['operating_growth'][case][i]
        prepaid_earned = min(contract, a['contract_liabilities'] * cfg['contract_delivery_fraction_of_opening'][case][i])
        refund = min(max(0, contract - prepaid_earned), a['contract_liabilities'] * cfg['contract_refund_fraction_of_opening'][case][i])
        contract -= prepaid_earned + refund
        nominal_forecast_revenue = sales * (1 + g) * fraction
        reference_prepaid = a['contract_liabilities'] * cfg['reference_opening_contract_delivery_house'][i]
        prepaid_timing_delta = prepaid_earned - reference_prepaid
        future_revenue = nominal_forecast_revenue + prepaid_timing_delta
        volume = (1 + g) / (1 + cfg['realized_price_mix'][case])
        vc = var * volume * (1 + cfg['variable_input_inflation'][case]) * fraction
        fc = fixed * (1 + cfg['fixed_cash_inflation'][case]) * fraction
        capex = cfg['annual_maintenance_capex'] * fraction + max(0, future_revenue / fraction - sales) * cfg['expansion_capex_per_incremental_revenue'] * fraction
        assetcohorts.append(dict(year=i, spend=capex))
        oldnonlease = max(0, a['known_H1_DA'] * 2 - cfg['annual_ROU_DA_proxy']) * max(0, 1 - (i + 1) / cfg['software_asset_life'])
        newDA = sum((x['spend'] / cfg['software_asset_life'] * (fraction * 0.5 if x['year'] == i else fraction) for x in assetcohorts if i - x['year'] < cfg['software_asset_life']))
        DA = oldnonlease * fraction + cfg['annual_ROU_DA_proxy'] * fraction + newDA
        futureOP = future_revenue - vc - fc - DA
        nci = 0
        cohortrows = []
        covered_now = 0
        for c in cohorts:
            growth = cfg['entity_profit_growth'][c['name']][case][i]
            c['current_outside_claim'] *= 1 + growth
            prepaid_effect = prepaid_timing_delta * (1 - a['tax_rate']) * 0.25 / fraction if c['name'] == 'AI ONE25%outside' else 0
            effective_claim = c['current_outside_claim'] + prepaid_effect
            covered = effective_claim * c['put_covered_fraction_house']
            ratio = max(0.25, effective_claim / c['outside_profit_anchor_annual'])
            weight = c['outside_profit_anchor_annual'] * c['put_covered_fraction_house'] / covered_anchor
            cohortprice = a['put_PV'] * weight * cfg['put_price_multiplier_house'][case] * ratio ** cfg['put_earnings_elasticity'][case] * (1 + cfg['seller_time_value_rate']) ** (i + 0.5)
            cohortput = cohortprice * exercise
            average_bought = openingpaid + 0.5 * exercise
            remaining_claim = effective_claim * (1 - c['put_covered_fraction_house'] * average_bought) * fraction
            nci += remaining_claim
            covered_now += covered
            cohortrows.append(dict(name=c['name'], source_annual_outside_claim=c['outside_profit_anchor_annual'], outside_claim_before_purchase_annual=effective_claim, prepaid_timing_effect_on_annualized_outside_profit=prepaid_effect, put_covered_fraction_house=c['put_covered_fraction_house'], opening_bought_fraction_of_covered_pool=openingpaid, new_bought_fraction_of_covered_pool=exercise, closing_bought_fraction_of_covered_pool=paidput, remaining_aftertax_NCI_this_forecast_period=remaining_claim, put_cash_purchase=cohortput, pending_put_house_cashpoint=cohortprice * (1 - paidput)))
        putcash = sum((x['put_cash_purchase'] for x in cohortrows))
        index = max(0.25, covered_now / covered_anchor)
        earncash = a['earnout_FV'] * earnfraction * cfg['earnout_price_multiplier_house'][case] * index ** cfg['earnout_earnings_elasticity'][case] * (1 + cfg['seller_time_value_rate']) ** (i + 0.5)
        pendingput = sum((x['pending_put_house_cashpoint'] for x in cohortrows))
        pendingearn = a['earnout_FV'] * (1 - paidearn) * cfg['earnout_price_multiplier_house'][case] * index ** cfg['earnout_earnings_elasticity'][case] * (1 + cfg['seller_time_value_rate']) ** (i + 0.5)
        noncash_unwind = (a['put_PV'] * (1 - openingpaid - 0.5 * exercise) + a['earnout_FV'] * (1 - (paidearn - earnfraction) - 0.5 * earnfraction)) * cfg['seller_time_value_rate'] * fraction
        fixedcash = cfg['fixed_AI_ONE_schedule'][i] if cfg['fixed_AI_ONE_is_extra_to_seller_pools_house'] else 0
        credit_runrate = (future_revenue - prepaid_earned) / fraction
        target_receivables = a['receivables'] * credit_runrate / initial_credit_runrate
        target_payables = a['payables'] * (future_revenue / fraction) / a['scope_adjusted_revenue_annual_runrate']
        workingcapital = target_receivables - receivables - (target_payables - payables)
        repayment = min(debt, cfg['bank_repayment_house'][i])
        cash_interest_income = a['known_H1_cash_interest_received'] * 2 * fraction
        leaseinterest = a['lease_debt'] * cfg['lease_interest_rate'] * fraction
        leaseprincipal = cfg['annual_lease_principal_proxy'] * fraction
        financefee = cfg['annual_other_cash_finance_fee'] * fraction
        taxarrears = a['tax_payable'] if i == 0 else 0
        reserve = (pendingput + pendingearn) * cfg['unsettled_claim_cash_reserve_fraction'] + contract
        cashfloor = future_revenue / fraction / 12 * cfg['cash_floor_months_of_revenue']
        refinance = 0
        equity = 0
        rate = cfg['bank_rate'][case]
        for _ in range(20):
            bankinterest = debt * rate * fraction + refinance * rate * fraction * 0.5
            taxable = futureOP + cash_interest_income - bankinterest - leaseinterest - financefee
            futuretax = max(0, taxable) * a['tax_rate']
            cashflow = futureOP + DA + cash_interest_income - bankinterest - leaseinterest - financefee - futuretax - workingcapital - prepaid_earned - refund
            unfunded = cash + cashflow - capex - leaseprincipal - putcash - earncash - fixedcash - repayment - taxarrears
            need = max(0, cashfloor + reserve - unfunded)
            newref = min(need, repayment * cfg['rollover_fraction_of_maturing_principal'] + cfg['maximum_new_credit_above_repaid_maturity_assumed'])
            newequity = max(0, need - newref)
            if abs(newref - refinance) + abs(newequity - equity) < 1e-08:
                refinance = newref
                equity = newequity
                break
            refinance = newref
            equity = newequity
        bankinterest = debt * rate * fraction + refinance * rate * fraction * 0.5
        taxable = futureOP + cash_interest_income - bankinterest - leaseinterest - financefee
        futuretax = max(0, taxable) * a['tax_rate']
        futurePBT = taxable - noncash_unwind
        cashflow = futureOP + DA + cash_interest_income - bankinterest - leaseinterest - financefee - futuretax - workingcapital - prepaid_earned - refund
        unfunded = cash + cashflow - capex - leaseprincipal - putcash - earncash - fixedcash - repayment - taxarrears
        endcash = unfunded + refinance + equity
        enddebt = debt - repayment + refinance
        issueprice = a['current_price'] * (1 - cfg['equity_issue_discount'])
        newshares = equity * 1000000.0 / issueprice
        weightedshares = (a['shares_H1_weighted'] * 0.5 + shares * 0.5 if i == 0 else shares) + newshares * fraction * 0.5
        knownPBT = a['known_H1_core_OP'] + a['known_H1_cash_interest_received'] - a['known_H1_finance_cost'] if i == 0 else 0
        knownTax = max(0, a['known_H1_core_OP'] + a['known_H1_cash_interest_received'] - a['known_H1_cash_interest_paid']) * a['tax_rate'] if i == 0 else 0
        knownNCI = a['known_H1_NCI'] if i == 0 else 0
        PBT = knownPBT + futurePBT
        tax = knownTax + futuretax
        totalNCI = knownNCI + nci
        parent = PBT - tax - totalNCI
        row = dict(label=f'FY{i}', period_end=end, op=futureOP + (a['known_H1_core_OP'] if i == 0 else 0), forecast_period_revenue=future_revenue, sales=future_revenue + (a['known_H1_sales'] if i == 0 else 0), forecast_period_variable_cash_cost=vc, forecast_period_fixed_cash_cost=fc, depreciation_amortization=DA + (a['known_H1_DA'] if i == 0 else 0), forecast_period_DA=DA, recurring_pbt=PBT, tax=tax, noncontrolling_profit=totalNCI, recurring_parent_profit=parent, weighted_average_basic_shares=weightedshares, recurring_eps=parent * 1000000.0 / weightedshares, known_H1_recurring_PBT=knownPBT, forecast_period_PBT=futurePBT, forecast_period_cash_tax=futuretax, noncash_seller_PV_unwind=noncash_unwind, bank_cash_interest=bankinterest, lease_cash_interest=leaseinterest, cash_finance_fee=financefee, cash_interest_income=cash_interest_income, nci_entity_cohorts=cohortrows, put_cash_paid=putcash, earnout_cash_paid=earncash, fixed_AI_ONE_cash_variant=fixedcash, pending_put_house_cashpoint=pendingput, pending_earnout_house_cashpoint=pendingearn, customer_prepaid_revenue_earned_without_new_cash=prepaid_earned, customer_refunds_paid=refund, remaining_contract_liability=contract, working_capital_change=workingcapital, forecast_period_business_cash_flow=cashflow, cash_capex=capex, lease_principal_cash=leaseprincipal, source_tax_payable_cash_paid=taxarrears, opening_cash=cash, ending_cash=endcash, opening_debt=debt, mandatory_bank_principal_paid=repayment, conditional_bank_refinancing=refinance, ending_debt=enddebt, conditional_equity_cash_required=equity, new_basic_shares=newshares, ending_basic_shares=shares + newshares, unsettled_claim_and_customer_cash_reserve=reserve, cash_after_claim_reserves=endcash - reserve, cash_without_refinance_or_equity=unfunded, cash_reconciliation_error=endcash - (cash + cashflow - capex - leaseprincipal - putcash - earncash - fixedcash - repayment - taxarrears + refinance + equity), funding_status='conditional_refinance_and_equity_not_committed' if equity > 1e-06 else 'conditional_rollover_not_committed' if refinance > 1e-06 else 'observed_cash_funds_case')
        row.update(elapsed_years_since_opening=i + 0.5, opening_lease_debt=a['lease_debt'], new_lease_liabilities_house=leaseprincipal, ending_lease_debt=a['lease_debt'], opening_prepaid_delivery_embedded_in_nominal_anchor=reference_prepaid, prepaid_revenue_timing_difference=prepaid_timing_delta, receivables_balance=target_receivables, payables_balance=target_payables)
        rows.append(row)
        cash = endcash
        debt = enddebt
        shares += newshares
        oldannual = sales
        sales = nominal_forecast_revenue / fraction
        var = var * (sales / oldannual) / (1 + cfg['realized_price_mix'][case]) * (1 + cfg['variable_input_inflation'][case])
        fixed *= 1 + cfg['fixed_cash_inflation'][case]
        receivables = target_receivables
        payables = target_payables
    return rows
