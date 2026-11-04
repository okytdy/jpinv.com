"""Takaoka own FY27–30 economic model; no guidance/valuation imported.

JPY million, shares absolute, EPS yen. Financial order/throughput/cost proxies
are explicit; the engine does not claim undisclosed physical units or fees.
"""
from pathlib import Path
from copy import deepcopy
import json,datetime as dt,math,csv
B=Path(__file__).parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
SEG=['power','meter','GX','optical']

def da(cohort,end):
 fyend=dt.date.fromisoformat(end);start=dt.date.fromisoformat(cohort['start']);fy=dt.date(fyend.year-1,4,1)
 stop=start.replace(year=start.year+int(cohort['life']))-dt.timedelta(days=1)
 days=max(0,(min(fyend,stop)-max(fy,start)).days+1)
 return cohort['cost']/cohort['life']*days/((fyend-fy).days+1)

def evaluate(a,ass,case='base',overrides=None):
 p=deepcopy(ass['cases'][case])
 if overrides and set(overrides)-set(p):raise KeyError('Unknown house driver: '+','.join(sorted(set(overrides)-set(p))))
 p.update(overrides or {})
 f=a['fy26'];h=a['h1'];sf=a['segments']['FY2026_March']['values'];sh=a['segments']['FY2027_H1']['values'];sp=a['segments']['FY2026_H1']['values'];ob=a['orders']['FY2027_H1'];jv=a['jv']['values']
 for actual in [f,h]:
  if abs(actual['sales']-actual['cogs']-actual['sga']-actual['op'])>3 or abs(actual['pbt']-actual['total_tax']-actual['group_ni'])>3 or abs(actual['group_ni']-actual['nci_ni']-actual['parent_ni'])>3:raise ValueError('Inconsistent reported P&L actuals beyond integer-million rounding')
 if len(p['capex'])!=4 or any(x<0 for x in p['capex'])or p['capex'][0]<h['cash_capex']:raise ValueError('Future capital spending cannot be negative or below already paid H1cashCAPEX')
 if any(v<0 for v in p['hasuda_future_additions'])or abs(p['hasuda_opening_cip_proxy']+sum(p['hasuda_future_additions'])-p['hasuda_total_budget'])>1e-6:raise ValueError('Hasuda openingCIP and newadditions must equal project budget')
 if abs(sum(p['capex_allocation'])-1)>1e-8 or any(v<0 for v in p['capex_allocation']):raise ValueError('Invalid capexallocation')
 for key,value in p.items():
  if key.endswith(('_h2_open','_h2_new','_annual_open','_annual_new'))and not 0<=value<=1:raise ValueError('Invalid delivery fraction '+key)
 if not 0<=p['property_advance_other_CL_fraction']<=1:raise ValueError('Invalid advance classification allocation')
 for key in ['tax','jv_tax','normalization_marginal_tax','payout','future_nci_payout','pension_liability_share_of_cash_drag','property_scope_retention','cancellation_rate','old_backlog_repricing_fraction','tax_payable_fraction','legacy_other_CL_settlement_fraction','hasuda_building_fraction','equity_method_cash_distribution_fraction','borrow_average_fraction']:
  if not 0<=p[key]<=1:raise ValueError('Fraction outside0–1:'+key)
 if any(x<0 or int(x)!=x for x in p['future_share_grants']):raise ValueError('Future sharegrants must be nonnegative whole shares')
 if any(x<=0 for x in p['asset_lives']) or p['hasuda_building_life']<=0 or p['hasuda_equipment_life']<=0:raise ValueError('Nonpositive assetlife')
 if p['hasuda_opening_cip_proxy']<0 or p['hasuda_opening_cip_proxy']>h['cip']:raise ValueError('Hasuda openingCIP outside reported aggregateCIP')
 if p['new_credit_planning_limit']<0 or p['draw_interest_rate']<0 or p['min_cash']<0:raise ValueError('Negative financing domain')
 if any(v<=-1 for key in ['prices','input_inflation','fixed_inflation']for v in p[key]):raise ValueError('Price/cost index must staypositive')
 if p['power_current_volume_cap']<=-1 or p['power_volume_cap']<=-1 or p['legacy_core_da_growth']<=-1:raise ValueError('Resource/depreciation growth domain')
 if p['hasuda_commission']<'2026-10-01' or (p['unallocated_opening_CIP_commission'] and p['unallocated_opening_CIP_commission']<'2026-10-01'):raise ValueError('Project alreadycommissionedbeforecashanchor requiresactualrebase, notforecastDAreplay')
 dates=a['fiscal_ends'];initial_price=p['opening_backlog_price_index'];price=[1.]*4;mat=[1.]*4;fix=[1.]*4
 if any(x<=0 for x in initial_price):raise ValueError('Nonpositive initial contract index')
 backlog=ob['closing_backlog'][:4];bconstant=[backlog[i]/initial_price[i]for i in range(4)]
 actual_h1constant=[sh['external_sales'][i]/initial_price[i]for i in range(4)]
 power_cap=None;previous_orders=None;previous_sales=None;rows=[];cohorts=[]
 # Full Sep30 balance, with source rounding preserved as fixed small residuals.
 current_LT_source=a['current_LT_debt_calculated_from_maturities']
 state=dict(cash=h['cash_equivalents'],ar=h['notes_trade_receivable_contract_assets']+h['electronic_receivables'],inventory=h['finished_goods']+h['wip']+h['raw_materials'],ap=h['trade_and_notes_payable']+h['electronic_payable'],advances=h['contract_liabilities'],bonus=h['bonus_provision'],taxpay=h['tax_payable'],dta=h['dta'],dtl=h['dtl'],pension_liability=h['pension_liability'],pension_asset=h['pension_asset'],asset_pool=h['ppe']+h['intangibles']+h['other_noncurrent_assets'],investment_assets=h['investment_securities'],other_CA=h['other_current_assets']+h['bad_debt_allowance'],other_CL=h['other_current_liabilities'],repair=h['repair_provision'],warranty=h['warranty_provision'],director=h['director_share_provision'],other_NCL=h['other_noncurrent_liabilities'],bank_short=h['current_borrowing']-current_LT_source,bank_LT=h['long_debt']+current_LT_source,lease=h['current_lease']+h['long_lease'],new_draws=0.,parent_equity=h['parent_equity'],nci_equity=h['nci_equity'],deposit=p['property_advance_m'])
 state['other_CL']-=state['deposit']*p['property_advance_other_CL_fraction']
 state['advances']-=state['deposit']*(1-p['property_advance_other_CL_fraction'])
 if min(state['other_CL'],state['advances'],state['bank_short'])<0:raise ValueError('Opening liability allocation negative')
 # Short-bank380/currentLT600 is an explicit calculation from source balances
 # and contractual600/year schedule, not a separate disclosed Sep table.
 assert abs(state['bank_short']+state['bank_LT']-h['current_borrowing']-h['long_debt'])<1e-6
 ca0=state['cash']+state['ar']+state['inventory']+state['other_CA'];nca0=state['asset_pool']+state['investment_assets']+state['pension_asset']+state['dta']
 cl0=state['ap']+state['advances']+state['bonus']+state['taxpay']+state['other_CL']+state['deposit']+state['bank_short']+current_LT_source+h['current_lease']
 ncl0=state['bank_LT']-current_LT_source+state['lease']-h['current_lease']+state['dtl']+state['repair']+state['warranty']+state['director']+state['pension_liability']+state['other_NCL']
 asset_round=h['total_assets']-ca0-nca0;cl_round=h['current_liabilities']-cl0;ncl_round=h['total_liabilities']-h['current_liabilities']-ncl0
 if max(abs(asset_round),abs(cl_round),abs(ncl_round))>10:raise ValueError('Opening source rounding residual exceeds disclosed integermillion scope')
 legacy_depreciable_available=h['ppe']+h['intangibles']-h['land']-h['cip'];legacy_DA_cumulative=0.
 # Source-rental scope versus segment scope: no new external income is created.
 rent=a['property_rent']['values'];rental_profit=rent['rental_profit_FY26'];rental_da=rent['rental_property_da_FY26'];rent_sales=sf['external_sales'][4]
 scope_profit=sf['segment_op'][4]-rental_profit;scope_da=sf['segment_da'][4]-rental_da;scope_cash_cost=sf['internal_sales'][4]-scope_profit-scope_da
 external_rent_cash_cost=rent_sales-rental_profit-rental_da
 core_legacy_annual=h['da']*2-sf['segment_da'][4]
 coreweights=sf['segment_da'][:4]+[sf['central_da']+(sf['group_da']-sum(sf['segment_da'])-sf['central_da'])]
 coreweights=[x/sum(coreweights)for x in coreweights]
 h1_da_proxy=[core_legacy_annual*x/2 for x in coreweights]
 historical_cash_fixed=[sf['external_sales'][i]*p['contribution'][i]-sf['segment_op'][i]-sf['segment_da'][i]for i in range(4)]
 if any(x<0 for x in historical_cash_fixed):raise ValueError('Contributionproxy implies negative historical fixed cashcost')
 prior_half_corp_da=sf['central_da']/2
 corp_seasonality=((sf['central_cost']-sp['central_cost'])-prior_half_corp_da)/(sp['central_cost']-prior_half_corp_da)
 corp_h1_core_cash=sh['central_cost']-h1_da_proxy[4]-p['historical_transfer_reference']/2
 corp_h2_core_cash=corp_h1_core_cash*corp_seasonality
 corp_annual_core=corp_h1_core_cash+corp_h2_core_cash
 known_extra=h['special_income']-h['special_losses'];norm_h1_parent=h['parent_ni']-known_extra*(1-p['normalization_marginal_tax']);norm_h1_group=norm_h1_parent+h['nci_ni'];norm_h1_pbt=h['pbt']-known_extra;norm_h1_tax=norm_h1_pbt-norm_h1_group
 prior_parent=None;prior_eps=None;total_new_draws=0.
 for t,end in enumerate(dates):
  frac=.5 if t==0 else 1.;price=[price[i]*(1+p['prices'][i])for i in range(4)];mat=[mat[i]*(1+p['input_inflation'][i])for i in range(4)];fix=[fix[i]*(1+p['fixed_inflation'][i])for i in range(4)]
  if t==0:
   orders=[p['power_h2_orders'],p['meter_h2_orders'],p['gx_h2_orders'],p['optical_h2_orders']]
   old_rates=[p['power_h2_open'],p['meter_h2_open'],p['gx_h2_open'],p['optical_h2_open']];new_rates=[p['power_h2_new'],p['meter_h2_new'],p['gx_h2_new'],p['optical_h2_new']]
   power_cap=(sf['external_sales'][0]-sp['external_sales'][0])*(1+p['power_current_volume_cap'])
  else:
   orders=[previous_orders[0]*(1+p['power_order_growth'][t-1]),previous_orders[1]*(1+p['meter_order_growth'][t-1]),p['gx_orders'][t-1],p['optical_orders'][t-1]]
   old_rates=[p['power_annual_open'],p['meter_annual_open'],p['gx_annual_open'],p['optical_annual_open']];new_rates=[p['power_annual_new'],p['meter_annual_new'],p['gx_annual_new'],p['optical_annual_new']]
   power_cap=previous_annual_power_capacity*(1+p['power_volume_cap'])
  if any(v<0 for v in orders):raise ValueError('Negative new orders')
  retention=[1.]*4
  if t and p['new_order_retention_threshold_months']:
   for i in range(4):
    months=12*backlog[i]/previous_sales[i] if previous_sales[i]>0 else math.inf
    retention[i]=min(1,p['new_order_retention_threshold_months']/months)if months>0 else 1
    orders[i]*=retention[i]
  reprice=[backlog[i]*p['prices'][i]*p['old_backlog_repricing_fraction']if t else 0 for i in range(4)]
  available=[backlog[i]+reprice[i]for i in range(4)];cancel=[available[i]*p['cancellation_rate']for i in range(4)];oldtargets=[(available[i]-cancel[i])*old_rates[i]for i in range(4)];newtargets=[orders[i]*new_rates[i]for i in range(4)]
  oldship=[];newship=[];constant=[]
  for i in range(4):
   oldconst=oldtargets[i]*bconstant[i]/available[i] if available[i]else 0;newconst=newtargets[i]/price[i]
   capacity=power_cap if i==0 else math.inf
   ofill=min(1,capacity/oldconst)if oldconst>0 else 1;nfill=min(1,max(0,capacity-oldconst)/newconst)if newconst>0 else 1
   os=oldtargets[i]*ofill;ns=newtargets[i]*nfill
   oldship.append(os);newship.append(ns);constant.append(os*bconstant[i]/available[i]+ns/price[i]if available[i]else ns/price[i])
  future_sales=[oldship[i]+newship[i]for i in range(4)]
  closing=[available[i]+orders[i]-cancel[i]-future_sales[i]for i in range(4)]
  closingconstant=[bconstant[i]*(1-p['cancellation_rate'])-oldship[i]*bconstant[i]/available[i]+(orders[i]-newship[i])/price[i]for i in range(4)]
  if any(v<-.000001 for v in closing+closingconstant):raise ValueError('Overshipped backlog')
  annual_core_sales=[future_sales[i]+(sh['external_sales'][i]if t==0 else 0)for i in range(4)]
  annual_constant=[constant[i]+(actual_h1constant[i]if t==0 else 0)for i in range(4)]
  annual_orders=[orders[i]+(ob['orders'][i]if t==0 else 0)for i in range(4)]
  prior_h2=sf['external_sales'][0]-sp['external_sales'][0]
  if t==0 and constant[0]>prior_h2*(1+p['power_current_volume_cap'])+1e-6:raise ValueError('Power throughput capacity exceeded')
  # All future spend is post-Sep. Existing H1spend is never added again to DA.
  period_capex=p['capex'][t]-(h['cash_capex']if t==0 else 0)
  hasuda_add=p['hasuda_future_additions'][t]
  if hasuda_add>period_capex or period_capex<0:raise ValueError('Named project spending exceeds total capital budget')
  pooled=period_capex-hasuda_add;start=f'{int(end[:4])-1}-12-31'if t==0 else f'{int(end[:4])-1}-10-01'
  for i in range(6):
   if i==4:continue
   cohorts.append(dict(name='Poolednewcapital',cost=pooled*p['capex_allocation'][i],life=p['asset_lives'][i],start=start,segment=i))
  if t==0:
   for weight,life in [(p['hasuda_building_fraction'],p['hasuda_building_life']),(1-p['hasuda_building_fraction'],p['hasuda_equipment_life'])]:cohorts.append(dict(name='HasudaVCTproject',cost=p['hasuda_total_budget']*weight,life=life,start=p['hasuda_commission'],segment=1))
   if p['unallocated_opening_CIP_commission']:
    unallocated=h['cip']-p['hasuda_opening_cip_proxy'];cohorts.append(dict(name='UnallocatedopeningCIPtimingsensitivity',cost=unallocated,life=p['unallocated_opening_CIP_life'],start=p['unallocated_opening_CIP_commission'],segment=5))
  legacy_core_period=core_legacy_annual*(1+p['legacy_core_da_growth'])**t*frac
  core_da=[legacy_core_period*coreweights[i]+sum(da(z,end)for z in cohorts if z['segment']==(i if i<4 else 5))for i in range(5)]
  # Rental cash costs and depreciation are distinct: changing DA changes OP.
  fyend=dt.date.fromisoformat(end);fystart=dt.date(fyend.year-1,4,1);periodstart=dt.date(2026,10,1)if t==0 else fystart
  disposal_day=dt.date.fromisoformat(p['property_sale_date'])
  last_rental_day=min(fyend,disposal_day-dt.timedelta(days=1))if p['property_sale_enabled']else fyend
  rent_days=max(0,(last_rental_day-periodstart).days+1)
  ext_rent=p['property_remaining_rent_runrate']*rent_days/((fyend-fystart).days+1)
  ext_da=rental_da*ext_rent/rent_sales
  ext_cash_cost=external_rent_cash_cost*ext_rent/rent_sales*(1+p['corp_cash_inflation'])**(t+1)
  scope_cash=scope_cash_cost*(1+p['corp_cash_inflation'])**(t+1)*frac;scope_DA=scope_da*frac
  scope_net=sf['internal_sales'][4]*frac-scope_cash-scope_DA
  retained_scope=scope_net*p['property_scope_retention'];property_period_op=ext_rent-ext_cash_cost-ext_da+retained_scope-p['property_unoffset_scope_loss_annual']*frac
  # A classification-only move from property to central preserves earnings/DA.
  central_scope_credit=scope_net*(1-p['property_scope_retention'])
  period_property_da=ext_da+scope_DA
  total_period_da=sum(core_da)+period_property_da
  legacy_DA_cumulative+=legacy_core_period+period_property_da
  group_da=total_period_da+(h['da']if t==0 else 0)
  cost_details=[];period_segment_op=[]
  for i in range(4):
   if t==0:
    reference_sales=sf['external_sales'][i]-sp['external_sales'][i];reference_op=sf['segment_op'][i]-sp['segment_op'][i];reference_da=sf['segment_da'][i]/2
    fixed_cash=reference_sales*p['contribution'][i]-reference_op-reference_da
    cash_fixed=fixed_cash*fix[i]*(1+p['staff_elasticity'][i]*max(0,constant[i]/reference_sales-1))
   else:
    reference_sales=sf['external_sales'][i];cash_fixed=historical_cash_fixed[i]*fix[i]*(1+p['staff_elasticity'][i]*max(0,constant[i]/reference_sales-1))
   if i==2:cash_fixed-=p['reclassification']*frac
   var_cost=constant[i]*(1-p['contribution'][i])*mat[i]
   op=future_sales[i]-var_cost-cash_fixed-core_da[i]
   period_segment_op.append(op);cost_details.append(dict(external_sales=future_sales[i],constant_FY26_reference_value=constant[i],variable_cash_cost=var_cost,fixed_cash_cost=cash_fixed,DA=core_da[i],OP=op,scope='Affineexternalfinancialactivitycostproxy calibratedto segmentOP; includes netinternalallocations, notdisclosedphysicalunitmargin.'))
  corporate_period_cash=(corp_h2_core_cash if t==0 else corp_annual_core*(1+p['corp_cash_inflation'])**t)+p['corp_incremental_program'][t]*frac
  corporate_period_transfer=p['reclassification']*frac
  corporate_period=corporate_period_cash+corporate_period_transfer+core_da[4]-central_scope_credit+p['net_elimination']*frac
  period_op=sum(period_segment_op)+property_period_op-corporate_period
  full_op=period_op+(h['op']if t==0 else 0)
  full_sales=(h['sales']if t==0 else 0)+sum(future_sales)+ext_rent
  full_external=annual_core_sales+[ext_rent+(sh['external_sales'][4]if t==0 else 0)]
  # Equity-accounted profit is noncash until a separately assumed distribution.
  em_profit=p['equity_method_profit_annual']*frac;em_distribution=em_profit*p['equity_method_cash_distribution_fraction']
  cash_nonop=p['other_cash_nonop_annual']*frac+state['cash']*p['cash_interest_rate']*frac
  # Entity tax and minority sharing. No automatic refund/credit for loss-making entities.
  if t==0:
   historical_h2_share=1-a['h1_prior']['nci_ni']/f['nci_ni']
   entity_pbt=jv['ordinary_profit']*historical_h2_share+(future_sales[1]-(sf['external_sales'][1]-sp['external_sales'][1]))*p['jv_incremental_pretax_capture']-(core_da[1]-sf['segment_da'][1]/2)*p['jv_da_fraction']
  else:entity_pbt=jv['ordinary_profit']+(annual_core_sales[1]-sf['external_sales'][1])*p['jv_incremental_pretax_capture']-(core_da[1]-sf['segment_da'][1])*p['jv_da_fraction']
  entity_tax=max(0,entity_pbt)*p['jv_tax'];entity_ni=entity_pbt-entity_tax
  other_nci=(f['nci_ni']-jv['net_income']*jv['other_owner_share'])*frac
  period_nci=entity_ni*jv['other_owner_share']+other_nci
  full_nci=period_nci+(h['nci_ni']if t==0 else 0)
  # Material working-capital accounts, not a percentage of profit.
  volume=sum(annual_constant)/sum(sf['external_sales'][:4]);weighted_cost_index=sum(annual_constant[i]*mat[i]for i in range(4))/sum(annual_constant)
  cogs_wc_proxy=f['cogs']*volume*weighted_cost_index
  ar=full_sales/365*p['receivable_days'];inventory=cogs_wc_proxy/365*p['inventory_days'];ap=cogs_wc_proxy/365*p['payable_days'];advances=full_sales/365*p['advance_days'];bonus=f['bonus_provision']*volume*(1+p['fixed_inflation'][0])**(t+1)
  wc_delta=(ar-state['ar'])+(inventory-state['inventory'])-(ap-state['ap'])-(advances-state['advances']);bonus_delta=bonus-state['bonus']
  pension_drag=p['pension_cash_drag'][t]-(-h['cf_pension_liability']-h['cf_pension_asset'])if t==0 else p['pension_cash_drag'][t]
  closing_pension_liability=state['pension_liability']-pension_drag*p['pension_liability_share_of_cash_drag'];closing_pension_asset=state['pension_asset']+pension_drag*(1-p['pension_liability_share_of_cash_drag'])
  property_gain=property_book=property_cash=advance_release=0.
  if p['property_sale_enabled']and periodstart<=disposal_day<=fyend:
   property_gain=p['property_final_gain'];property_book=p['property_final_book'];advance_release=state['deposit'];property_cash=property_gain+property_book-advance_release
   if property_cash<0:raise ValueError('Disposal receipt negative; explicit additional cash/fees schedule required')
  other_CL_settle=state['other_CL']*p['legacy_other_CL_settlement_fraction']if t==0 else 0
  other_CL=state['other_CL']-other_CL_settle
  closing_deposit=state['deposit']-advance_release
  # The non-operating sale deposit is always separate. Its release is noncash,
  # never a change in ordinary customer-advance working capital.
  legacy_depreciable_available-=property_book
  if legacy_DA_cumulative>legacy_depreciable_available+1e-6:raise ValueError('LegacyDA exceeds opening depreciablebook after disposals; land/CIP cannot be amortized')
  current_LT_pay=p['contractual_lt_repayment'][t]
  if current_LT_pay<0 or current_LT_pay>state['bank_LT']+1e-6:raise ValueError('Contractual debt repayment outside outstanding LTprincipal')
  lease_pay=p['legacy_lease_repayment'][t]
  if lease_pay<0 or lease_pay>state['lease']:raise ValueError('Lease payment exceeds existing principal')
  repayment=current_LT_pay+lease_pay
  future_grants=sum(p['future_share_grants'][:t+1]);end_eps_shares=a['shares']['values']['post_cancel_external_eps_shares']+future_grants
  if t==0:weighted_shares=(h['shares_weighted_h1']*183+end_eps_shares*182)/365
  else:weighted_shares=a['shares']['values']['post_cancel_external_eps_shares']+sum(p['future_share_grants'][:t])+p['future_share_grants'][t]/2
  dividend_shares=end_eps_shares+p['trust_dividend_shares_proxy']
  nci_div=0 if t==0 else max(0,rows[-1]['nci_profit'])*p['future_nci_payout']
  interest_existing=(state['bank_short']*p['existing_short_bank_rate'][t]+(state['bank_LT']-current_LT_pay/2)*p['existing_long_bank_rate'][t]+state['new_draws']*p['draw_interest_rate']+(state['lease']-lease_pay/2)*p['lease_interest_rate'])*frac
  def finance(draw):
   interest=interest_existing+draw*p['draw_interest_rate']*p['borrow_average_fraction']*frac
   pbt=period_op+cash_nonop+em_profit-interest
   other_tax=max(0,pbt-entity_pbt-em_profit)*p['tax'];rec_tax=other_tax+entity_tax
   recurring_group=pbt-rec_tax;recurring_parent=recurring_group-period_nci
   full_parent=recurring_parent+(norm_h1_parent if t==0 else 0);full_group=recurring_group+(norm_h1_group if t==0 else 0)
   eps=full_parent*1e6/weighted_shares
   book_sale_tax=max(0,property_gain)*p['tax'];book_tax=rec_tax+book_sale_tax
   # Income-related future DTA only. Historical OCI taxes are never treated as cash.
   desired_DTA_change=(bonus_delta-pension_drag)*p['tax']
   DTA_change=max(-state['dta'],desired_DTA_change)
   current_tax=max(entity_tax,book_tax+DTA_change);DTA_change=current_tax-book_tax
   closing_DTA=state['dta']+DTA_change
   annual_current=current_tax+(h['current_tax']if t==0 else 0)
   taxpay=annual_current*p['tax_payable_fraction'];cash_tax=current_tax+state['taxpay']-taxpay
   reported_group=recurring_group+property_gain-book_sale_tax;reported_parent=reported_group-period_nci
   CFO=reported_group+total_period_da-property_gain-em_profit+em_distribution-wc_delta-pension_drag+bonus_delta-DTA_change+(taxpay-state['taxpay'])-other_CL_settle
   # Source actual interim is paid after Sep; no repeat of H1June dividend/buyback.
   if t==0:dividend=a['dividend']['values']['interim_yen']*dividend_shares/1e6
   else:
    previous_final=max(0,rows[-1]['recurring_eps']*p['payout']-a['dividend']['values']['interim_yen'])if t==1 else max(0,rows[-1]['recurring_eps'])*p['payout']/2
    current_interim=max(0,eps)*p['payout']/2
    dividend=(previous_final+current_interim)*dividend_shares/1e6
   cash=state['cash']+CFO-period_capex+property_cash-dividend-nci_div-repayment+draw
   return dict(period_interest=interest,period_recurring_pbt=pbt,period_recurring_tax=rec_tax,period_recurring_group_profit=recurring_group,period_recurring_parent_profit=recurring_parent,recurring_parent_profit=full_parent,recurring_group_profit=full_group,recurring_eps=eps,period_reported_group_profit=reported_group,period_reported_parent_profit=reported_parent,period_book_tax=book_tax,period_current_tax=current_tax,period_cash_tax=cash_tax,deferred_tax_change=DTA_change,closing_DTA=closing_DTA,closing_tax_payable=taxpay,period_CFO=CFO,parent_dividend_cash=dividend,closing_cash=cash)
  draw=0.;without=finance(0)
  if without['closing_cash']<p['min_cash']:
   lo=0.;hi=max(0,p['new_credit_planning_limit']-total_new_draws)
   for _ in range(80):
    mid=(lo+hi)/2
    if finance(mid)['closing_cash']<p['min_cash']:lo=mid
    else:hi=mid
   draw=hi
  fin=finance(draw);total_new_draws+=draw
  if fin['closing_cash']<-.000001:raise ValueError('Unfunded cash shortfall: revise financing or operating case before extending forecast')
  bankLT=state['bank_LT']-current_LT_pay;lease=state['lease']-lease_pay;debt=state['bank_short']+bankLT+total_new_draws+lease
  closing_asset_pool=state['asset_pool']+period_capex-total_period_da-property_book
  if closing_asset_pool<0 or closing_pension_liability<0 or fin['closing_DTA']<-.00001:raise ValueError('Negative modeled asset/liability requires explicit runoff treatment')
  investment=state['investment_assets']+em_profit-em_distribution
  parent_eq=state['parent_equity']+fin['period_reported_parent_profit']-fin['parent_dividend_cash'];nci_eq=state['nci_equity']+period_nci-nci_div
  current_LT=min(bankLT,p['contractual_lt_repayment'][t+1]if t<3 else 0);current_lease=min(lease,4.)
  CA=fin['closing_cash']+ar+inventory+state['other_CA'];NCA=closing_asset_pool+investment+closing_pension_asset+fin['closing_DTA'];assets=CA+NCA+asset_round
  CL=ap+advances+bonus+fin['closing_tax_payable']+other_CL+closing_deposit+state['bank_short']+total_new_draws+current_LT+current_lease+cl_round
  NCL=bankLT-current_LT+lease-current_lease+state['dtl']+state['repair']+state['warranty']+state['director']+closing_pension_liability+state['other_NCL']+ncl_round
  liabilities=CL+NCL;capital=assets-CL;residual=assets-liabilities-parent_eq-nci_eq
  row=dict(case=case,period_end=end,full_year_sales=full_sales,segment_external_sales=full_external,forecast_period_sales=future_sales,segment_constant_activity=annual_constant,forecast_period_constant_activity=constant,orders=annual_orders,forecast_period_orders=orders,opening_forecast_backlog=backlog,opening_constant_backlog=bconstant,opening_repricing=reprice,cancellations=cancel,old_cohort_shipments=oldship,new_cohort_shipments=newship,closing_backlog=closing,closing_constant_backlog=closingconstant,new_order_price_index=price[:],new_order_retention=retention,power_constant_capacity=power_cap,power_constant_workload=constant[0],segment_costs=cost_details,forecast_period_segment_op=period_segment_op,property_external_rent=ext_rent,property_external_cash_cost=ext_cash_cost,property_external_DA=ext_da,property_scope_OP=retained_scope,property_scope_cash_cost=scope_cash,property_scope_DA=scope_DA,property_scope_central_credit=central_scope_credit,forecast_property_OP=property_period_op,corporate_period_cash=corporate_period_cash,corporate_period_DA=core_da[4],corporate_period_transfer=corporate_period_transfer,forecast_net_corporate_cost=corporate_period,recurring_op=full_op,forecast_period_OP=period_op,ebit_margin_pct=100*full_op/full_sales,group_DA=group_da,forecast_period_DA=total_period_da,core_period_DA=core_da,capital_cohorts=deepcopy(cohorts),annual_capex_budget=p['capex'][t],cash_capex_after_anchor=period_capex,hasuda_additions=hasuda_add,pooled_capital_additions=pooled,weighted_shares=weighted_shares,ending_eps_shares=end_eps_shares,dividend_eligible_shares=dividend_shares,JV_period_pretax=entity_pbt,JV_period_tax=entity_tax,JV_period_net=entity_ni,JV_ownership=jv['ownership'],forecast_period_NCI=period_nci,nci_profit=full_nci,nci_dividend_cash=nci_div,equity_method_profit=em_profit,equity_method_distribution=em_distribution,nonop_cash=cash_nonop,receivables=ar,inventory=inventory,payables=ap,contract_liabilities=advances,bonus_liability=bonus,working_capital_delta=wc_delta,bonus_liability_change=bonus_delta,pension_cash_above_expense=pension_drag,pension_liability=closing_pension_liability,pension_asset=closing_pension_asset,property_disposal_gain=property_gain,property_book_derecognition=property_book,property_advance_release=advance_release,property_remaining_cash=property_cash,legacy_other_CL_settlement=other_CL_settle,bank_LT_repayment=current_LT_pay,lease_principal=lease_pay,new_borrowing=draw,required_uncommitted_new_financing_total=total_new_draws,closing_bank_LT=bankLT,closing_lease=lease,closing_debt=debt,closing_asset_pool=closing_asset_pool,closing_investments=investment,parent_equity=parent_eq,nci_equity=nci_eq,total_assets=assets,current_liabilities=CL,noncurrent_liabilities=NCL,total_liabilities=liabilities,capital_employed=capital,closing_roce_pct=100*full_op/capital,balance_sheet_residual=residual,opening_source_rounding=dict(assets=asset_round,current_liabilities=cl_round,noncurrent_liabilities=ncl_round),cash_period_months=int(12*frac),cash_period_start='2026-10-01'if t==0 else f'{int(end[:4])-1}-04-01',funding_gap=max(0,p['min_cash']-fin['closing_cash']),**fin)
  row['reported_FCF_after_anchor']=fin['period_CFO']-period_capex
  row['annual_maintenance_capex_house_allocation']=min(p['maintenance_capex'],p['capex'][t])
  row['annual_growth_capex_house_allocation']=p['capex'][t]-row['annual_maintenance_capex_house_allocation']
  row['annual_reported_parent_profit']=fin['period_reported_parent_profit']+(h['parent_ni']if t==0 else 0)
  rows.append(row)
  state.update(cash=fin['closing_cash'],ar=ar,inventory=inventory,ap=ap,advances=advances,bonus=bonus,taxpay=fin['closing_tax_payable'],dta=fin['closing_DTA'],asset_pool=closing_asset_pool,investment_assets=investment,pension_liability=closing_pension_liability,pension_asset=closing_pension_asset,other_CL=other_CL,bank_LT=bankLT,lease=lease,new_draws=total_new_draws,parent_equity=parent_eq,nci_equity=nci_eq,deposit=closing_deposit)
  previous_annual_power_capacity=power_cap+(actual_h1constant[0]if t==0 else 0);previous_orders=annual_orders;previous_sales=annual_core_sales;backlog=closing;bconstant=closingconstant
 return rows

