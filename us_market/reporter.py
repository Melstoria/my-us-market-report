"""
reporter.py
분석 결과를 Apple 스타일 HTML 리포트로 변환
"""

import json
import datetime
from pathlib import Path


DOCS_DIR = Path(__file__).parent.parent / "docs"
DOCS_DIR.mkdir(exist_ok=True)


# ──────────────────────────────────────────
# 헬퍼
# ──────────────────────────────────────────

def fmt_amount(v: float) -> str:
    """거래대금: B / M 단위 포맷"""
    if v >= 1_000_000_000:
        return f"${v/1_000_000_000:.1f}B"
    elif v >= 1_000_000:
        return f"${v/1_000_000:.0f}M"
    return f"${v:,.0f}"

def chg_class(v: float) -> str:
    if v > 0: return "pos"
    if v < 0: return "neg"
    return "neu"

def chg_sign(v: float) -> str:
    return f"+{v:.2f}%" if v > 0 else f"{v:.2f}%"

def sector_bar(pct: float, max_pct: float) -> int:
    if max_pct == 0: return 0
    return int(abs(pct) / max_pct * 100)


# ──────────────────────────────────────────
# 섹션 렌더러
# ──────────────────────────────────────────

def render_index_cards(index: dict) -> str:
    order = ["SPY", "QQQ", "DIA", "IWM"]
    vix   = index.get("VIX", {})
    cards = ""
    for sym in order:
        d = index.get(sym, {})
        if not d: continue
        cc = chg_class(d["change_pct"])
        cards += f"""
        <div class="index-card">
          <div class="index-sym">{sym}</div>
          <div class="index-name">{d['name']}</div>
          <div class="index-price">{d['price']:,.2f}</div>
          <div class="index-chg {cc}">{chg_sign(d['change_pct'])}</div>
        </div>"""

    # VIX 별도
    if vix:
        cc = "neg" if vix["change_pct"] > 0 else "pos"
        cards += f"""
        <div class="index-card vix-card">
          <div class="index-sym">VIX</div>
          <div class="index-name">Fear Index</div>
          <div class="index-price">{vix['price']:.2f}</div>
          <div class="index-chg {cc}">{chg_sign(vix['change_pct'])}</div>
        </div>"""
    return cards


def render_sector_etf(sector_etf: dict) -> str:
    items = sorted(sector_etf.items(), key=lambda x: x[1]["change_pct"], reverse=True)
    max_abs = max(abs(v["change_pct"]) for _, v in items) if items else 1
    rows = ""
    for sym, d in items:
        cc  = chg_class(d["change_pct"])
        bar = sector_bar(d["change_pct"], max_abs)
        dir_ = "bar-pos" if d["change_pct"] >= 0 else "bar-neg"
        rows += f"""
        <div class="sector-row">
          <div class="sector-name">{d['name']}</div>
          <div class="sector-bar-wrap">
            <div class="sector-bar {dir_}" style="width:{bar}%"></div>
          </div>
          <div class="sector-chg {cc}">{chg_sign(d['change_pct'])}</div>
        </div>"""
    return rows


