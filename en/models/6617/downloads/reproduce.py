"""Reproduce all published scenario outputs without changing the inputs."""
from pathlib import Path
import json, math
from engine import evaluate
B=Path(__file__).parent
read=lambda p:json.loads((B/p).read_text(encoding="utf-8-sig"))
actuals=read("actuals.json"); assumptions=read("assumptions.json"); frozen=read("all_forecast_records.json")
for case in ["bear","base","bull"]:
    rows=evaluate(actuals,assumptions,case)
    assert rows==frozen["cases"][case]["annual"],case+" does not match frozen outputs"
    print(case+": exact match; FY3/30 recurring EPS = "+str(rows[-1]["recurring_eps"]))
