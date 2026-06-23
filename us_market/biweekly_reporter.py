"""
biweekly_reporter.py — 격주 리포트 (10거래일 집계)
"""
import json, datetime
from pathlib import Path
from us_market.reporter import fmt_amount, chg_sign, chg_cls, sec_color, sec_icon, CSS

DOCS_DIR = Path(__file__).parent.parent / "docs"
DATA_DIR = Path(__file__).parent.parent / "data"


def is_biweekly_friday(date: datetime.date) -> bool:
    if date.weekday() != 4: return False
    base  = datetime.date(2026, 1, 2)
    weeks = (date - base).days // 7
    return weeks % 2 == 0


def load_recent_dailies(n=10):
    files = sorted(DATA_DIR.glob("market_2*.json"), reverse=True)
    out = []
    for f in files[:n]:
        try:
            with open(f) as fp: out.append(json.load(fp))
        except: continue
    return out


def aggregate_universe(dailies, key):
    sector_map, ticker_map, highs_set = {}, {}, set()
    dates = []
    for d in dailies:
        dates.append(d.get("date",""))
        u = d.get(key, {})
        if isinstance(u, dict):
            records  = u.get("sector_flow", [])
            # 신고가 종목 누적
            for r in u.get("highs", []):
                highs_set.add((r["ticker"], r.get("sector","Unknown")))
            # 종목 누적
            for r in u.get("top_amount", []):
                t = r["ticker"]
                if t not in ticker_map:
                    ticker_map[t] = {"ticker":t,"sector":r.get("sector","Unknown"),"amount":0,"chg_sum":0,"days":0}
                ticker_map[t]["amount"]   += r.get("amount",0)
                ticker_map[t]["chg_sum"]  += r.get("change_pct",0)
                ticker_map[t]["days"]     += 1
            for s in records:
                sec = s.get("sector","Unknown")
                if sec not in sector_map:
                    sector_map[sec] = {"amount":0,"chg_sum":0,"days":0}
                sector_map[sec]["amount"]  += s.get("amount",0)
                sector_map[sec]["chg_sum"] += s.get("avg_change",0)
                sector_map[sec]["days"]    += 1

    sector_flow = sorted([
        {"sector":sec,"amount":v["amount"],
         "avg_change":round(v["chg_sum"]/max(v["days"],1),2),"days":v["days"]}
        for sec,v in sector_map.items()
    ], key=lambda x: x["amount"], reverse=True)

    top_tickers = sorted(ticker_map.values(), key=lambda x: x["amount"], reverse=True)[:10]
    highs_list  = [{"ticker":t,"sector":s} for t,s in highs_set]

    return {"dates":dates,"sector_flow":sector_flow,"top_tickers":top_tickers,"highs":highs_list}


def _render_flow(sf):
    if not sf: return "<p style='color:#9CA3AF'>데이터 없음</p>"
    max_amt = sf[0]["amount"]
    html = ""
    for s in sf[:10]:
        sec   = s["sector"]
        color = sec_color(sec)
        bar_w = int(s["amount"]/max_amt*100)
        cc    = chg_cls(s["avg_change"])
        html += f"""
        <div class="sb-block">
          <div class="sb-hd">
            <div class="sb-left"><span class="sb-ic">{sec_icon(sec)}</span><span class="sb-nm">{sec}</span></div>
            <div class="sb-right">
              <span class="sb-amt">{fmt_amount(s['amount'])}</span>
              <span class="sb-badge {cc}">{chg_sign(s['avg_change'])}/일</span>
              <span class="sb-badge">{s['days']}일</span>
            </div>
          </div>
          <div class="sb-track"><div class="sb-fill" style="width:{bar_w}%;background:{color}"></div></div>
        </div>"""
    return html