def render_universe_tab(u: dict) -> str:
    """S&P500 또는 Nasdaq100 탭 콘텐츠"""
    if not u:
        return "<p class='empty'>데이터 없음</p>"

    # 신고가 테이블
    def stock_rows(records, show_sector=True):
        rows = ""
        for r in records[:30]:
            cc = chg_class(r.get("change_pct", 0))
            sec_cell = f"<td class='sec'>{r.get('sector','')}</td>" if show_sector else ""
            rows += f"""
            <tr>
              <td class="ticker">{r['ticker']}</td>
              {sec_cell}
              <td class="price">${r.get('close',0):,.2f}</td>
              <td class="{cc}">{chg_sign(r.get('change_pct',0))}</td>
              <td class="amount">{fmt_amount(r.get('amount',0))}</td>
            </tr>"""
        return rows

    # 섹터 자금흐름
    sf = u.get("sector_flow", [])
    max_amt = sf[0]["amount"] if sf else 1
    sector_rows = ""
    for s in sf:
        bar_w = int(s["amount"] / max_amt * 100)
        cc    = chg_class(s["avg_change"])
        sector_rows += f"""
        <div class="sector-row">
          <div class="sector-name">{s['sector']} <span class="sec-count">({s['count']})</span></div>
          <div class="sector-bar-wrap">
            <div class="sector-bar bar-neu" style="width:{bar_w}%"></div>
          </div>
          <div class="sector-amt">{fmt_amount(s['amount'])}</div>
          <div class="sector-chg {cc}">{chg_sign(s['avg_change'])}</div>
        </div>"""

    highs_count = u.get("highs_count", 0)
    total       = u.get("total", 0)

    return f"""
    <div class="uni-stats">
      <div class="stat-chip">총 {total}종목</div>
      <div class="stat-chip highlight">52주 신고가 {highs_count}종목</div>
      <div class="stat-chip">모멘텀 {len(u.get('momentum',[]))}종목</div>
    </div>

    <div class="section-grid">

      <!-- 섹터 자금흐름 -->
      <div class="card full-width">
        <div class="card-title">섹터별 자금흐름 (거래대금 기준)</div>
        <div class="sector-list">{sector_rows}</div>
      </div>

      <!-- 거래대금 Top 30 -->
      <div class="card">
        <div class="card-title">거래대금 Top 30</div>
        <table class="stock-table">
          <thead><tr><th>티커</th><th>섹터</th><th>종가</th><th>등락</th><th>거래대금</th></tr></thead>
          <tbody>{stock_rows(u.get('top_amount',[]))}</tbody>
        </table>
      </div>

      <!-- 52주 신고가 -->
      <div class="card">
        <div class="card-title">52주 신고가 돌파</div>
        <table class="stock-table">
          <thead><tr><th>티커</th><th>섹터</th><th>종가</th><th>등락</th><th>거래대금</th></tr></thead>
          <tbody>{stock_rows(u.get('highs',[]))}</tbody>
        </table>
      </div>

      <!-- 모멘텀 (신고가 + 거래대금 동시) -->
      <div class="card">
        <div class="card-title">⚡ 모멘텀 종목 <span class="subtitle">(신고가 + 거래대금 상위)</span></div>
        <table class="stock-table">
          <thead><tr><th>티커</th><th>섹터</th><th>종가</th><th>등락</th><th>거래대금</th></tr></thead>
          <tbody>{stock_rows(u.get('momentum',[]))}</tbody>
        </table>
      </div>

      <!-- 상승 Top 10 -->
      <div class="card half">
        <div class="card-title">상승률 Top 10</div>
        <table class="stock-table">
          <thead><tr><th>티커</th><th>등락</th><th>거래대금</th></tr></thead>
          <tbody>{"".join(f"<tr><td class='ticker'>{r['ticker']}</td><td class='pos'>{chg_sign(r.get('change_pct',0))}</td><td class='amount'>{fmt_amount(r.get('amount',0))}</td></tr>" for r in u.get('top_gainers',[]))}</tbody>
        </table>
      </div>

      <!-- 하락 Top 10 -->
      <div class="card half">
        <div class="card-title">하락률 Top 10</div>
        <table class="stock-table">
          <thead><tr><th>티커</th><th>등락</th><th>거래대금</th></tr></thead>
          <tbody>{"".join(f"<tr><td class='ticker'>{r['ticker']}</td><td class='neg'>{chg_sign(r.get('change_pct',0))}</td><td class='amount'>{fmt_amount(r.get('amount',0))}</td></tr>" for r in u.get('top_losers',[]))}</tbody>
        </table>
      </div>

    </div>
    """


def render_cross(cross: list[dict]) -> str:
    """S&P500 + Nasdaq100 동시 신고가 크로스 시그널"""
    if not cross:
        return "<p class='empty'>당일 크로스 시그널 없음</p>"
    rows = ""
    for r in cross[:20]:
        cc = chg_class(r.get("change_pct", 0))
        rows += f"""
        <tr>
          <td class="ticker">{r['ticker']}</td>
          <td class="sec">{r.get('sector','')}</td>
          <td class="price">${r.get('close',0):,.2f}</td>
          <td class="{cc}">{chg_sign(r.get('change_pct',0))}</td>
          <td class="amount">{fmt_amount(r.get('amount',0))}</td>
          <td class="high">${r.get('high_52w',0):,.2f}</td>
        </tr>"""
    return f"""
    <div class="cross-desc">S&amp;P 500 <em>AND</em> Nasdaq 100 동시 52주 신고가 돌파 — 가장 강한 모멘텀 시그널</div>
    <table class="stock-table">
      <thead><tr><th>티커</th><th>섹터</th><th>종가</th><th>등락</th><th>거래대금</th><th>52주고가</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>"""


# ──────────────────────────────────────────
# HTML 최종 조립
# ──────────────────────────────────────────

