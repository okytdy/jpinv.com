"""Dai-Dan: auditable financial-capacity and fixed-bid order-vintage model.

JPY millions except EPS and million shares. No guidance file is imported.
Revenue-equivalent capacity is a financial proxy, not measured physical units.
"""
import copy,json
from pathlib import Path


def evaluate(inputs,case='base'):
    a=inputs['actual'];p=inputs['cases'][case];c=inputs['conventions']
    h=a['h1'];prior=a['prior_h1'];fy=a['prior_fy']
    h2_sales=(fy['revenue']-prior['revenue'])*(h['revenue']/prior['revenue'])*p['h2_delivery_factor']
    direct_da=h['da']-h['sga_da'];prior_direct=prior['da']-prior['sga_da']
    improvement=(h['gross_profit']+direct_da)/h['revenue']-(prior['gross_profit']+prior_direct)/prior['revenue']
    historical_h2_cash_gp=(fy['gross_profit']-prior['gross_profit']+fy['da']-fy['sga_da']-prior_direct)/(fy['revenue']-prior['revenue'])
    cash_gp_rate=historical_h2_cash_gp+improvement*p['improvement_carry']
    def cash_sga(row):
        return row['sga']-row['sga_da']-row['goodwill_amort']-row['pension_expense']-row['equity_pay']
    h2_cash_sga=(cash_sga(fy)-cash_sga(prior))*cash_sga(h)/cash_sga(prior)
    h2_gp=h2_sales*cash_gp_rate-direct_da
    h2_sga=h2_cash_sga+h['sga_da']+h['goodwill_amort']+h['pension_expense']+h['equity_pay']
    first_sales=h['revenue']+h2_sales
    # H1 minus-one source rounding is explicit; forecast periods have none.
    first_rounding=h['ebit']-(h['gross_profit']-h['sga'])
    first_gp=h['gross_profit']+h2_gp
    first_sga=h['sga']+h2_sga
    base_cash_cost_ratio=(first_sales-first_gp-2*direct_da)/first_sales
    people_share=h['cash_people_cost']/cash_sga(h)
    annual_cash_sga=cash_sga(h)+h2_cash_sga
    recurring_nonop=a['ttm_recurring_nonop_before_interest']
    pension=2*h['pension_expense'];equity_pay=2*h['equity_pay'];gw=2*h['goodwill_amort']
    cash=a['cash'];debt=a['debt'];equity=a['equity'];wc=a['receivables']+a['inventory']-a['payables']-a['advances']
    other_deposits=a['other_deposits']
    nci_book=a['nci_book'];ncl=a['nondebt_noncurrent_liabilities']
    annual=[];book=[];cohort_log=[]
    cohorts=[dict(vintage='opening_2026-09',remaining=x['backlog'],bid_index=1.0,cost_factor=1.0,lane=lane) for lane,x in a['lanes'].items()]
    recognition_limit=(fy['revenue']-prior['revenue'])/a['prior_september_backlog']
    reference_capacity=first_sales
    bid_index=1.;cost_factor=1.;cost_new=a['parent_direct_labor']/a['parent_construction_cost']
    base_ppe=2*h['ppe_cash_spend'];base_da=2*h['da'];da_cohorts=[]
    prior_capacity=reference_capacity
    for year in range(4):
        periods=1 if year==0 else 2
        if year:
            reference_capacity*= (1+p['headcount_growth'])*(1+p['productivity_growth'])
            bid_index*=1+p['new_bid_price_growth']
            # Vintage incremental cost/price factors are locked. Aggregate recognition cost profile changes from H2 to full-year mix; not fixed project-level budgets.
            cost_factor*=((1-cost_new)*(1+p['nonlabor_input_growth'])+cost_new*(1+p['pay_growth'])/(1+p['productivity_growth']))/(1+p['new_bid_price_growth'])
        recognized=[];lane_sales={lane:0. for lane in a['lanes']};costs=0.;revenue=0.
        for half in range(periods):
            opening=sum(x['remaining'] for x in cohorts)
            allowed={id(x):x['remaining']*min(1.,recognition_limit*p['recognition_factor']) for x in cohorts}
            new_orders=0.
            for lane,anchor in a['lanes'].items():
                orders=anchor['ttm_orders']/2*(1+p['orders_growth'])**(year+1)
                cohort=dict(vintage=f'FY{2027+year}-H{half+1}',remaining=orders,bid_index=bid_index,cost_factor=cost_factor,lane=lane)
                cohorts.append(cohort)
                # Uniform award arrival: half the opening-book exposure, with parallel execution.
                allowed[id(cohort)]=orders*min(1.,recognition_limit*p['recognition_factor'])*c['new_order_halfyear_exposure']
                new_orders+=orders
            cap=h2_sales if year==0 else reference_capacity/2
            half_sales=0.;half_cost=0.;used_capacity=0.
            for cohort in cohorts:
                # Parallel projects; pro-rata eligible workload within each observed revenue lane.
                lane_share=a['lanes'][cohort['lane']]['h1_revenue']/sum(x['h1_revenue'] for x in a['lanes'].values())
                eligible=sum(allowed[id(x)]/x['bid_index'] for x in cohorts if x['lane']==cohort['lane'])
                scale=min(1.,cap*lane_share/eligible) if eligible else 0.
                reference=allowed[id(cohort)]/cohort['bid_index']*scale
                nominal=reference*cohort['bid_index'];cohort['remaining']-=nominal
                ratio=1-cash_gp_rate if year==0 else base_cash_cost_ratio
                unbudgeted=p['legacy_overrun'] if cohort['vintage']=='opening_2026-09' else 0.
                cost=nominal*ratio*cohort['cost_factor']*(1+unbudgeted)
                recognized.append(dict(year=year,half=half,lane=cohort['lane'],vintage=cohort['vintage'],revenue=nominal,reference_revenue=reference,bid_index=cohort['bid_index'],cost_factor=cohort['cost_factor'],cash_cost=cost))
                half_sales+=nominal;half_cost+=cost;used_capacity+=reference;lane_sales[cohort['lane']]+=nominal
            closing=sum(x['remaining'] for x in cohorts)
            book.append(dict(year=year,half=half,opening=opening,orders=new_orders,revenue=half_sales,closing=closing,identity_error=opening+new_orders-half_sales-closing,reference_capacity=cap,used_reference_capacity=used_capacity))
            revenue+=half_sales;costs+=half_cost
        cohort_log.extend(recognized)
        # Current H1 actuals are never reconstructed from a cost ratio.
        if year==0:
            revenue+=h['revenue'];lane_sales={k:v+a['lanes'][k]['h1_revenue'] for k,v in lane_sales.items()}
            # Headline versus two disclosed lanes is issuer rounding, not another business.
            lane_rounding=h['revenue']-sum(x['h1_revenue'] for x in a['lanes'].values())
            gp=h['gross_profit']+(revenue-h['revenue']-costs)-direct_da
            cash_expense=annual_cash_sga;da=base_da;sga_da=2*h['sga_da']
        else:
            lane_rounding=0.
            real_ratio=reference_capacity/prior_capacity
            annual_cash_sga*=people_share*(1+p['headcount_growth'])*(1+p['pay_growth'])+(1-people_share)*real_ratio*(1+p['nonlabor_input_growth'])
            cash_expense=annual_cash_sga
            da=base_da+sum(x['annual_da'] for x in da_cohorts)
            sga_da=da*h['sga_da']/h['da']
            gp=revenue-costs-(da-sga_da)
        ppe=base_ppe*(reference_capacity/first_sales)
        expansion=max(0.,ppe-base_da)
        incremental_da=expansion/p['asset_life']
        # Half-year commissioning convention for identified net expansion; maintenance replaces run-off.
        new_da=incremental_da/2
        if year==0:new_da/=2
        da+=new_da;sga_da+=new_da*h['sga_da']/h['da'];gp-=new_da*(1-h['sga_da']/h['da'])
        da_cohorts.append(dict(annual_da=incremental_da))
        pension_recognized=h['pension_expense']*(1+p['pension_credit_carry']) if year==0 else pension*p['pension_credit_carry']
        sga=cash_expense+sga_da+gw+pension_recognized+equity_pay
        rounding=first_rounding if year==0 else 0.
        ebit=gp-sga+rounding
        shares=(a['h1_weighted_shares_m']+a['closing_eps_shares_m'])/2 if year==0 else a['closing_eps_shares_m']
        duration=.5 if year==0 else 1.
        interest=debt*p['debt_interest_rate']*duration
        nonop=recurring_nonop
        # Actual H1 recurring normalization uses its own observed tax/NCI; future uses TTM tax proxy.
        h1_norm=h['parent_profit']-h['extraordinary_net']*(1-h['tax']/h['pbt'])*(1-h['nci']/h['group_profit'])
        if year==0:
            future_op=ebit-h['ebit'];pbt=(future_op+nonop/2-interest)
            tax=max(0.,pbt)*p['tax_rate'];nci=(pbt-tax)*p['nci_claim_rate']
            parent=h1_norm+pbt-tax-nci
        else:
            pbt=ebit+nonop-interest;tax=max(0.,pbt)*p['tax_rate'];nci=(pbt-tax)*p['nci_claim_rate'];parent=pbt-tax-nci
        annual_revenue=revenue
        # Same-date observable WC intensities; half-year uses annual run rate.
        receivables=annual_revenue*(a['receivables']/(2*h['revenue'])+p['collection_delay_days']/c['days_in_year'])
        inventory=annual_revenue*a['inventory']/(2*h['revenue'])
        payables=(annual_revenue-gp)*a['payables']/(2*(h['revenue']-h['gross_profit']))
        advances=sum(x['remaining'] for x in cohorts)*a['advances']/sum(x['backlog'] for x in a['lanes'].values())
        new_wc=receivables+inventory-payables-advances
        wc_change=new_wc-wc
        deposit_use=other_deposits*p['other_deposit_unwind']*duration
        other_deposits-=deposit_use
        other_investing=2*h['other_investing_outflow']*duration
        dividends=a['declared_interim_cash'] if year==0 else max(0.,parent)*p['payout']*a['dividend_eligible_shares_m']/shares
        # The FY3/27 final dividend is paid next fiscal year; future year includes prior final + current interim proxy.
        if year:
            previous_final=a['announced_final_dps']*a['dividend_eligible_shares_m'] if year==1 else max(0.,annual[-1]['recurring_parent_profit'])*p['payout']*.5*a['dividend_eligible_shares_m']/annual[-1]['shares_m']
            dividends=previous_final+max(0.,parent)*p['payout']*.5*a['dividend_eligible_shares_m']/shares
        # From September cash only the remaining half-year earnings/cash adjustments enter FY0.
        cash_earnings=parent-h1_norm if year==0 else parent
        adj_da=da-h['da'] if year==0 else da
        # Observed CF adjustment is not a disclosed contribution. Its unresolved
        # total-P&L/direct-cost scope stays a funding proxy, never a pension cash fact.
        pension_cf=2*(h['pension_cf_adjustment']+h['pension_expense']*(p['pension_credit_carry']-1))*duration
        cashflow=cash_earnings+nci+adj_da+gw*duration+equity_pay*duration+pension_cf-wc_change-deposit_use
        principal=min(debt,a['annual_principal_runrate']*duration)
        cash_before=cash+cashflow-ppe*duration-other_investing-dividends-principal
        minimum=annual_revenue*p['liquidity_months']/c['months_in_year']
        payout_fraction=0. if year==0 else p['payout']*.5*a['dividend_eligible_shares_m']/shares
        fixed_dividend=dividends-max(0.,parent)*payout_fraction
        initial_parent=parent;initial_pbt=pbt;initial_tax=tax;initial_cf=cashflow;initial_dividends=dividends
        def funded(draw):
            extra_interest=draw*p['debt_interest_rate']*duration/2
            funded_pbt=initial_pbt-extra_interest
            # No unverified immediate tax refund or deferred-tax asset in loss stress.
            funded_tax=max(0.,funded_pbt)*p['tax_rate']
            group_change=(funded_pbt-funded_tax)-(initial_pbt-initial_tax)
            funded_parent=initial_parent+group_change*(1-p['nci_claim_rate'])
            funded_dividend=fixed_dividend+max(0.,funded_parent)*payout_fraction
            funded_cash=cash_before+draw+group_change-(funded_dividend-initial_dividends)
            return funded_cash,extra_interest,funded_pbt,funded_tax,funded_parent,funded_dividend,initial_cf+group_change
        draw=0.
        if cash_before<minimum:
            lo=0.;hi=max(1.,minimum-cash_before)
            while funded(hi)[0]<minimum:hi*=2
            for _ in range(80):
                mid=(lo+hi)/2
                if funded(mid)[0]<minimum:lo=mid
                else:hi=mid
            draw=hi
        cash,extra_interest,pbt,tax,parent,dividends,cashflow=funded(draw)
        interest+=extra_interest;nci=(pbt-tax)*p['nci_claim_rate']
        cash_earnings=parent-h1_norm if year==0 else parent
        debt=debt-principal+draw
        equity+=cash_earnings-dividends
        nci_book+=nci
        capital=equity+nci_book+ncl+debt
        row=dict(period_end=f'{2027+year}-03-31',revenue=revenue,lane_revenue=lane_sales,lane_rounding=lane_rounding,gross_profit=gp,sga=sga,reported_rounding=rounding,ebit=ebit,op_margin=ebit/revenue,cash_construction_cost=revenue-gp-(da-sga_da),cash_sga=cash_expense,da=da,sga_da=sga_da,goodwill_amort=gw,pension_expense=pension_recognized,equity_pay=equity_pay,recurring_nonop=nonop,interest=interest,forward_pbt=pbt,forward_tax=tax,forward_nci=nci,recurring_parent_profit=parent,recurring_eps=parent/shares,shares_m=shares,cash=cash,debt=debt,cashflow=cashflow,cash_ppe=ppe*duration,other_investing=other_investing,dividend_cash=dividends,principal=principal,draw=draw,working_capital=new_wc,wc_change=wc_change,other_deposit_cash_use=deposit_use,cash_inclusive_capital_proxy=capital,roce_cash_inclusive_proxy=ebit/capital,closing_backlog=sum(x['remaining'] for x in cohorts),reference_capacity=reference_capacity,new_bid_index=bid_index)
        annual.append(row);wc=new_wc;prior_capacity=reference_capacity
    growth=(annual[-1]['recurring_eps']/annual[0]['recurring_eps'])**(1/3)-1 if annual[-1]['recurring_eps']>0 and annual[0]['recurring_eps']>0 else None
    return dict(annual=annual,backlog_rollforwards=book,recognized_vintages=cohort_log,capacity_note='Reference-price revenue-equivalent capacity; parallel fixed-bid-price vintages and aggregate recognition-cost profiles; not disclosed physical volume or absolute project budgets.',anchors=dict(h2_cash_gp_rate=cash_gp_rate,h1_cash_gp_improvement=improvement,prior_h2_cash_gp_rate=historical_h2_cash_gp,current_h2_cash_sga=h2_cash_sga,cash_cogs_ratio=base_cash_cost_ratio,sga_people_weight=people_share,recognition_halfyear_limit=recognition_limit,h1_recurring_parent=h1_norm),eps_cagr=growth)


if __name__=='__main__':
    inputs=json.loads((Path(__file__).parent/'INPUTS.json').read_text('utf-8'))
    print(json.dumps({'cases':{case:evaluate(inputs,case) for case in inputs['cases']}},ensure_ascii=False,indent=2,allow_nan=False))
