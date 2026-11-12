"""Reproduce JII HVAC EPS forecasts. Run: python model.py > reproduced_forecasts.csv"""
from pathlib import Path
import csv,json,sys
d=json.loads((Path(__file__).parent/'forecast.json').read_text(encoding='utf-8'))
w=csv.writer(sys.stdout);w.writerow(['company','fiscal_year','revenue_JPY_bn','OP_JPY_bn','OP_margin_pct','net_income_JPY_bn','weighted_shares_m','EPS_JPY'])
for ticker,p in d['inputs'].items():
 for i,(sales,margin) in enumerate(zip(p['sales_bn'],p['op_margin'])):
  op=sales*margin;ni=op*p['net_income_per_op'];eps=ni*1000/p['weighted_shares_m']
  w.writerow([p['company'],'FY3/'+str(27+i),round(sales,6),round(op,6),round(margin*100,4),round(ni,6),round(p['weighted_shares_m'],6),round(eps,4)])
