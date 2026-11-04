"""JII Kamakura Shinsho forecast. Python standard library only.

Inputs: actuals.json and assumptions.json. Guidance is never loaded.
Seven management-business revenue proxies; observed consolidated expense pools;
asset-cohort depreciation, entity-specific minority claims and annual cash funding.
All financial amounts are JPY millions, shares are absolute and EPS is JPY/share.
"""
import copy, csv, json, math
from pathlib import Path

HERE = Path(__file__).resolve().parent

def load(name):
    return json.loads((HERE/name).read_text(encoding='utf-8-sig'))

def historical_cost_identity(r):
    return r['sales']-sum(r[k] for k in ['op','personnel','advertising','other_operating_costs','asset_da','goodwill_amort','sbc'])

def run(a, p, case='base', overrides=None):
    p=copy.deepcopy(p)
    if overrides:p.update(overrides)
    h,py,fy=a['h1'],a['h1_prior'],a['fy26']
    assert all(abs(historical_cost_identity(a[k]))<1e-7 for k in ['fy26','h1_prior','h1'])
    sign={'bear':-1,'base':0,'bull':1}[case]
    business={};annual=[];cash=h['cash'];debt=h['debt'];capital=h['capital_employed']
    legacy_book=h['existing_depreciable_assets'];gw_book=h['goodwill'];cohorts=[]
    prior_noncurrent_debt=h['long_debt']
    prior_nwc={k:h[k] for k in ['receivables','inventory','prepaids','payables','customer_advances','insurance_reserves']}
    g_observed=h['sales']/py['sales']-1
    staff_e=((h['personnel']/py['personnel'])/(1+p['wage_inflation'])-1)/g_observed
    if staff_e<0 or staff_e>1:raise ValueError('Incompatible wage/staffing assumptions')
    mix_anchor=(a['businesses']['care']['h1']+a['businesses']['municipal']['h1'])/h['sales']
    ad_relative=(h['advertising']/(h['sales']-a['businesses']['insurance']['h1']))/(py['advertising']/(py['sales']-a['businesses']['insurance']['h1_prior']))
    last_sales=fy['sales'];last_noninsurance=fy['sales']-a['businesses']['insurance']['fy26']
    personnel=fy['personnel'];ads=fy['advertising'];other=fy['other_operating_costs']
    for j in range(4):
        first=j==0;duration=.5 if first else 1.0
        for name,b in a['businesses'].items():
            rate=p['growth'][name][j]+sign*p['scenario_growth_spread'][name]
            if rate<=-1:raise ValueError('Revenue growth below−100%')
            business[name]=(b['h1']+(b['fy26']-b['h1_prior'])*(1+rate)) if first else business[name]*(1+rate)
        reconciliation=h['business_reconciliation']+fy['business_reconciliation']-py['business_reconciliation'] if first else reconciliation
        sales=sum(business.values())+reconciliation
        noninsurance=sales-business['insurance']
        period_sales=sales-h['sales'] if first else sales
        prior_period_sales=fy['sales']-py['sales'] if first else last_sales
        activity_growth=period_sales/prior_period_sales-1
        mix=(business['care']+business['municipal'])/sales
        staff_elasticity=min(p['staff_elasticity_cap'],staff_e*(1+p['staff_mix_response']*(mix/mix_anchor-1)))
        if 'staff_elasticity_override' in p:staff_elasticity=p['staff_elasticity_override']
        wage=p['wage_inflation']+(.01 if case=='bear' else 0)
        infl=p['other_cost_inflation']+(.01 if case=='bear' else 0)
        other_e=p['other_cost_elasticity']+(.20 if case=='bear' else -.10 if case=='bull' else 0)
        ad_multiplier=(1.05 if case=='bear' else .98 if case=='bull' else 1)*(1+p['ad_intensity_annual_change'])
        if first:
            personnel_future=max(2*h['q2_personnel'],(fy['personnel']-py['personnel'])*(1+wage)*(1+staff_elasticity*activity_growth))
            other_future=(fy['other_operating_costs']-py['other_operating_costs'])*(1+infl)*(1+other_e*activity_growth)
            ni_future=period_sales-(business['insurance']-a['businesses']['insurance']['h1'])
            ni_prior=fy['sales']-py['sales']-(a['businesses']['insurance']['fy26']-a['businesses']['insurance']['h1_prior'])
            ads_future=(fy['advertising']-py['advertising'])*(ni_future/ni_prior)*ad_relative*ad_multiplier
            personnel=h['personnel']+personnel_future;other=h['other_operating_costs']+other_future;ads=h['advertising']+ads_future
        else:
            personnel_future=personnel*(1+wage)*(1+staff_elasticity*activity_growth)
            other_future=other*(1+infl)*(1+other_e*activity_growth)
            ads_future=ads*(noninsurance/last_noninsurance)*ad_multiplier
            personnel,other,ads=personnel_future,other_future,ads_future
        capex=p['capex'][j]*(.90 if case=='bear' else 1.15 if case=='bull' else 1)
        capex=max(capex,h['cash_capex']) if first else capex
        prepaid=p['prepaid_spend'][j]
        capex_future=capex-h['cash_capex'] if first else capex
        prepaid_future=prepaid-h['prepaid_spend'] if first else prepaid
        legacy_da=min(legacy_book,p['legacy_da_annual']*duration)
        legacy_book-=legacy_da;asset_da_future=legacy_da
        # Opening CIP is already funded and is not another cash investment.
        if first:
            cohorts.append({'name':'Opening software CIP','cost':h['software_in_progress'],'book':h['software_in_progress'],
                'life':p['software_life'],'first_fraction':duration,
                'delay':0 if p['cip_commission_h2_fraction'] else 1})
        for c in cohorts:
            if c.get('delay',0)>0:c['delay']-=1;continue
            time=c.pop('first_fraction',duration)
            d=min(c['book'],c['cost']/c['life']*time);c['book']-=d;asset_da_future+=d
        for name,cost,life in [('New software',capex_future*p['software_share'],p['software_life']),
             ('New PPE',capex_future*(1-p['software_share']),p['ppe_life']),('New long-term prepaids',prepaid_future,p['prepaid_life'])]:
            d=cost/life*duration*.5
            cohorts.append({'name':name,'year':2027+j,'cost':cost,'book':cost-d,'life':life})
            asset_da_future+=d
        goodwill_future=min(gw_book,p['goodwill_amort_annual']*duration);gw_book-=goodwill_future
        sbc_future=p['sbc_annual'][j]-(h['sbc'] if first else 0)
        op_future=period_sales-personnel_future-ads_future-other_future-asset_da_future-goodwill_future-sbc_future
        asset_da=(h['asset_da'] if first else 0)+asset_da_future
        goodwill=(h['goodwill_amort'] if first else 0)+goodwill_future
        op=(h['op'] if first else 0)+op_future
        closing_nwc={
            'receivables':h['receivables']*sales/(2*h['sales'])+sales*p['working_capital_days_add']/365,
            'inventory':h['inventory']*noninsurance/(2*(h['sales']-a['businesses']['insurance']['h1'])),
            'prepaids':h['prepaids']*sales/(2*h['sales']),
            'payables':h['payables']*sales/(2*h['sales']),
            'customer_advances':h['customer_advances']*sales/(2*h['sales']),
            'insurance_reserves':h['insurance_reserves']*business['insurance']/(2*a['businesses']['insurance']['h1'])}
        wc_changes={k:closing_nwc[k]-prior_nwc[k] for k in prior_nwc}
        dwc=sum(wc_changes[k] for k in ['receivables','inventory','prepaids'])-sum(wc_changes[k] for k in ['payables','customer_advances','insurance_reserves'])
        repayment=min(debt,h['current_debt'] if first else h['long_debt']/3)
        close_debt=debt-repayment
        interest_future=(debt+close_debt)/2*p['existing_debt_rate']*duration
        receipts_future=cash*p['cash_yield']*duration
        nonop_future=receipts_future-interest_future-p['other_nonoperating_cost_annual']*duration
        pbt_future=op_future+nonop_future
        tax_future=max(0,(pbt_future+goodwill_future*p['nondeductible_goodwill_fraction'])*p['tax_rate'])
        minority={}
        for name,e in a['minority_entities'].items():
            driver=e['revenue_driver'];factor=business[driver]/a['businesses'][driver]['fy26']
            profit=e['ordinary_pbt'] if 'ordinary_pbt' in e else e['reported_net_income']
            # Observed recurring losses are not awarded a fresh tax credit.
            minority[name]=profit*factor*(1-e['parent_ownership'])*duration*p['minority_loss_scale']
        nci_future=sum(minority.values())
        if 'nci_annual_override' in p:nci_future=p['nci_annual_override']*duration
        group_future=pbt_future-tax_future;parent_future=group_future-nci_future
        pbt=(h['pbt'] if first else 0)+pbt_future
        tax=(h['tax'] if first else 0)+tax_future
        nci=(h['nci_profit'] if first else 0)+nci_future
        parent=(h['parent_profit'] if first else 0)+parent_future
        group=parent+nci
        basic_shares=h['basic_weighted_shares']
        eps=parent*1e6/basic_shares
        # Identified parent insurance/FX gains net of disposals: known H1 net4.962m.
        # This optional bridge never reclassifies the unexplained actual NCI.
        recurring_adjustment=4.962*(1-p['tax_rate']) if first else 0
        recurring_eps=(parent-recurring_adjustment)*1e6/basic_shares
        cfo_future=group_future+asset_da_future+goodwill_future+sbc_future-dwc
        cfo=(h['cfo'] if first else 0)+cfo_future
        dividends_future=0 if first else basic_shares*p['dividend_per_share']/1e6
        div=(h['dividends_paid'] if first else 0)+dividends_future
        close_cash=cash+cfo_future-capex_future-prepaid_future-dividends_future-repayment
        funding_gap=max(0,-close_cash)
        # A displayed funding need does not assert access to a facility.
        funding_interest=0
        if funding_gap:
            for _ in range(30):
                benefit=min(tax_future,funding_interest*p['tax_rate'])
                updated=(funding_gap+funding_interest-benefit)*p['new_debt_rate']*duration*.5
                if abs(updated-funding_interest)<1e-10:break
                funding_interest=updated
        if funding_interest:
            benefit=min(tax_future,funding_interest*p['tax_rate'])
            pbt-=funding_interest;tax-=benefit;parent-=funding_interest-benefit;group-=funding_interest-benefit
            group_future-=funding_interest-benefit
            eps=parent*1e6/basic_shares;recurring_eps=(parent-recurring_adjustment)*1e6/basic_shares
            cfo_future-=funding_interest-benefit;cfo-=funding_interest-benefit;close_cash-=funding_interest-benefit
            funding_gap=max(0,-close_cash)
        next_current=min(close_debt,h['long_debt']/3)
        noncurrent_debt=max(0,close_debt-next_current)
        close_capital=capital+group_future+sbc_future-dividends_future+(noncurrent_debt-prior_noncurrent_debt)
        open_annual_capital=fy['capital_employed'] if first else capital
        row={'period_end':f'{2027+j}-01-31','label':f'FY1/{27+j}E','sales_m':sales,
            'business_sales_m':copy.deepcopy(business),'business_reconciliation_m':reconciliation,
            'personnel_m':personnel,'advertising_m':ads,'other_operating_costs_m':other,
            'asset_da_m':asset_da,'goodwill_amortization_m':goodwill,'sbc_m':p['sbc_annual'][j],
            'op_m':op,'op_margin_pct':op/sales*100,'pbt_m':pbt,'tax_m':tax,'nci_profit_m':nci,
            'parent_profit_m':parent,'weighted_basic_shares':basic_shares,'basic_eps':eps,
            'recurring_basic_eps':recurring_eps,'economic_option_adjusted_eps':parent*1e6/(basic_shares+a['identified_options']),
            'cash_capex_m':capex,'prepaid_investment_m':prepaid,'cfo_m':cfo,'operating_fcf_m':cfo-capex-prepaid,
            'parent_dividend_cash_m':div,'debt_repayment_future_m':repayment,'closing_debt_m':close_debt,
            'cash_opening_future_period_m':cash,'cash_flow_forecast_duration_years':duration,
            'cfo_future_period_m':cfo_future,'capex_future_period_m':capex_future,'prepaid_future_period_m':prepaid_future,
            'dividend_future_period_m':dividends_future,'closing_cash_m':close_cash,'funding_gap_m':funding_gap,
            'new_funding_interest_m':funding_interest,'working_capital_changes_m':wc_changes,
            'closing_working_capital_balances_m':closing_nwc,'working_capital_investment_m':dwc,
            'staffing_elasticity':staff_elasticity,'other_cost_elasticity':other_e,
            'minority_future_period_m':minority,'closing_legacy_asset_book_m':legacy_book,
            'closing_new_asset_book_m':sum(c['book'] for c in cohorts),'closing_goodwill_m':gw_book,
            'closing_capital_employed_m':close_capital,'average_cash_inclusive_roce_pct':op/((open_annual_capital+close_capital)/2)*100}
        annual.append(row)
        cash,debt,capital=close_cash,close_debt,close_capital
        prior_nwc=closing_nwc;prior_noncurrent_debt=noncurrent_debt
        last_sales,last_noninsurance=sales,noninsurance
    return annual