def build():
 a=read(B/'actuals.json');ass=read(B/'assumptions.json');cases={c:dict(annual=evaluate(a,ass,c))for c in ['bear','base','bull']}
 out=dict(schema_version=3,ticker='6617',company='Takaoka Toko',research_date=a['cutoff'],target_date='2030-03-31',status='reviewed_refined_independent_house_model_conditional',eps_basis='RecurringparentbasicEPS; after-renteconomicbasiswithunquantifiedFY28leaseGAAPtransition',method='Datedfixed-priceordercohorts andconstant-referencefinancialthroughput;actualcostpools;projectedcapital/DA;entitytaxandNCI;fullpooledBSandcashfunding',cases=cases,limitations=['UnknownunitASP/nameplatecapacity/productcosts: explicitfinancialproxies,notphysicalprecision.','CurrentH1actualslocked; firstcashrowisremaining6monthsOct26–Mar27, laterrows12months.','GroupD&A/deferredtax/otheraccrualsinvolveidentifiedscopeandtimingassumptions; modeledfullpooledBSisaneconomicprojection,notprecisestatutoryassetregister.','Propertyremainingcash/book/advanceclassificationunknown: housebridgeandcoherentzerodealstress;notknowncashfloor.','Anynewborrowingisrequireduncommittedfinancing,notaconfirmedfacility;cashplanningfloorisnotacovenant.'])
 (B/'EPS_MODEL.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
 summary={}
 for c,z in cases.items():
  rr=z['annual'];x=rr[0]['recurring_eps'];y=rr[-1]['recurring_eps']
  summary[c]=dict(EPS=[r['recurring_eps']for r in rr],CAGR_pct=((y/x)**(1/3)-1)*100 if x>0 and y>0 else None,sales=[r['full_year_sales']for r in rr],OP=[r['recurring_op']for r in rr],cash=[r['closing_cash']for r in rr],debt=[r['closing_debt']for r in rr],NCI=[r['nci_profit']for r in rr],BSresiduals=[r['balance_sheet_residual']for r in rr],funding_gap=[r['funding_gap']for r in rr])
 (B/'SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))
 return out
if __name__=='__main__':build()
