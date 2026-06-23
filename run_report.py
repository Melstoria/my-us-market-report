import datetime
from us_market.collector import collect_all
from us_market.analyzer  import analyze
from us_market.reporter  import build_report
from us_market.biweekly_reporter  import build_biweekly_report, is_biweekly_friday
from us_market.monthly_reporter   import build_monthly_report, is_month_end
from us_market.quarterly_reporter import build_quarterly_report, is_quarter_end
from us_market.update_index       import build_index

today = datetime.date.today()

raw      = collect_all()
analyzed = analyze(raw)
build_report(analyzed)

if is_biweekly_friday(today):
    print("\n📊 격주 금요일 — 격주 리포트 생성")
    build_biweekly_report(str(today))

if is_month_end(today):
    print("\n📆 월말 — 월간 리포트 생성")
    build_monthly_report(str(today))

if is_quarter_end(today):
    print("\n🗓 분기말 — 분기 리포트 생성")
    build_quarterly_report(str(today))

build_index()
print("\n✅ 전체 완료!")
