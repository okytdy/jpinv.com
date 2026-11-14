"""Reproduce all annual scenarios and seven sensitivities. Python 3.9+, standard library only."""
from pathlib import Path
import copy,json,math,sys
sys.dont_write_bytecode=True
from model import calculate
ROOT=Path(__file__).resolve().parent
read=lambda name:json.loads((ROOT/name).read_text(encoding="utf-8"))
a=read("actuals.json");cfg=read("assumptions.json");expected=read("forecast.json")
for case in ("bear","base","bull"):
    assert calculate(a,cfg,case)==expected["cases"][case]["annual"],case
variants=[
 lambda z:z["put_exercise_fraction_of_original_covered_pool"].__setitem__("base",[0,0,0,0]),
 lambda z:z.__setitem__("fixed_AI_ONE_is_extra_to_seller_pools_house",False),
 lambda z:(z["put_price_multiplier_house"].__setitem__("base",2.0),z["earnout_price_multiplier_house"].__setitem__("base",2.0)),
 lambda z:(z["contract_delivery_fraction_of_opening"].__setitem__("base",[.25,.20,.05,0]),z["contract_refund_fraction_of_opening"].__setitem__("base",[.50,0,0,0])),
 lambda z:z["operating_growth"].__setitem__("base",[x-.05 for x in z["operating_growth"]["base"]]),
 lambda z:(z.__setitem__("equity_issue_discount",.50),z["put_price_multiplier_house"].__setitem__("base",2.0),z["earnout_price_multiplier_house"].__setitem__("base",2.0)),
 lambda z:z.__setitem__("rollover_fraction_of_maturing_principal",0)
]
for mut,s in zip(variants,expected["sensitivities"]):
    z=copy.deepcopy(cfg);mut(z);rr=calculate(a,z,"base");last=rr[-1]
    actual={"FY3_eps":last["recurring_eps"],"delta_eps":last["recurring_eps"]-expected["cases"]["base"]["annual"][-1]["recurring_eps"],"minimum_cash_after_claim_reserves":min(x["cash_after_claim_reserves"] for x in rr),"maximum_conditional_refinance":max(x["conditional_bank_refinancing"] for x in rr),"total_conditional_equity":sum(x["conditional_equity_cash_required"] for x in rr),"ending_basic_shares":last["ending_basic_shares"]}
    for k,v in actual.items():assert math.isclose(v,s[k],rel_tol=1e-12,abs_tol=1e-8),(s["name"],k)
print(json.dumps({"status":"PASS","annual_scenarios":3,"annual_periods":12,"sensitivities":7}))
