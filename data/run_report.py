from us_market.collector import collect_all
from us_market.analyzer  import analyze
from us_market.reporter  import build_report

raw      = collect_all()
analyzed = analyze(raw)
build_report(analyzed)
