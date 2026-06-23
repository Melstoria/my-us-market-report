"""
quarterly_reporter.py — 분기 리포트
"""
import json, datetime
from pathlib import Path
from us_market.biweekly_reporter import aggregate_universe, generate_period_html

DOCS_DIR = Path(__file__).parent.parent / "docs"
DATA_DIR = Path(__file__).parent.parent / "data"

QUARTER_END_MONTHS = {3, 6, 9, 12}


def is_quarter_end(date: datetime.date) -> bool:
    import calendar
    if date.month not in QUARTER_END_MONTHS: return False
    last = calendar.monthrange(date.year, date.month)[1]
    return date.day == last


def quarter_of(date: datetime.date):
    return (date.month - 1) // 3 + 1


def load_quarter_dailies(year: int, quarter: int):
    start_month = (quarter - 1) * 3 + 1
    end_month   = start_month + 2
    files = []
    for m in range(start_month, end_month + 1):
        files += sorted(DATA_DIR.glob(f"market_{year}-{m:02d}-*.json"))
    files = sorted(files, reverse=True)
    out = []
    for f in files:
        try:
            with open(f) as fp: out.append(json.load(fp))
        except: continue
    return out


def build_quarterly_report(date_str=None):
    if date_str is None: date_str = str(datetime.date.today())
    d = datetime.date.fromisoformat(date_str)
    q = quarter_of(d)
    dailies = load_quarter_dailies(d.year, q)
    if not dailies: print("❌ 데이터 없음"); return

    sp500  = aggregate_universe(dailies, "sp500")
    ndx200 = aggregate_universe(dailies, "nasdaq100")
    period = f"{d.year}년 {q}분기 (Q{q})"
    html   = generate_period_html(sp500, ndx200, date_str, "분기 리포트", period)

    out_dir = DOCS_DIR / "quarterly"; out_dir.mkdir(exist_ok=True)
    out = out_dir / f"{date_str}.html"
    with open(out,"w",encoding="utf-8") as f: f.write(html)
    print(f"✅ 분기 리포트: {out}")
    return str(out)


if __name__ == "__main__":
    build_quarterly_report()