CSS = """
:root {
  --bg:       #ffffff;
  --bg2:      #f5f5f7;
  --bg3:      #e8e8ed;
  --text:     #1d1d1f;
  --text2:    #6e6e73;
  --text3:    #aeaeb2;
  --accent:   #0071e3;
  --pos:      #34c759;
  --neg:      #ff3b30;
  --neu:      #8e8e93;
  --border:   #d2d2d7;
  --radius:   14px;
  --shadow:   0 2px 16px rgba(0,0,0,.06);
}

* { margin:0; padding:0; box-sizing:border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
  background: var(--bg); color: var(--text);
  font-size: 14px; line-height: 1.5;
}

/* ── 헤더 ── */
.header {
  background: rgba(255,255,255,.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
  position: sticky; top: 0; z-index: 100;
  padding: 0 32px;
}
.header-inner {
  max-width: 1280px; margin: 0 auto;
  display: flex; align-items: center;
  justify-content: space-between;
  height: 56px;
}
.logo { font-size: 17px; font-weight: 600; letter-spacing: -.3px; }
.logo span { color: var(--accent); }
.date-badge {
  font-size: 12px; color: var(--text2);
  background: var(--bg2); border-radius: 20px;
  padding: 4px 12px;
}

/* ── 지수 카드 ── */
.index-strip {
  background: var(--bg2);
  border-bottom: 1px solid var(--border);
  padding: 16px 32px;
}
.index-strip-inner {
  max-width: 1280px; margin: 0 auto;
  display: flex; gap: 12px; flex-wrap: wrap;
}
.index-card {
  background: var(--bg); border-radius: var(--radius);
  border: 1px solid var(--border);
  padding: 14px 20px; min-width: 140px;
  box-shadow: var(--shadow);
}
.vix-card { border-color: #ff9f0a44; }
.index-sym  { font-size: 11px; font-weight: 600; color: var(--text2); letter-spacing: .5px; text-transform: uppercase; }
.index-name { font-size: 11px; color: var(--text3); margin-top: 1px; }
.index-price { font-size: 20px; font-weight: 600; margin-top: 6px; letter-spacing: -.4px; }
.index-chg  { font-size: 13px; font-weight: 500; margin-top: 2px; }

/* ── 색상 ── */
.pos { color: var(--pos); }
.neg { color: var(--neg); }
.neu { color: var(--neu); }

/* ── 탭 ── */
.tab-bar {
  max-width: 1280px; margin: 0 auto;
  padding: 24px 32px 0;
  display: flex; gap: 4px;
}
.tab-btn {
  padding: 8px 20px; border-radius: 20px;
  border: 1px solid var(--border);
  background: var(--bg); color: var(--text2);
  font-size: 13px; font-weight: 500;
  cursor: pointer; transition: all .2s;
}
.tab-btn.active {
  background: var(--text); color: #fff; border-color: var(--text);
}

/* ── 탭 콘텐츠 ── */
.tab-content { display: none; }
.tab-content.active { display: block; }

/* ── 메인 레이아웃 ── */
.main { max-width: 1280px; margin: 0 auto; padding: 24px 32px 60px; }

.uni-stats {
  display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px;
}
.stat-chip {
  padding: 6px 14px; border-radius: 20px;
  background: var(--bg2); font-size: 12px; color: var(--text2);
  border: 1px solid var(--border);
}
.stat-chip.highlight {
  background: #0071e318; color: var(--accent); border-color: #0071e344;
}

.section-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.card {
  background: var(--bg); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 20px;
  box-shadow: var(--shadow);
}
.card.full-width { grid-column: 1 / -1; }
.card.half { }

.card-title {
  font-size: 13px; font-weight: 600; color: var(--text);
  margin-bottom: 14px; letter-spacing: -.1px;
}
.card-title .subtitle { font-weight: 400; color: var(--text2); }

/* ── 섹터 바 ── */
.sector-list { display: flex; flex-direction: column; gap: 8px; }
.sector-row  { display: flex; align-items: center; gap: 10px; }
.sector-name { width: 200px; font-size: 12px; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sec-count   { color: var(--text3); font-size: 11px; }
.sector-bar-wrap { flex: 1; height: 6px; background: var(--bg3); border-radius: 3px; overflow: hidden; }
.sector-bar  { height: 100%; border-radius: 3px; transition: width .4s; }
.bar-pos { background: var(--pos); }
.bar-neg { background: var(--neg); }
.bar-neu { background: var(--accent); }
.sector-amt  { width: 70px; font-size: 11px; color: var(--text2); text-align: right; }
.sector-chg  { width: 56px; font-size: 12px; font-weight: 500; text-align: right; }

/* ── 테이블 ── */
.stock-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.stock-table thead th {
  padding: 6px 8px; text-align: left;
  color: var(--text3); font-weight: 500;
  border-bottom: 1px solid var(--border);
  font-size: 11px;
}
.stock-table tbody tr { border-bottom: 1px solid var(--bg2); }
.stock-table tbody tr:hover { background: var(--bg2); }
.stock-table td { padding: 7px 8px; }
.ticker { font-weight: 600; font-size: 12px; color: var(--text); font-family: "SF Mono", monospace; }
.price  { color: var(--text); }
.amount { color: var(--text2); }
.sec    { color: var(--text3); font-size: 11px; }
.high   { color: var(--text2); }

/* ── 크로스 시그널 ── */
.cross-desc {
  font-size: 13px; color: var(--text2); margin-bottom: 16px;
  padding: 12px 16px; background: var(--bg2); border-radius: 10px;
}
.cross-desc em { font-style: normal; font-weight: 600; color: var(--accent); }

/* ── 섹터 ETF 스트립 ── */
.etf-section {
  max-width: 1280px; margin: 0 auto;
  padding: 20px 32px 0;
}
.etf-title { font-size: 13px; font-weight: 600; color: var(--text2); margin-bottom: 10px; }

.empty { color: var(--text3); font-size: 13px; padding: 20px; }

@media (max-width: 768px) {
  .header-inner, .index-strip-inner, .tab-bar, .main, .etf-section { padding-left: 16px; padding-right: 16px; }
  .section-grid { grid-template-columns: 1fr; }
  .card.full-width { grid-column: 1; }
  .sector-name { width: 140px; }
}
"""

