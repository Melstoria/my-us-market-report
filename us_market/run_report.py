"""
run_report.py — GitHub Actions 엔트리포인트
"""
import datetime
from us_market.collector         import collect_all
from us_market.analyzer          import analyze
from us_market.reporter          import build_report
from us_market.biweekly_reporter import build_biweekly_report, is_biweekly_friday
from us_market.monthly_reporter  import build_monthly_report, is_month_end
from us_market.quarterly_reporter import build_quarterly_report, is_quarter_end
from us_market.update_index      import build_index

today = datetime.date.today()

# 1. 데이터 수집
raw      = collect_all()
analyzed = analyze(raw)

# 2. 일간 리포트
build_report(analyzed)

# 3. 격주 금요일
if is_biweekly_friday(today):
    print(f"\n📊 격주 금요일 — 격주 리포트 생성")
    build_biweekly_report(str(today))

# 4. 월말
if is_month_end(today):
    print(f"\n📆 월말 — 월간 리포트 생성")
    build_monthly_report(str(today))

# 5. 분기말
if is_quarter_end(today):
    print(f"\n🗓 분기말 — 분기 리포트 생성")
    build_quarterly_report(str(today))

# 6. 인덱스 업데이트
build_index()
print("\n✅ 전체 완료!")
