"""Reproduce the saved Integral forecast and meaningful boundary tests offline."""
import copy,csv,json,tempfile,sys
sys.dont_write_bytecode=True
from pathlib import Path
from model import calculate,run_all
P=Path(__file__).resolve().parent
a=json.loads((P/'actuals.json').read_text(encoding='utf-8'))
p=json.loads((P/'assumptions.json').read_text(encoding='utf-8'))
saved=json.loads((P/'forecast.json').read_text(encoding='utf-8'))
assert run_all()==saved,'Saved forecast differs from engine'
checks=['12 annual scenario rows exactly reproduced']
for name,rows in saved.items():
 previous_investments=a['investment_assets_june26']
 previous_principal=a['principal_fv_june26']
 previous_equity=a['parent_equity_june26']
 previous_gp=p[name]['opening_uncalled_existing_gp_proxy']
 previous_new_gp=0
 previous_new_commitment=0
 for i,r in enumerate(rows):
  assert abs(r['basic_eps']-r['parent_profit']*1e6/r['basic_shares'])<1e-9
  assert abs(r['cash']-(r['opening_cash']+r['forward_cash_flow_before_funding']-r['forward_debt_repayment']+r['forward_new_borrowing']))<1e-7
  assert abs(r['investment_assets']-(previous_investments+r['forward_investment_calls']-r['forward_investment_capital_return']+r['forward_principal_mark']))<1e-7
  assert abs(r['principal_fv']-(previous_principal+r['forward_principal_calls']-r['forward_principal_capital_return']+r['forward_principal_mark']))<1e-7
  forward_profit=r['parent_profit']-(a['parent_profit_h126'] if i==0 else 0)
  assert abs(r['parent_equity']-(previous_equity+forward_profit-r['forward_parent_dividend']))<1e-7
  new_commitment=(r['new_fund_commitments']-previous_new_commitment)*.02
  assert abs((previous_gp+previous_new_gp+new_commitment-r['forward_gp_calls'])-(r['uncalled_existing_gp_proxy']+r['uncalled_new_gp']))<1e-7
  assert 0 <= r['forward_principal_capital_return'] <= r['forward_investment_capital_return']
  assert r['remaining_june_carry']>=0 and r['cash']>=p[name]['minimum_cash']-1e-6
  assert abs(r['cash_after_full_gp_and_deferred_tax_settlement']-(r['cash']-r['uncalled_existing_gp_proxy']-r['uncalled_new_gp']-r['deferred_tax_liquidity_reserve']))<1e-7
  assert r['deferred_tax_liquidity_reserve']>=a['opening_deferred_tax_liability']
  previous_investments=r['investment_assets'];previous_principal=r['principal_fv'];previous_equity=r['parent_equity']
  previous_gp=r['uncalled_existing_gp_proxy'];previous_new_gp=r['uncalled_new_gp'];previous_new_commitment=r['new_fund_commitments']
checks.append('Cash, parent equity, investment sleeves and uncalled GP balances conserve across all12rows;fullDTL/GP cash stress reconciles')
bad=copy.deepcopy(p['base']);bad['carry_realization']=[23000,0,0,0]
try: calculate(a,bad);raise AssertionError('Impossible carry accepted')
except ValueError:pass
bad=copy.deepcopy(p['base']);bad['principal_capital_return'][0]=1e9
try:calculate(a,bad);raise AssertionError('Impossible principal disposal accepted')
except ValueError:pass
bad=copy.deepcopy(a);del bad['cash_june26']
try:calculate(bad,p['base']);raise AssertionError('Missing cash accepted')
except KeyError:pass
checks.append('Impossible carry, impossible investment sleeve and missing input rejected')
base=saved['base'];q=copy.deepcopy(p['base']);q['annual_share_dilution']=.02
assert calculate(a,q)[-1]['basic_eps']<base[-1]['basic_eps']
q=copy.deepcopy(a);q['nci_h126']*=2
assert calculate(q,p['base'])[-1]['basic_eps']<base[-1]['basic_eps']
q=copy.deepcopy(p['base']);q['annual_asset_capex']=200
assert calculate(a,q)[-1]['forward_da']>base[-1]['forward_da']
assert calculate(a,q)[-1]['cash']<base[-1]['cash']
q=copy.deepcopy(p['base']);q['minimum_cash']=100000
funded=calculate(a,q)
assert funded[0]['forward_new_borrowing']>0 and funded[0]['forward_finance_cost']>base[0]['forward_finance_cost']
assert funded[0]['basic_eps']<base[0]['basic_eps']
assert funded[0]['forward_cash_tax']<=base[0]['forward_cash_tax']
q=copy.deepcopy(p['base']);q['minimum_cash']=1000000;q['carry_realization']=[0,0,0,0]
extreme=calculate(a,q)
assert all(x['forward_cash_tax']>=0 for x in extreme)
assert all(abs(x['cash']-q['minimum_cash'])<1e-6 for x in extreme)
q=copy.deepcopy(p['base']);q['new_fund_commitment_end']=[0,0,0,0]
assert calculate(a,q)[-1]['recurring_fee_eps']<base[-1]['recurring_fee_eps']
checks.append('Shares,NCI,capex/depreciation,borrowing/interest and successor-fee consequences propagate')
with tempfile.TemporaryDirectory(dir=P,prefix='_tmp_verify_') as d:
 d=Path(d)
 for n in ['actuals.json','assumptions.json']:(d/n).write_bytes((P/n).read_bytes())
 assert run_all(d)==saved
 (d/'guidance_comparator.json').write_text('{"deliberately_impossible":999999999}')
 assert run_all(d)==saved
checks.append('Deleting or mutating guidance leaves every forecast unchanged')
with (P/'annual_forecast.csv').open(encoding='utf-8-sig',newline='') as f:assert len(list(csv.DictReader(f)))==12
result={'status':'PASS','checks':checks,'scope_limit':'These checks validate arithmetic and causality,not undisclosed fundraising/exit timing. Independent analyst review is separate.'}
print(json.dumps(result,indent=2))
