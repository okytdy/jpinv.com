"""HAMAKYOREX independent financial-proxy scenarios. Python standard library.
Run this file to regenerate outputs and checks. JPYm / absolute shares / yen EPS.
Guidance is never imported; management_comparator.md is a later editorial comparison.
"""
from pathlib import Path
import json, copy, csv, hashlib, math
ROOT=Path(__file__).resolve().parent
def read(name): return json.loads((ROOT/name).read_text(encoding='utf-8-sig'))
def save(name,value): (ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def finance(op,da,sales,opening,capex,new_leases,lease_pay,years,common,case,nci,dividend=None,special_loss=0):
    """Half-year/full-year cash roll from Sep2026; interest includes average new draw."""
    c=common; rate=case['borrow_rate'];tax=case['tax_rate']
    ar=sales*c['ar_days']/365;ap=sales*c['ap_days']/365;inv=sales*c['inventory_days']/365
    # Receivable/payable days use annualized run rate, including FY27 H2 funding.
    wc=(ar-opening['ar'])+(inv-opening['inventory'])-(ap-opening['ap'])+c['other_wc_outflow']*years
    repay=min(opening['debt'],c['annual_debt_amortization']*years)
    other=(c['other_recurring_nonop']+opening['cash']*c['cash_yield'])*years
    def calc(draw):
        interest=(opening['debt']-repay/2+draw/2)*rate*years+(opening['lease_debt']+(new_leases-lease_pay)/2)*c['lease_interest_rate']*years
        pbt=op+other-interest; net=pbt*(1-tax);parent=net-nci
        div=max(parent,0)*c['dividend_payout'] if dividend is None else dividend
        nci_div=nci*c['nci_payout'];cfo=net+da-wc
        cash=opening['cash']+cfo-capex-lease_pay-div-nci_div-repay+draw
        return dict(interest=interest,recurring_other_nonop=other,pbt=pbt,tax=pbt*tax,group_net=net,nci=nci,parent=parent,dividends=div,nci_dividends=nci_div,cfo=cfo,cash=cash)
    # Solve draw algebraically; a fixed dividend has no dividend offset to interest.
    zero=calc(0);need=max(0,c['minimum_cash']-zero['cash'])
    retained=1 if dividend is not None else 1-c['dividend_payout']
    draw=need/(1-rate*years/2*(1-tax)*retained)
    z=calc(draw);z.update(debt=opening['debt']-repay+draw,new_borrowing=draw,debt_repayment=repay,
       lease_debt=opening['lease_debt']+new_leases-lease_pay,new_leases=new_leases,lease_principal=lease_pay,
       receivables=ar,payables=ap,inventory=inv,wc_outflow=wc,capex=capex,
       business_fcf_after_leases=z['cfo']-capex-lease_pay,
       parent_equity=opening['equity']+z['parent']-z['dividends'],
       nci_equity=opening['nci_equity']+nci-z['nci_dividends'])
    z['cash_roll_error']=z['cash']-(opening['cash']+z['cfo']-capex-lease_pay-z['dividends']-z['nci_dividends']-repay+draw)
    # Defined broad capital measure, not statutory company ROCE.
    capital0=opening['equity']+opening['nci_equity']+opening['debt']+opening['lease_debt']
    capital1=z['parent_equity']+z['nci_equity']+z['debt']+z['lease_debt']
    z['cash_inclusive_roic_proxy']=op/years/((capital0+capital1)/2)
    z['annualized_op_capital_proxy']=op/years
    return z

def next_open(z):
    return dict(cash=z['cash'],debt=z['debt'],lease_debt=z['lease_debt'],ar=z['receivables'],ap=z['payables'],inventory=z['inventory'],equity=z['parent_equity'],nci_equity=z['nci_equity'])

def run_case(a,assumptions,name,overrides=None):
    c=copy.deepcopy(assumptions['common']);k=copy.deepcopy(assumptions['cases'][name])
    if overrides:c.update(overrides.get('common',{}));k.update(overrides.get('case',{}))
    assert 0<=k['center_new_contract_fraction']<=c['max_new_center_contract_revenue_fraction'], 'new contract proxy exceeds historical feasibility envelope'
    assert c['shares']>0 and c['growth_asset_life']>0
    h=a['H1'];f=a['FY26'];hp=a['prior_H1'];segments={};h2segs={}
    # Freeze latest H1 actual profits. DA allocation is an explicitly uncertain cash-cost proxy.
    for name2 in ['center','truck']:
        s=h['segments'][name2];fy=f['segments'][name2];prior=hp['segments'][name2]
        seasonal=(fy['sales']-prior['sales'])/prior['sales']
        h2sales=s['sales']*seasonal*(1+k['h2_'+name2+'_vs_h1_seasonal'])
        # Allocate the uncertain central DA proxy into segment cash-cost anchors;
        # group OP already embeds corporate accounting. It is never an extra OP deduction.
        h1da=c['fy27_h1_da_proxy_'+name2]+c['fy27_h1_central_da_proxy']*c['fy27_h1_da_proxy_'+name2]/(c['fy27_h1_da_proxy_center']+c['fy27_h1_da_proxy_truck'])
        fixedshare=c['cash_fixed_share_'+name2]
        cash=s['sales']-s['op']-h1da
        # Preserve observed H2 cost seasonality (including Q4 bonus/site costs),
        # rather than manufacture a seasonal fixed-cost leverage windfall.
        prior_half_da=(fy['da']+fy['goodwill'])/2
        prior_h1_cash=prior['sales']-prior['op']-prior_half_da
        prior_h2_cash=(fy['sales']-prior['sales'])-(fy['op']-prior['op'])-prior_half_da
        cost_seasonal=prior_h2_cash/prior_h1_cash
        h2cash=cash*cost_seasonal*(fixedshare+(1-fixedshare)*(1+k['h2_'+name2+'_vs_h1_seasonal']))*(1+k['h2_unit_cost_pressure'])
        # Named commitments are not commissioned during H2 FY27. Only additional
        # discretionary growth spend is allowed a half-of-half-year DA convention.
        committed_h2=sum(p['cash_H2FY27'] for p in c['committed_projects'])
        extra_h2=max(0,c['fy27_h2_growth_capex']-committed_h2)
        lease_h2_da=(c['annual_lease_new']/2)/c['lease_asset_life']/4
        h2da=h1da+(extra_h2*(1-c['land_share_growth_spend'])/c['growth_asset_life']/4+lease_h2_da)*(c['center_share_new_capex'] if name2=='center' else 1-c['center_share_new_capex'])
        h2segs[name2]=dict(sales=h2sales,da=h2da,cash_cost=h2cash,op=h2sales-h2cash-h2da)
        segments[name2]=dict(sales=s['sales']+h2sales,op=s['op']+h2sales-h2cash-h2da,da=h1da+h2da,cash_cost=cash+h2cash)
    h2op=sum(x['op'] for x in h2segs.values())-19/2
    h2da=sum(x['da'] for x in h2segs.values())
    # Central DA is added to segment cash-flow addback, not deducted twice from segment OP.
    opening=dict(cash=h['cash_deposits']-c['unavailable_time_deposits'],debt=h['short_debt']+h['long_debt'],lease_debt=c['opening_lease_debt_proxy'],ar=h['ar'],ap=h['ap'],inventory=h['inventory'],equity=h['equity'],nci_equity=h['nci_equity'])
    fullsales=sum(x['sales'] for x in segments.values())
    nci_h2=(f['nci_net']-hp['nci_net'])*(1+k['nci_pool_growth'])
    z=finance(h2op,h2da,fullsales,opening,c['fy27_h2_capex'],c['annual_lease_new']/2,c['annual_lease_principal']/2,0.5,c,k,nci_h2,dividend=c['fy27_h2_declared_interim_dividend_yen']*c['shares']/1e6)
    # FY27 H1 reported parent includes settlement182m. Normalize only the identified settlement,
    # taxed at the observed H1 effective rate, at 100% parent attribution (explicit assumption).
    settlement_aftertax=h['settlement_loss']*(1-h['tax']/h['pbt'])
    parent_rec=h['parent_net']+settlement_aftertax+z['parent']
    fy0shares=(h['weighted_shares']*183+c['shares']*182)/365
    row=dict(year=2027,label='FY0',period_end='2027-03-31',sales=fullsales,op=h['op']+h2op,da=sum(v['da'] for v in segments.values()),
        parent_recurring=parent_rec,parent_reported_like=parent_rec-settlement_aftertax,
        eps=parent_rec*1e6/fy0shares,reported_like_eps=(parent_rec-settlement_aftertax)*1e6/fy0shares,segments=segments,
        funding_period='2026-10-01 to 2027-03-31 only; H1 cash flow unavailable at cutoff',funding=z,shares=fy0shares,
        unallocated_op_adjustment=h['op_elimination_rounded']-19/2,
        fiscal_capex_envelope_not_actual=c['fy27_h2_capex']*2)
    rows=[row];opening=next_open(z);legacy_da=sum(s['da']+s['goodwill'] for s in f['segments'].values())+f['central_da']
    # Rebase legacy D&A to FY27 annual proxy. Runoff offsets replacement cohorts.
    legacy_da=row['da']-lease_h2_da;cohorts=[];kin=f['kinbutsu']['net_profit'];other_nci=f['nci_net']-kin*(1-f['kinbutsu']['parent_ownership'])
    # Scale pool to current annual NCI (H1+modeled H2), then grow pools independently.
    nci0=h['nci_net']+nci_h2;kin0=kin*(1+k['kinbutsu_net_growth']);nci_other0=nci0-kin0*0.27
    for j,year in enumerate([2028,2029,2030]):
        old=rows[-1];newsegs={}
        committed_cash=sum(p.get('cash_FY'+str(year-2000),0) for p in c['committed_projects'])
        assert c['annual_growth_capex'][j]>=committed_cash,'capex envelope below named commitments'
        discretionary=(c['annual_growth_capex'][j]-committed_cash)*k['growth_capex_multiplier']
        growthcap=committed_cash+discretionary;maint=c['maintenance_cash_capex']*(1+c['fixed_inflation'])**j
        # D&A spend cohorts: land excluded; half-year convention at commissioning.
        cohorts.append(dict(year=year,growth=discretionary*(1-c['land_share_growth_spend']),maint=maint))
        committed_da=sum(p['basis']/p['life']*p['fraction_FY'+str(year-2000)] for p in c['committed_projects'])
        lease_da=c['legacy_lease_da_proxy']*(1-1/c['lease_asset_life'])**(j+1)+(c['annual_lease_new']/2)/c['lease_asset_life']+sum(c['annual_lease_new']/c['lease_asset_life']*(0.5 if yy==year else 1) for yy in range(2028,year+1))
        nonlease_legacy=legacy_da-c['legacy_lease_da_proxy']
        da=nonlease_legacy*(1-c['legacy_da_runoff'])**(j+1)+sum((q['growth']/c['growth_asset_life']+q['maint']/c['maintenance_asset_life'])*(0.5 if q['year']==year else 1) for q in cohorts)+committed_da+lease_da
        for name2 in ['center','truck']:
            prev=old['segments'][name2];fixedshare=c['cash_fixed_share_'+name2]
            if name2=='center':
                activity=(1+k['center_volume'])*(1-k['center_churn']);newrev=prev['sales']*k['center_new_contract_fraction']
                sales=prev['sales']*activity*(1+k['center_price'])+newrev
                # New-revenue proxy is defined at prior-year rates; no extra price uplift added.
                physical_proxy=activity+newrev/prev['sales'];productivity=k['center_productivity']
            else:
                physical_proxy=1+k['truck_volume'];newrev=0;sales=prev['sales']*physical_proxy*(1+k['truck_price']);productivity=k['truck_productivity']
            unitinfl=c['labor_share_of_cash_cost']*k['wage_inflation']+(1-c['labor_share_of_cash_cost'])*k['other_variable_inflation']
            recurring_cash=prev['cash_cost']-prev.get('startup_cost',0)
            var=recurring_cash*(1-fixedshare)*physical_proxy*(1+unitinfl)*(1-productivity)
            fixed=recurring_cash*fixedshare*(1+c['fixed_inflation'])
            # Fixed capacity added for new business. A 30% fixed share scales only the
            # new work, and represents staff/rent expansion; no free site capacity.
            fixed+=recurring_cash*fixedshare*(newrev/prev['sales'])
            startup=newrev*k['new_contract_startup_cost_rate']
            share=prev['da']/sum(v['da'] for v in old['segments'].values())
            segda=da*share;cash=var+fixed+startup
            newsegs[name2]=dict(sales=sales,op=sales-cash-segda,da=segda,cash_cost=cash,
               new_contract_revenue_proxy=newrev,variable_cash_cost=var,fixed_cash_cost=fixed,startup_cost=startup,
               activity_proxy=physical_proxy,price=k[name2+'_price'])
        op=sum(s['op'] for s in newsegs.values())-19;rev=sum(s['sales'] for s in newsegs.values())
        kinprofit=kin0*(1+k['kinbutsu_net_growth'])**(j+1)
        pool=nci_other0*(1+k['nci_pool_growth'])**(j+1);nci=0.27*kinprofit+pool
        z=finance(op,da,rev,opening,maint+growthcap,c['annual_lease_new'],min(opening['lease_debt']+c['annual_lease_new'],c['annual_lease_principal']),1,c,k,nci)
        z['kinbutsu_entity_net_proxy']=kinprofit;z['other_nci_claim_pool']=pool
        rows.append(dict(year=year,label='FY'+str(j+1),period_end=str(year)+'-03-31',sales=rev,op=op,da=da,parent_recurring=z['parent'],parent_reported_like=z['parent'],eps=z['parent']*1e6/c['shares'],reported_like_eps=z['parent']*1e6/c['shares'],segments=newsegs,funding_period='full fiscal year',funding=z,shares=c['shares'],unallocated_op_adjustment=-19,maintenance_cash_capex=maint,growth_cash_capex=growthcap,committed_project_cash=committed_cash,committed_project_da=committed_da,finance_lease_asset_da=lease_da))
        opening=next_open(z)
    return rows

def build(a,s):
    cases={k:run_case(a,s,k) for k in s['cases']};f=a['FY26'];h=a['H1'];hp=a['prior_H1']
    ttm_parent=f['parent_net']+h['parent_net']-hp['parent_net']
    # Apr-Sep183 days; Oct-Mar182. Reconstruct compatible post-split daily weights.
    h2shares=(365*f['weighted_shares']-183*hp['weighted_shares'])/182
    ttm_shares=(h2shares*182+h['weighted_shares']*183)/365
    norm_rate=f['tax']/f['pbt'];signed=-941*(1-norm_rate)-120-54*(1-norm_rate)-12*(1-norm_rate)+126*(1-norm_rate)
    normalization=[dict(label='Remove exceptional fixed-asset gain at parent company',pretax=-941,tax_offset=941*norm_rate,parent_aftertax=-941*(1-norm_rate),nci_aftertax=0),
      dict(label='Remove negative goodwill, assumed tax-free',pretax=-120,tax_offset=0,parent_aftertax=-120,nci_aftertax=0),
      dict(label='Remove investment-security gain',pretax=-54,tax_offset=54*norm_rate,parent_aftertax=-54*(1-norm_rate),nci_aftertax=0),
      dict(label='Remove other exceptional gain',pretax=-12,tax_offset=12*norm_rate,parent_aftertax=-12*(1-norm_rate),nci_aftertax=0),
      dict(label='Add back exceptional losses',pretax=126,tax_offset=-126*norm_rate,parent_aftertax=126*(1-norm_rate),nci_aftertax=0)]
    # Tax-free negative goodwill120; other gains/losses at observed ETR; assume parent100%.
    sensitivities=[];base=cases['base'][-1]
    variants=[('Center price recovery -1 percentage point each year',{'case':{'center_price':s['cases']['base']['center_price']-0.01}}),
      ('Center variable productivity -1 percentage point',{'case':{'center_productivity':s['cases']['base']['center_productivity']-0.01}}),
      ('Cash capex +JPY3bn per year and useful-life link',{'common':{'annual_growth_capex':[10302,8500,9000]}}),
      ('Receivables +10 days',{'common':{'ar_days':s['common']['ar_days']+10}}),
      ('Higher minority attribution at fixed consolidated earnings',{'case':{'nci_pool_growth':0.14}}),
      ('No nonlease legacy depreciation runoff',{'common':{'legacy_da_runoff':0.00}}),
      ('Unavailable Sep deposits JPY5bn rather than JPY1.721bn',{'common':{'unavailable_time_deposits':5000}}),
      ('Opening leases +JPY5bn and annual principal +JPY1bn',{'common':{'opening_lease_debt_proxy':11702,'annual_lease_principal':3100}}),
      ('Finance-lease assets depreciate over4 rather than5 years',{'common':{'lease_asset_life':4}}),
      ('FY27 H2 extra commissioned growth capex +JPY3bn',{'common':{'fy27_h2_capex':9400,'fy27_h2_growth_capex':6400}})]
    for label,over in variants:
        q=run_case(a,s,'base',over)[-1];sensitivities.append(dict(label=label,eps=q['eps'],delta_eps=q['eps']-base['eps'],op_delta=q['op']-base['op'],cash_delta=q['funding']['cash']-base['funding']['cash'],debt_delta=q['funding']['debt']-base['funding']['debt'],capital_return_delta=q['funding']['cash_inclusive_roic_proxy']-base['funding']['cash_inclusive_roic_proxy']))
    # Sequential bridge: effects depend on this declared order; they sum exactly.
    disabled={'center_volume':0,'center_churn':0,'center_new_contract_fraction':0,'truck_volume':0,'center_price':0,'truck_price':0,'wage_inflation':0,'other_variable_inflation':0,'center_productivity':0,'truck_productivity':0}
    bridge=[dict(label='FY0 recurring starting EPS',eps=cases['base'][0]['eps'],delta_eps=0,op=cases['base'][0]['op'])]
    stages=[('Capital/D&A, funding, tax/NCI and time; no operating growth',[],0),('Volume, churn and new customer-contract revenue',['center_volume','center_churn','center_new_contract_fraction','truck_volume'],0),('Contract price recovery',['center_price','truck_price'],0),('Wage, subcontract and fixed cost inflation',['wage_inflation','other_variable_inflation'],s['common']['fixed_inflation']),('Productivity',['center_productivity','truck_productivity'],s['common']['fixed_inflation'])]
    for label,keys,fixed in stages:
        for key in keys:disabled[key]=s['cases']['base'][key]
        q=run_case(a,s,'base',{'case':disabled,'common':{'fixed_inflation':fixed}})[-1]
        bridge.append(dict(label=label,eps=q['eps'],delta_eps=q['eps']-bridge[-1]['eps'],op=q['op'],delta_vs_reported_FY26_pct_of_baseline=(q['eps']-bridge[-1]['eps'])/f['reported_eps']))
    # Illustrative, observed minimum noncancellable lessee rent, not complete lease book.
    rent=3680;lease_rate=.03;term=4;pv=rent*(1-(1+lease_rate)**(-term))/lease_rate;liability=pv;lease_rows=[]
    for year in [2028,2029,2030]:
        interest=liability*lease_rate;dep=pv/term;principal=rent-interest
        pbt_delta=rent-dep-interest
        lease_rows.append(dict(year=year,op_delta=rent-dep,pbt_delta=pbt_delta,eps_delta=pbt_delta*(1-s['cases']['base']['tax_rate'])*1e6/s['common']['shares'],lease_interest=interest,lease_principal=principal,lease_liability_opening=liability,lease_liability_closing=liability-principal,pretax_total_cash_change=0))
        liability-=principal
    uncertain_norm_bound=sum(abs(x['parent_aftertax']) for x in normalization[1:])*.466*1e6/f['weighted_shares']
    return dict(as_of=a['as_of'],target='2030-03-31',basis='Independent financial proxies on constant pre-FY28-adoption lease economics; not a statutory new-lease-GAAP EPS forecast. No unannounced M&A profit, relay fees or subsidy income',anchors=dict(reported_FY26_eps=f['reported_eps'],normalized_FY26_parent=f['parent_net']+signed,normalized_FY26_eps=(f['parent_net']+signed)*1e6/f['weighted_shares'],signed_parent_normalization=signed,normalization_components=normalization,normalization_basis='after-tax parent approximation: observed FY26 ETR, negative goodwill tax-free; all adjustments100% parent except exact fixed-asset parent ownership verified; other attribution uncertain',uncertain_normalization_parent_attribution_gross_bound_eps=uncertain_norm_bound,ttm_parent=ttm_parent,ttm_weighted_shares=ttm_shares,ttm_eps=ttm_parent*1e6/ttm_shares,ttm_period='2025-10-01 to 2026-09-30'),cases=cases,sensitivities=sensitivities,base_sequential_eps_bridge=bridge,lease_accounting_illustration=dict(basis='Observed FY26 lessee noncancellable rent within one year3680m; assume four years flat and3% discount. Not statutory forecast: complete durations, exemptions, renewals and subsidiary allocation unavailable; issuer adopting FYMar2028. Annual report printed59/companyPDF62.',initial_liability=pv,rows=lease_rows),growth={k:dict(fy0_fy3_cagr=(v[-1]['eps']/v[0]['eps'])**(1/3)-1,target_vs_FY26_reported=(v[-1]['eps']/f['reported_eps'])-1,target_vs_FY26_annualized=(v[-1]['eps']/f['reported_eps'])**(1/4)-1,actual_baseline_to_target_years=4) for k,v in cases.items()})

def summary(out):
    lines=['# HAMAKYOREX independent three-year EPS outlook','',
      'Research cutoff: 5 November 2026. Target: FY ending31 March2030; FY0 is FY ending31 March2027. Amounts JPY million, EPS yen.',
      '', '**Base case: growing outsourced contract work and retained productivity raise economic recurring EPS, but labor and subcontract costs decide the result.** Regulation supplies a reason for customers to redesign logistics; it is not a margin or earnings guarantee.',
      '', '**Accounting basis: constant pre-FY2028 lease economics. These are independent pro-forma recurring estimates, not a precise forecast of statutory EPS after new lease-standard adoption.** Source YUHO states adoption from April2027, with impact unquantified. Operating rents remain in cash operating costs; finance-lease principal is separately funded.',
      '', '## Annual economic cases','', '| Case | FYMar2027 FY0 | FYMar2028 FY1 | FYMar2029 FY2 | FYMar2030 FY3 | FY0–FY3 CAGR |','|---|---:|---:|---:|---:|---:|']
    for k,rows in out['cases'].items():lines.append('| '+k+' | '+' | '.join(f"{r['eps']:.2f}" for r in rows)+f" | {out['growth'][k]['fy0_fy3_cagr']:.1%} |")
    an=out['anchors'];lines += ['',f"Reported FYMar2026 basic split-adjusted EPS is JPY{an['reported_FY26_eps']:.2f}; estimated normalized annual EPS JPY{an['normalized_FY26_eps']:.2f}. Latest reported TTM parent profit10,973m / daily-weighted shares{an['ttm_weighted_shares']:,.2f} =JPY{an['ttm_eps']:.2f} (October2025–September2026). No quarterly EPS is summed.",
      '',f"Base FYMar2030 EPS is {out['growth']['base']['target_vs_FY26_reported']:.1%} above FYMar2026 reported EPS over four fiscal years ({out['growth']['base']['target_vs_FY26_annualized']:.1%} annualized). The three-year CAGR uses estimated FY0 and FY3. These are different comparisons.",
      '', '## Base operating and funding path','', '| FY ending March | Sales | EBIT | Margin | D&A | Cash capex | Business FCF after finance-lease principal | Closing cash | Bank debt |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in out['cases']['base']:
        z=r['funding'];lines.append(f"| {r['year']} | {r['sales']:,.0f} | {r['op']:,.0f} | {r['op']/r['sales']:.1%} | {r['da']:,.0f} | {z['capex']:,.0f} | {z['business_fcf_after_leases']:,.0f} | {z['cash']:,.0f} | {z['debt']:,.0f} |")
    lines += ['', '**FY2027 cash capex/FCF cover only October2026–March2027.** H1 actual cash flows are not disclosed at the cutoff; the funding roll starts from actual September cash/debt. FY2027 annual D&A is a proxy, while full-year P&L includes actual H1. Finance leases begin at an explicitly uncertain6,702m proxy and remain visible separately from bank debt.',
      '', 'Named building commitments11,702m are reserved within the cash-capex envelopes and depreciated from their stated completion months. Reserving full March commitments after September may overstate remaining cash needed because H1 project spending is unknown. Future unannounced M&A earnings or acquisition cash, relay fees and subsidies are zero. Debt draws occur when the analyst liquidity reserve is needed and incur interest in the draw year; lender availability is an assumption.',
      '', '## Sequential FY0–FY3 EPS bridge','', '| Step (declared order) | Delta EPS | % of FYMar2026 reported EPS144.83 | Ending EPS |','|---|---:|---:|---:|']
    for q in out['base_sequential_eps_bridge']:
        lines.append(f"| {q['label']} | {q['delta_eps']:+.2f} | {q['delta_eps']/144.83:+.1%} | {q['eps']:.2f} |")
    lines += ['', 'The sequential attribution is order dependent. Price recovery largely offsets cost inflation; productivity supplies a material residual gain. The capital/time step includes replacement D&A, financing, nonoperating and minority claims and is not operating growth. Startup costs are removed from the recurring cost base after their initial cohort year.',
      '', '## Causal sensitivities: FYMar2030 versus base','', '| Change | EPS effect | % of FYMar2026 reported basic EPS144.83 | EBIT effect | Cash effect | Bank-debt effect |','|---|---:|---:|---:|---:|---:|']
    for q in out['sensitivities']:lines.append(f"| {q['label']} | {q['delta_eps']:+.2f} | {q['delta_eps']/144.83:+.1%} | {q['op_delta']:+,.0f} | {q['cash_delta']:+,.0f} | {q['debt_delta']:+,.0f} |")
    lines += ['', 'The cost split, realized price increases and new-contract contribution are bounded financial proxies. The model rejects an unsupported50% new-contract revenue fraction; it cannot establish exact physical center capacity because comparable floor area, throughput and customer fee data are not disclosed. Bear and bull are coherent economic stresses, not statistical confidence bounds.',
      '', '## Lease-adoption illustration','', 'Using the disclosed3,680m of noncancellable lessee payments due within one year, a purely illustrative four-year flat-rent cohort discounted at3% starts with13,679m of lease liability. It raises OP about260m/year while EPS effects are−1.35/−0.47/+0.44 in FY2028/29/30: −0.93%/−0.32%/+0.30% of the named FYMar2026 reported split-adjusted basic EPS144.83, before entity-allocation and tax-timing refinements. Total pretax cash is unchanged; classification changes. This is a source-anchored illustration of accounting timing, not the actual transition forecast. The full lease book, renewals, exemptions and discount rates remain unavailable.',
      '', '## Reproduction and limits','', 'Run `earnings_model.py` with Python3. It imports only actuals.json and assumptions.json and regenerates model_output.json, annual_cases.csv, validation.json and this summary. The operating model does not read management_comparator.md. Actual arithmetic, EPS, segments, annual cash rolls, extra borrowing interest, shares/NCI, commissioning and missing-driver tests are in validation.json; the completed independent review and separate target/sensitivity recomputations are in model_review.md.',
      '', 'Source locators, input bounds, rationale, normalization and falsifiers are in assumption_register.md. No previous9037 executable was replaced. Already known management forecasts cannot be mentally erased; computational separation and transparent cost equations establish the dependency boundary, not psychological independence.']
    return '\n'.join(lines)+'\n'

def validate(a,s,out):
    checks={};checks['H1_sales']=sum(x['sales'] for x in a['H1']['segments'].values())==a['H1']['revenue']
    checks['FY26_op']=sum(x['op'] for x in a['FY26']['segments'].values())+a['FY26']['op_elimination']==a['FY26']['op']
    checks['cash_rolls']=all(abs(r['funding']['cash_roll_error'])<1e-7 for rows in out['cases'].values() for r in rows)
    checks['eps_arithmetic']=all(abs(r['eps']-r['parent_recurring']*1e6/r['shares'])<1e-9 for rows in out['cases'].values() for r in rows)
    checks['segment_reconciliation']=all(abs(sum(x['op'] for x in r['segments'].values())+r['unallocated_op_adjustment']-r['op'])<1e-7 for rows in out['cases'].values() for r in rows)
    checks['contiguous_fiscal_periods']=all([r['year'] for r in rows]==[2027,2028,2029,2030] for rows in out['cases'].values())
    checks['draw_interest']=run_case(a,s,'base',{'common':{'minimum_cash':70000}})[-1]['funding']['interest']>out['cases']['base'][-1]['funding']['interest']
    checks['extra_capex_adds_da']=run_case(a,s,'base',{'common':{'annual_growth_capex':[10302,8500,9000]}})[-1]['da']>out['cases']['base'][-1]['da']
    checks['FY27_extra_capex_adds_da']=run_case(a,s,'base',{'common':{'fy27_h2_capex':9400,'fy27_h2_growth_capex':6400}})[0]['da']>out['cases']['base'][0]['da']
    delayed=copy.deepcopy(s['common']['committed_projects']);delayed[1]['fraction_FY28']=0
    checks['commissioning_delay_changes_da']=run_case(a,s,'base',{'common':{'committed_projects':delayed}})[1]['da']<out['cases']['base'][1]['da']
    checks['nci_mutation_propagates']=run_case(a,s,'base',{'case':{'nci_pool_growth':0.14}})[-1]['eps']<out['cases']['base'][-1]['eps']
    checks['share_mutation_propagates']=run_case(a,s,'base',{'common':{'shares':s['common']['shares']*1.1}})[-1]['eps']<out['cases']['base'][-1]['eps']
    try:run_case(a,s,'base',{'case':{'center_new_contract_fraction':0.5}});checks['impossible_capacity_envelope_rejected']=False
    except AssertionError:checks['impossible_capacity_envelope_rejected']=True
    missing=copy.deepcopy(s);del missing['cases']['base']['center_new_contract_fraction']
    try:run_case(a,missing,'base');checks['missing_driver_fails']=False
    except KeyError:checks['missing_driver_fails']=True
    # The rejected case is a bounded financial-proxy plausibility test, not a physical
    # capacity proof: exact site throughput, areas, rates and utilization are unavailable.
    checks['guidance_dependency']='No comparator file read by model; guidance absent from imported JSON schema'
    checks['status']='PASS' if all(v is not False for v in checks.values()) else 'FAIL'
    return checks

if __name__=='__main__':
    a=read('actuals.json');s=read('assumptions.json');out=build(a,s)
    save('model_output.json',out);save('validation.json',validate(a,s,out))
    (ROOT/'model_summary.md').write_text(summary(out),encoding='utf-8')
    fields=['case','year','sales','op','op_margin','da','parent_recurring','eps','cash','debt','lease_debt','capex','cfo','fcf_after_leases','nci','capital_return_proxy','funding_period']
    with (ROOT/'annual_cases.csv').open('w',newline='',encoding='utf-8-sig') as handle:
        writer=csv.DictWriter(handle,fields);writer.writeheader()
        for case,rows in out['cases'].items():
            for r in rows:
                z=r['funding'];writer.writerow(dict(case=case,year=r['year'],sales=r['sales'],op=r['op'],op_margin=r['op']/r['sales'],da=r['da'],parent_recurring=r['parent_recurring'],eps=r['eps'],cash=z['cash'],debt=z['debt'],lease_debt=z['lease_debt'],capex=z['capex'],cfo=z['cfo'],fcf_after_leases=z['business_fcf_after_leases'],nci=z['nci'],capital_return_proxy=z['cash_inclusive_roic_proxy'],funding_period=r['funding_period']))
    print(json.dumps({'validation':read('validation.json'),'base_eps':[r['eps'] for r in out['cases']['base']],'target_eps':{k:v[-1]['eps'] for k,v in out['cases'].items()}},indent=2))
