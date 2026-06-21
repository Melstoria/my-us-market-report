"""
analyzer.py
수집된 원시 데이터를 리포트용 구조로 가공
"""

import json
from pathlib import Path


def analyze(data: dict) -> dict:
    sp500_raw  = data.get("sp500", [])
    ndx100_raw = data.get("nasdaq100", [])

    return {
        "date":       data["date"],
        "index":      data["index"],
        "sector_etf": data["sector_etf"],
        "sp500":      _analyze_universe(sp500_raw,  label="S&P 500"),
        "nasdaq100":  _analyze_universe(ndx100_raw, label="Nasdaq 100"),
        "cross":      _cross_signal(sp500_raw, ndx100_raw),
    }


def _analyze_universe(records, label):
    if not records:
        return {}

    by_amount  = sorted(records, key=lambda x: x.get("amount", 0),     reverse=True)
    by_chg_pos = sorted(records, key=lambda x: x.get("change_pct", 0), reverse=True)
    by_chg_neg = sorted(records, key=lambda x: x.get("change_pct", 0))

    highs        = [r for r in records if r.get("is_52w_high")]
    highs_sorted = sorted(highs, key=lambda x: x.get("amount", 0), reverse=True)
    top_amount   = by_amount[:30]
    sector_flow  = _sector_flow(records)

    # 모멘텀: 신고가 + 거래대금 상위 50%
    amounts = sorted([r.get("amount", 0) for r in records], reverse=True)
    threshold = amounts[len(amounts) // 2] if amounts else 0
    momentum = sorted(
        [r for r in highs if r.get("amount", 0) >= threshold],
        key=lambda x: x.get("amount", 0), reverse=True
    )

    return {
        "label":       label,
        "total":       len(records),
        "highs_count": len(highs),
        "top_amount":  top_amount,
        "top_gainers": by_chg_pos[:10],
        "top_losers":  by_chg_neg[:10],
        "highs":       highs_sorted[:30],
        "momentum":    momentum[:20],
        "sector_flow": sector_flow,
    }


def _sector_flow(records):
    """섹터별 거래대금 + 평균등락 + 대표종목 4개"""
    sector_map = {}
    for r in records:
        sec = r.get("sector", "Unknown")
        if sec not in sector_map:
            sector_map[sec] = {"amount": 0.0, "change_sum": 0.0, "count": 0, "stocks": []}
        sector_map[sec]["amount"]     += r.get("amount", 0)
        sector_map[sec]["change_sum"] += r.get("change_pct", 0)
        sector_map[sec]["count"]      += 1
        sector_map[sec]["stocks"].append(r)

    result = []
    for sec, v in sector_map.items():
        if v["count"] == 0:
            continue
        top_stocks = sorted(v["stocks"], key=lambda x: x.get("amount", 0), reverse=True)[:4]
        result.append({
            "sector":     sec,
            "amount":     v["amount"],
            "avg_change": round(v["change_sum"] / v["count"], 2),
            "count":      v["count"],
            "top_stocks": top_stocks,
        })
    return sorted(result, key=lambda x: x["amount"], reverse=True)


def _cross_signal(sp500, ndx100):
    """S&P500 + Nasdaq100 동시 신고가"""
    sp500_highs  = {r["ticker"] for r in sp500  if r.get("is_52w_high")}
    ndx100_highs = {r["ticker"] for r in ndx100 if r.get("is_52w_high")}
    both = sp500_highs & ndx100_highs
    sp500_map = {r["ticker"]: r for r in sp500}
    result = [sp500_map[t] for t in both if t in sp500_map]
    return sorted(result, key=lambda x: x.get("amount", 0), reverse=True)


if __name__ == "__main__":
    latest = Path(__file__).parent.parent / "data" / "market_latest.json"
    with open(latest) as f:
        raw = json.load(f)
    result = analyze(raw)
    print(json.dumps(result, indent=2, ensure_ascii=False)[:2000])
