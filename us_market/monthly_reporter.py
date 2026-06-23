"""
monthly_reporter.py — 월간 리포트
"""
import json, datetime, calendar
from pathlib import Path
from us_market.biweekly_reporter import aggregate_universe, generate_period_html, load_recent_dailies

DOCS_DIR = Path(__file__).parent.parent / "docs"
DATA_DIR = Path(__file__).parent.parent / "data"


def is_month_end(date: datetime.date) -> bool:
    last = calendar.monthrange(date.year, date.month)[1]
    return date.day == last


def load_month_dailies(year: int, month: int):
    files = sorted(DATA_DIR.glob(f"market_{year}-{month:02d}-*.json"), reverse=True)
    out = []
    for f in files:
        try:
            with open(f) as fp: out.append(json.load(fp))
        except: continue
    return out


def build_monthly_report(date_str=None):
    if date_str is None: date_str = str(datetime.date.today())
    d = datetime.date.fromisoformat(date_str)
    dailies = load_month_dailies(d.year, d.month)
    if not dailies:
        dailies = load_recent_dailies(22)
    if not dailies: print("❌ 데이터 없음"); return

    sp500  = aggregate_universe(dailies, "sp500")
    ndx200 = aggregate_universe(dailies, "nasdaq100")
    period = f"{d.year}년 {d.month}월"
    html   = generate_period_html(sp500, ndx200, date_str, "월간 리포트", period)

    out_dir = DOCS_DIR / "monthly"; out_dir.mkdir(exist_ok=True)
    out = out_dir / f"{date_str}.html"
    with open(out,"w",encoding="utf-8") as f: f.write(html)
    print(f"✅ 월간 리포트: {out}")
    return str(out)


if __name__ == "__main__":
    build_monthly_report()