def _render_tickers(tickers):
    if not tickers: return "<p style='color:#9CA3AF'>데이터 없음</p>"
    rows = ""
    for r in tickers:
        color = sec_color(r.get("sector","Unknown"))
        rows += f"""
        <div class="bx-row">
          <span class="bx-nm">{r['ticker']}</span>
          <span class="bx-sec" style="background:{color}">{r.get('sector','')[:10]}</span>
          <div class="bx-r"><span style="color:#9CA3AF;font-size:11px">{fmt_amount(r['amount'])}</span></div>
        </div>"""
    return rows


def _render_highs(highs):
    if not highs: return "<p style='color:#9CA3AF'>신고가 종목 없음</p>"
    by_sec = {}
    for r in highs:
        sec = r.get("sector","Unknown")
        by_sec.setdefault(sec,[]).append(r["ticker"])
    html = '<div class="hl-grid">'
    for sec, tickers in sorted(by_sec.items(), key=lambda x: len(x[1]), reverse=True):
        color = sec_color(sec)
        chips = "".join(f'<span class="hl-chip"><span class="hl-nm">{t}</span></span>' for t in tickers[:8])
        html += f"""
        <div class="hl-sec">
          <div class="hl-sec-hd" style="border-left:3px solid {color}">
            <span class="hl-sec-nm">{sec_icon(sec)} {sec}</span>
            <span class="hl-sec-cnt">{len(tickers)}개</span>
          </div>
          <div class="hl-chips">{chips}</div>
        </div>"""
    html += "</div>"
    return html


def generate_period_html(sp500, ndx200, date_str, period_label, period_str):
    dates = sp500.get("dates",[])
    n     = len(dates)
    sf1   = sp500.get("sector_flow",[])
    sf2   = ndx200.get("sector_flow",[])
    top1  = sp500.get("top_tickers",[])
    top2  = ndx200.get("top_tickers",[])
    h1    = sp500.get("highs",[])
    h2    = ndx200.get("highs",[])

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>US Market {period_label} — {date_str}</title>
<style>{CSS}</style>
</head>
<body>
<div class="page">
  <div class="hd-top">
    <div>
      <div class="hd-title">🇺🇸 US Market {period_label}</div>
      <div class="hd-sub">{period_str} · {n}거래일 집계</div>
    </div>
    <div><a href="../index.html" style="font-size:12px;color:#3B82F6">← 목록으로</a></div>
  </div>

  <div class="sec"><div class="sec-title">섹터 누적 자금흐름 — S&P 500</div>{_render_flow(sf1)}</div>
  <div class="sec"><div class="sec-title">섹터 누적 자금흐름 — Nasdaq 200</div>{_render_flow(sf2)}</div>

  <div class="sec">
    <div class="sec-title">거래대금 누적 Top 종목</div>
    <div class="box-grid">
      <div class="bx"><div class="bx-hd">S&P 500</div>{_render_tickers(top1)}</div>
      <div class="bx"><div class="bx-hd">Nasdaq 200</div>{_render_tickers(top2)}</div>
    </div>
  </div>

  <div class="sec"><div class="sec-title">기간 내 52주 신고가 종목 — S&P 500</div>{_render_highs(h1)}</div>
  <div class="sec"><div class="sec-title">기간 내 52주 신고가 종목 — Nasdaq 200</div>{_render_highs(h2)}</div>
</div>
</body>
</html>"""


def build_biweekly_report(date_str=None):
    if date_str is None: date_str = str(datetime.date.today())
    dailies = load_recent_dailies(10)
    if not dailies: print("❌ 데이터 없음"); return
    sp500  = aggregate_universe(dailies, "sp500")
    ndx200 = aggregate_universe(dailies, "nasdaq100")
    dates  = sp500.get("dates",[])
    period = f"{dates[-1]} ~ {dates[0]}" if dates else date_str
    html   = generate_period_html(sp500, ndx200, date_str, "격주 리포트", period)
    out_dir = DOCS_DIR / "biweekly"; out_dir.mkdir(exist_ok=True)
    out = out_dir / f"{date_str}.html"
    with open(out,"w",encoding="utf-8") as f: f.write(html)
    print(f"✅ 격주 리포트: {out}")
    return str(out)


if __name__ == "__main__":
    build_biweekly_report()
