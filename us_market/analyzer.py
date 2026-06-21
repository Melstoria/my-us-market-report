"""
analyzer.py
수집된 원시 데이터를 리포트용 구조로 가공
"""

import json
from pathlib import Path


def analyze(data: dict) -> dict:
    """
    collector.collect_all() 결과를 받아 리포트 구조 반환
    """
    sp500_raw   = data.get("sp500", [])
    ndx100_raw  = data.get("nasdaq100", [])

    return {
        "date":       data["date"],
        "index":      data["index"],
        "sector_etf": data["sector_etf"],
        "sp500":      _analyze_universe(sp500_raw,  label="S&P 500"),
        "nasdaq100":  _analyze_universe(ndx100_raw, label="Nasdaq 100"),
        "cross":      _cross_signal(sp500_raw, ndx100_raw),
    }


def _analyze_universe(records: list[dict], label: str) -> dict:
    if not records:
        return {}

    # 정렬 기준
    by_amount  = sorted(records, key=lambda x: x.get("amount", 0),      reverse=True)
    by_chg_pos = sorted(records, key=lambda x: x.get("change_pct", 0),  reverse=True)
    by_chg_neg = sorted(records, key=lambda x: x.get("change_pct", 0))

    # 신고가 종목
    highs = [r for r in records if r.get("is_52w_high")]
    highs_sorted = sorted(highs, key=lambda x: x.get("amount", 0), reverse=True)

    # 거래대금 Top 30
    top_amount = by_amount[:30]

    # 등락률 Top / Bottom 10
    top_gainers = by_chg_pos[:10]
    top_losers  = by_chg_neg[:10]

    # 섹터별 자금흐름
    sector_flow = _sector_flow(records)

    # 모멘텀 종목 (신고가 + 거래대금 상위 50% 교집합)
    amount_threshold = sorted([r.get("amount", 0) for r in records], reverse=True)
    half_idx = len(amount_threshold) // 2
    threshold_val = amount_threshold[half_idx] if half_idx < len(amount_threshold) else 0

    momentum = [
        r for r in highs
        if r.get("amount", 0) >= threshold_val
    ]
    momentum_sorted = sorted(momentum, key=lambda x: x.get("amount", 0), reverse=True)

    return {
        "label":        label,
        "total":        len(records),
        "highs_count":  len(highs),
        "top_amount":   top_amount,
        "top_gainers":  top_gainers,
        "top_losers":   top_losers,
        "highs":        highs_sorted[:30],
        "momentum":     momentum_sorted[:20],
        "sector_flow":  sector_flow,
    }


def _sector_flow(records: list[dict]) -> list[dict]:
    """섹터별 거래대금 합산 + 평균 등락률"""
    sector_map: dict[str, dict] = {}
    for r in records:
        sec = r.get("sector", "Unknown")
        if sec not in sector_map:
            sector_map[sec] = {"amount": 0.0, "change_sum": 0.0, "count": 0}
        sector_map[sec]["amount"]     += r.get("amount", 0)
        sector_map[sec]["change_sum"] += r.get("change_pct", 0)
        sector_map[sec]["count"]      += 1

    result = []
    for sec, v in sector_map.items():
        if v["count"] == 0:
            continue
        result.append({
            "sector":      sec,
            "amount":      v["amount"],
            "avg_change":  round(v["change_sum"] / v["count"], 2),
            "count":       v["count"],
        })
    return sorted(result, key=lambda x: x["amount"], reverse=True)


def _cross_signal(sp500: list[dict], ndx100: list[dict]) -> list[dict]:
    """두 지수 동시 신고가 종목 (강한 모멘텀)"""
    sp500_highs  = {r["ticker"] for r in sp500  if r.get("is_52w_high")}
    ndx100_highs = {r["ticker"] for r in ndx100 if r.get("is_52w_high")}
    both = sp500_highs & ndx100_highs

    # 원본 레코드에서 정보 추출 (sp500 기준)
    sp500_map = {r["ticker"]: r for r in sp500}
    result = [sp500_map[t] for t in both if t in sp500_map]
    return sorted(result, key=lambda x: x.get("amount", 0), reverse=True)


# ──────────────────────────────────────────
# CLI 직접 실행용
# ──────────────────────────────────────────

if __name__ == "__main__":
    latest = Path(__file__).parent.parent / "data" / "market_latest.json"
    with open(latest) as f:
        raw = json.load(f)
    result = analyze(raw)
    print(json.dumps(result, indent=2, ensure_ascii=False)[:2000])
    print("... (truncated)")