JS = """
function switchTab(id) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  document.querySelector('[data-tab="' + id + '"]').classList.add('active');
  document.getElementById(id).classList.add('active');
}
"""


def generate_html(analyzed: dict) -> str:
    date_str     = analyzed.get("date", str(datetime.date.today()))
    index        = analyzed.get("index", {})
    sector_etf   = analyzed.get("sector_etf", {})
    sp500        = analyzed.get("sp500", {})
    nasdaq100    = analyzed.get("nasdaq100", {})
    cross        = analyzed.get("cross", [])

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>US Market Report — {date_str}</title>
<style>{CSS}</style>
</head>
<body>

<header class="header">
  <div class="header-inner">
    <div class="logo">US Market <span>Report</span></div>
    <div class="date-badge">{date_str} · EST Close</div>
  </div>
</header>

<!-- 지수 카드 -->
<div class="index-strip">
  <div class="index-strip-inner">
    {render_index_cards(index)}
  </div>
</div>

<!-- 섹터 ETF -->
<div class="etf-section">
  <div class="etf-title">섹터 ETF 등락</div>
  <div class="card full-width" style="padding:16px 20px;">
    <div class="sector-list">{render_sector_etf(sector_etf)}</div>
  </div>
</div>

<!-- 탭 -->
<div class="tab-bar">
  <button class="tab-btn active" data-tab="sp500"    onclick="switchTab('sp500')">S&amp;P 500</button>
  <button class="tab-btn"        data-tab="nasdaq100" onclick="switchTab('nasdaq100')">Nasdaq 100</button>
  <button class="tab-btn"        data-tab="cross"     onclick="switchTab('cross')">⚡ 크로스 시그널</button>
</div>

<div class="main">

  <div class="tab-content active" id="sp500">
    {render_universe_tab(sp500)}
  </div>

  <div class="tab-content" id="nasdaq100">
    {render_universe_tab(nasdaq100)}
  </div>

  <div class="tab-content" id="cross">
    <div class="uni-stats">
      <div class="stat-chip highlight">S&amp;P500 + Nasdaq100 동시 신고가: {len(cross)}종목</div>
    </div>
    <div class="card full-width">
      <div class="card-title">⚡ 크로스 시그널 — 최강 모멘텀</div>
      {render_cross(cross)}
    </div>
  </div>

</div>

<script>{JS}</script>
</body>
</html>"""


# ──────────────────────────────────────────
# 메인
# ──────────────────────────────────────────

def build_report(analyzed: dict):
    date_str = analyzed.get("date", str(datetime.date.today()))
    html     = generate_html(analyzed)

    # 날짜별 파일
    out_path = DOCS_DIR / f"report_{date_str}.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    # index.html (최신)
    idx_path = DOCS_DIR / "index.html"
    with open(idx_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ 리포트 생성: {out_path}")
    return str(out_path)


if __name__ == "__main__":
    from pathlib import Path
    import json
    from analyzer import analyze

    latest = Path(__file__).parent.parent / "data" / "market_latest.json"
    with open(latest) as f:
        raw = json.load(f)
    analyzed = analyze(raw)
    build_report(analyzed)
