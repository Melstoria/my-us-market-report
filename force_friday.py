"""
force_friday.py
금요일(2026-06-20) 데이터로 강제 재생성
"""
import datetime
import json
from pathlib import Path

# 날짜를 금요일로 고정
TARGET_DATE = "2026-06-20"

from us_market.collector import (
    fetch_index_data, fetch_sector_etf_data,
    fetch_universe_data, enrich_sector,
    get_sp500_tickers, get_nasdaq100_tickers,
    DATA_DIR
)
from us_market.analyzer import analyze
from us_market.reporter import build_report

print(f"강제 수집: {TARGET_DATE} (금요일)")

print("\n[1/5] 지수...")
index_data = fetch_index_data()

print("\n[2/5] 섹터 ETF...")
sector_etf = fetch_sector_etf_data()

print("\n[3/5] S&P 500...")
sp500_tickers = get_sp500_tickers()
sp500_df = fetch_universe_data(sp500_tickers)

print("\n[4/5] Nasdaq 100...")
ndx100_tickers = get_nasdaq100_tickers()
ndx100_df = fetch_universe_data(ndx100_tickers)

print("\n[5/5] 섹터 보강...")
sp500_df  = enrich_sector(sp500_df,  sp500_tickers)
ndx100_df = enrich_sector(ndx100_df, ndx100_tickers)

output = {
    "date":       TARGET_DATE,
    "index":      index_data,
    "sector_etf": sector_etf,
    "sp500":      sp500_df.to_dict(orient="records"),
    "nasdaq100":  ndx100_df.to_dict(orient="records"),
}

out_path = DATA_DIR / f"market_{TARGET_DATE}.json"
with open(out_path, "w") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

latest_path = DATA_DIR / "market_latest.json"
with open(latest_path, "w") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n✅ 데이터 저장: {out_path}")
print(f"   S&P500: {len(sp500_df)}개 / Nasdaq100: {len(ndx100_df)}개")

analyzed = analyze(output)
build_report(analyzed)
print(f"\n✅ 리포트 생성 완료!")

from us_market.update_index import build_index
build_index()