def build(a,p):
    cases={c:run(a,p,c) for c in ['bear','base','bull']}
    tests={
      'Advertising intensity +10% each year':{'ad_intensity_annual_change':.10},
      'Staffing follows activity fully':{'staff_elasticity_override':1.0},
      'Other costs follow activity fully':{'other_cost_elasticity':1.0},
      'Software life three years':{'software_life':3},
      'CIP depreciation starts one year later (accounting only)':{'cip_commission_h2_fraction':0},
      'Tax rate +5 percentage points':{'tax_rate':p['tax_rate']+.05},
      'Nonparent annual profit 60m':{'nci_annual_override':60},
      'Working capital +15 receivable days':{'working_capital_days_add':15},
      'Capex +25% and collection +15days':{'capex':[x*1.25 for x in p['capex']],'working_capital_days_add':15}}
    sensitivity=[]
    base=cases['base'][-1]
    for name,overrides in tests.items():
        rows=run(a,p,'base',overrides);r=rows[-1]
        sensitivity.append({'name':name,'assumptions_changed':overrides,'fy30_op_m':r['op_m'],
            'fy30_basic_eps':r['basic_eps'],'eps_change_vs_base':r['basic_eps']-base['basic_eps'],
            'fy30_closing_cash_m':r['closing_cash_m'],'minimum_closing_cash_m':min(x['closing_cash_m'] for x in rows),
            'maximum_funding_gap_m':max(x['funding_gap_m'] for x in rows),
            'fy30_average_cash_inclusive_roce_pct':r['average_cash_inclusive_roce_pct']})
    return {'schema_version':1,'ticker':a['ticker'],'company':a['company'],'research_date':a['cutoff'],
      'model_version':p['version'],'method':'Seven issuer-specific management-business revenue paths; observed expense pools and funded asset cohorts.',
      'units':'JPY million except shares, EPS and percentages','cases':cases,'sensitivities':sensitivity,
      'confidence':'Medium on disclosed starting accounts; low to medium on forward cost responsiveness and service growth.',
      'basis_notes':[
       'FY1/27 combines reported H1 with a separate H2 forecast. Displayed CFO and capex are full fiscal-year amounts.',
       'Basic EPS includes known reported H1. Recurring_basic_eps separately removes the identified parent net one-off4.962m at assumed tax31.5%; no speculative NCI normalization.',
       'Future group tax rate31.5% plus assumed nondeductible goodwill. No new loss-tax-credit benefit.',
       'Management business figures are rounded and not statutory segments; a separate scope/reconciliation line is retained.',
       'Rent expense remains in observed operating costs. Forecasts use a comparable after-rent basis; issuer expects new lease accounting from FY1/29 but has not quantified its effect.',
       'Cash is consolidated, including regulated/guarantee businesses, and is not wholly distributable. Cash conversion, reserves and NCI sensitivities remain material.',
       'ROCE=OP/average(assets−current liabilities), on the modeled comparable basis. Opening source balances and retained earnings/SBC/noncurrent debt roll forward; other noncurrent balances/OCI are held flat.',
       'Full identified option overhang is an economic sensitivity, not GAAP diluted EPS. No exercise cash or unannounced M&A/buyback is credited.'
      ]}

if __name__=='__main__':
    result=build(load('actuals.json'),load('assumptions.json'))
    (HERE/'forecast.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({c:[{'year':r['label'],'sales':r['sales_m'],'op':r['op_m'],'eps':r['basic_eps'],'cash':r['closing_cash_m']} for r in rows] for c,rows in result['cases'].items()},ensure_ascii=False,indent=2))
