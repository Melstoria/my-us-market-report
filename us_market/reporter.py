"""
reporter.py — US Market Report (Korean daily report style)
"""

import json
import datetime
from pathlib import Path

DOCS_DIR = Path(__file__).parent.parent / "docs"
DOCS_DIR.mkdir(exist_ok=True)

# ── 섹터 색상 ──────────────────────────────
SECTOR_COLORS = {
    "Technology":             "#3B82F6",
    "Financials":             "#10B981",
    "Healthcare":             "#EF4444",
    "Consumer Discretionary": "#F59E0B",
    "Consumer Staples":       "#84CC16",
    "Energy":                 "#F97316",
    "Industrials":            "#6366F1",
    "Materials":              "#EC4899",
    "Real Estate":            "#14B8A6",
    "Utilities":              "#8B5CF6",
    "Communication Services": "#0EA5E9",
    "Unknown":                "#9CA3AF",
}

SECTOR_ICONS = {
    "Technology":             "💻",
    "Financials":             "🏦",
    "Healthcare":             "#🧬",
    "Consumer Discretionary": "🛍",
    "Consumer Staples":       "🛒",
    "Energy":                 "⚡",
    "Industrials":            "🏭",
    "Materials":              "🔩",
    "Real Estate":            "🏢",
    "Utilities":              "💡",
    "Communication Services": "📡",
    "Unknown":                "📊",
}

def sec_color(s): return SECTOR_COLORS.get(s, "#9CA3AF")
def sec_icon(s):  return SECTOR_ICONS.get(s, "📊")

def fmt_amount(v):
    if v >= 1_000_000_000: return f"${v/1_000_000_000:.1f}B"
    if v >= 1_000_000:     return f"${v/1_000_000:.0f}M"
    return f"${v:,.0f}"

def chg_cls(v):  return "up" if v > 0 else ("dn" if v < 0 else "neu")
def chg_sign(v): return f"+{v:.2f}%" if v > 0 else f"{v:.2f}%"


# ── 섹터 자금흐름 블록 ─────────────────────

def render_sector_flow(sector_flow, top_amount=None):
    """섹터별 바 + 대표 종목 pill (sector_flow[top_stocks] 사용)"""
    if not sector_flow:
        return "<p style='color:#9CA3AF'>데이터 없음</p>"

    max_amt = sector_flow[0]["amount"] if sector_flow else 1
    html = ""
    for s in sector_flow[:10]:
        sec   = s["sector"]
        color = sec_color(sec)
        icon  = sec_icon(sec)
        bar_w = int(s["amount"] / max_amt * 100)
        cc    = chg_cls(s["avg_change"])
        sign  = chg_sign(s["avg_change"])

        # 대표 종목 pills — sector_flow 안의 top_stocks 직접 사용
        pills = ""
        for r in s.get("top_stocks", [])[:10]:
            pc = chg_cls(r.get("change_pct", 0))
            pills += f"""<span class="st-pill">
              <span class="st-name">{r['ticker']}</span>
              <span class="st-sep">|</span>
              <span class="st-amt">{fmt_amount(r.get('amount',0))}</span>
              <span class="st-sep">|</span>
              <span class="st-pct {pc}">{chg_sign(r.get('change_pct',0))}</span>
            </span>"""

        html += f"""
        <div class="sb-block">
          <div class="sb-hd">
            <div class="sb-left">
              <span class="sb-ic">{icon}</span>
              <span class="sb-nm">{sec}</span>
            </div>
            <div class="sb-right">
              <span class="sb-amt">{fmt_amount(s['amount'])}</span>
              <span class="sb-badge {cc}">{sign}</span>
              <span class="sb-badge">{s['count']}종목</span>
            </div>
          </div>
          <div class="sb-track"><div class="sb-fill" style="width:{bar_w}%;background:{color}"></div></div>
          <div class="st-pills">{pills}</div>
        </div>"""
    return html


# ── 스코어카드 ─────────────────────────────

def render_scorecard(sector_flow):
    if not sector_flow:
        return ""
    max_amt = sector_flow[0]["amount"]
    rows = ""
    for i, s in enumerate(sector_flow[:10]):
        sec   = s["sector"]
        color = sec_color(sec)
        bar_w = int(s["amount"] / max_amt * 100)
        cc    = chg_cls(s["avg_change"])
        rows += f"""
        <tr>
          <td class="sc-rk">{i+1}</td>
          <td class="sc-sc">{sec_icon(sec)} {sec}</td>
          <td class="sc-am">{fmt_amount(s['amount'])}</td>
          <td><div class="sc-br">
            <div class="sc-track"><div class="sc-fill" style="width:{bar_w}%;background:{color}"></div></div>
            <span class="sc-val">{bar_w}</span>
          </div></td>
          <td class="sc-ch {cc}">{chg_sign(s['avg_change'])}</td>
          <td class="sc-sh">{s['count']}</td>
        </tr>"""
    return f"""
    <table class="sc-table">
      <thead><tr><th>#</th><th>섹터</th><th>거래대금</th><th>강도</th><th>평균등락</th><th>종목수</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>"""


# ── 신고가 섹터별 ──────────────────────────

def render_highs_by_sector(highs):
    if not highs:
        return "<p style='color:#9CA3AF'>신고가 종목 없음</p>"

    by_sec = {}
    for r in highs:
        sec = r.get("sector", "Unknown")
        by_sec.setdefault(sec, []).append(r)

    # 거래대금 기준 섹터 정렬
    sec_order = sorted(by_sec.keys(), key=lambda s: sum(r.get("amount",0) for r in by_sec[s]), reverse=True)

    html = '<div class="hl-grid">'
    for sec in sec_order:
        items = sorted(by_sec[sec], key=lambda x: x.get("amount",0), reverse=True)
        color = sec_color(sec)
        icon  = sec_icon(sec)
        chips = ""
        for r in items[:6]:
            pc = chg_cls(r.get("change_pct", 0))
            chips += f"""<span class="hl-chip">
              <span class="hl-nm">{r['ticker']}</span>
              <span class="hl-pct {pc}">{chg_sign(r.get('change_pct',0))}</span>
            </span>"""
        html += f"""
        <div class="hl-sec">
          <div class="hl-sec-hd" style="border-left:3px solid {color}">
            <span class="hl-sec-nm">{icon} {sec}</span>
            <span class="hl-sec-cnt">{len(items)}개</span>
          </div>
          <div class="hl-chips">{chips}</div>
        </div>"""
    html += "</div>"
    return html


# ── 4박스 (모멘텀·상승·하락·신고가+거래량) ─

def render_4boxes(u):
    def rows(records, show_vol=False):
        out = ""
        for r in records[:5]:
            pc  = chg_cls(r.get("change_pct",0))
            sec = r.get("sector","")
            color = sec_color(sec)
            extra = ""
            if show_vol and r.get("volume",0) > 0:
                extra = f'<span class="bx-vol">Vol {r["volume"]/1_000_000:.1f}M</span>'
            out += f"""
            <div class="bx-row">
              <span class="bx-nm">{r['ticker']}</span>
              <span class="bx-sec" style="background:{color}">{sec[:12]}</span>
              <div class="bx-r">
                <span class="bx-pct {pc}">{chg_sign(r.get('change_pct',0))}</span>
                {extra}
              </div>
            </div>"""
        return out

    momentum  = u.get("momentum", [])
    gainers   = u.get("top_gainers", [])
    losers    = u.get("top_losers", [])
    top_amt   = u.get("top_amount", [])

    return f"""
    <div class="box-grid">
      <div class="bx">
        <div class="bx-hd">⚡ 모멘텀 (신고가+거래대금)</div>
        {rows(momentum[:5])}
      </div>
      <div class="bx">
        <div class="bx-hd">🚀 상승률 Top</div>
        {rows(gainers[:5])}
      </div>
      <div class="bx">
        <div class="bx-hd">📉 하락률 Top</div>
        {rows(losers[:5])}
      </div>
      <div class="bx">
        <div class="bx-hd">💰 거래대금 Top</div>
        {rows(top_amt[:5], show_vol=True)}
      </div>
    </div>"""


# ── 시장 레짐 ─────────────────────────────

def render_regime(u, label):
    sf = u.get("sector_flow", [])
    highs_count = u.get("highs_count", 0)
    total = u.get("total", 1)
    momentum = u.get("momentum", [])

    # 주도 섹터
    top_sec = sf[0]["sector"] if sf else "—"
    top_sec_pct = int(sf[0]["amount"] / sum(s["amount"] for s in sf) * 100) if sf else 0
    top_color = sec_color(top_sec)

    # 태그 생성
    tags = []
    if top_sec_pct >= 30:
        tags.append((f"{top_sec} 집중", top_color))
    if highs_count >= 10:
        tags.append(("신고가 러시", "#F59E0B"))
    elif highs_count == 0:
        tags.append(("신고가 없음", "#9CA3AF"))
    if len(momentum) >= 5:
        tags.append(("모멘텀 강화", "#10B981"))
    if sf and sf[0]["avg_change"] < 0:
        tags.append(("주도섹터 약세", "#EF4444"))
    else:
        tags.append(("주도섹터 강세", "#3B82F6"))

    tag_html = ""
    for text, color in tags:
        tag_html += f'<span class="rg-tag" style="background:{color}20;color:{color};border:1px solid {color}50">{text}</span>'

    regime_txt = (
        f"{top_sec}에 자금 {top_sec_pct}% 집중. "
        f"52주 신고가 {highs_count}개 — {'추세 강화' if highs_count >= 10 else '신중 접근'}. "
        f"모멘텀 종목 {len(momentum)}개 포착."
    )

    return f"""
    <div class="rg-tags">{tag_html}</div>
    <div class="rg-txt">{regime_txt}</div>"""


# ── 전략 카드 ─────────────────────────────

def render_strategy(u, label):
    sf          = u.get("sector_flow", [])
    highs       = u.get("highs", [])
    momentum    = u.get("momentum", [])
    top_gainers = u.get("top_gainers", [])
    highs_count = u.get("highs_count", 0)

    # 주도 섹터 top3
    top_secs   = [s["sector"] for s in sf[:3]]
    top1       = top_secs[0] if top_secs else "—"
    top2       = top_secs[1] if len(top_secs) > 1 else "—"
    chips      = "".join(f'<span class="st-chip">{s}</span>' for s in top_secs)

    # 장세 판단
    bull_secs  = [s for s in sf if s["avg_change"] > 0]
    bear_secs  = [s for s in sf if s["avg_change"] < 0]
    is_bull    = len(bull_secs) >= len(bear_secs)
    is_broad   = len(bull_secs) >= 7   # 광범위 상승
    top1_chg   = sf[0]["avg_change"] if sf else 0

    # 단기 대표 모멘텀 종목 (신고가+거래대금 top3)
    mom_tickers = [r["ticker"] for r in momentum[:3]]
    mom_str     = ", ".join(mom_tickers) if mom_tickers else "—"

    # 단기 상승률 top 종목
    gain_tickers = [r["ticker"] for r in top_gainers[:3]]
    gain_str     = ", ".join(gain_tickers) if gain_tickers else "—"

    # 단기 전략
    if is_bull and highs_count >= 10:
        short_stance = "신고가 모멘텀 추종"
        short_pts = [
            f"주도섹터 {top1} 신고가 종목 ({mom_str}) 단기 트레이딩",
            f"거래대금 상위 + 신고가 동시 충족 종목 우선 진입",
            f"상승률 상위 ({gain_str}) 눌림목 재진입 노려볼 것",
        ]
    elif is_bull:
        short_stance = "선별적 모멘텀"
        short_pts = [
            f"주도섹터 {top1} 거래대금 상위 종목 단기 트레이딩",
            f"신고가 {highs_count}개 — 종목 선별 신중하게",
            f"상승률 상위 ({gain_str}) 추격보다 눌림목 진입",
        ]
    else:
        short_stance = "관망·헤지"
        short_pts = [
            f"주도섹터 {top1}만 부분 트레이딩, 나머지 관망",
            f"신고가 {highs_count}개 — 추세 약화, 무리한 추격 자제",
            f"하락 섹터 ({len(bear_secs)}개) 비중 축소 우선",
        ]

    # 중기 전략
    if is_broad:
        mid_stance = "광범위 상승 — 전 섹터 비중 확대"
        mid_pts = [
            f"전 섹터 동반 상승 — {top1}, {top2} 중심 비중 확대",
            f"신고가 돌파 종목 ({highs_count}개) 분할 매수",
            f"주도섹터 교체 신호 시 2위 섹터로 선제 이동",
        ]
    else:
        mid_stance = "섹터 로테이션 집중"
        mid_pts = [
            f"강세 섹터 ({len(bull_secs)}개) 집중, 약세 섹터 ({len(bear_secs)}개) 축소",
            f"신고가 돌파 {top1} 종목 중기 홀딩",
            f"크로스 시그널 종목 (S&P500∩Nasdaq200 동시 신고가) 우선 편입",
        ]

    # 장기 전략 — 섹터별 맞춤
    tech_strong = any(s["sector"] in ["Technology","Communication Services"] and s["avg_change"] > 0 for s in sf)
    health_strong = any(s["sector"] == "Healthcare" and s["avg_change"] > 0 for s in sf)

    if tech_strong:
        long_stance = "AI·반도체 구조적 성장 보유"
        long_pts = [
            "AI·반도체·클라우드 대형주 핵심 포지션 장기 유지",
            "PEG 1 이하 기술 성장주 구간별 분할 적립",
            "배당성장 + 자사주 매입 기업 복리 수익 극대화",
        ]
    elif health_strong:
        long_stance = "헬스케어·바이오 구조적 보유"
        long_pts = [
            "GLP-1·항암·유전자치료 테마 대형 바이오 장기 보유",
            "헬스케어 대형주 밸류에이션 매력 구간 분할 적립",
            "배당성장 + 자사주 매입 기업 복리 수익 극대화",
        ]
    else:
        long_stance = "대형 우량주 구조적 보유"
        long_pts = [
            f"{top1} 구조적 성장 대형주 핵심 포지션 유지",
            "PEG 1 이하 성장주 구간별 분할 적립",
            "배당성장 + 자사주 매입 기업 복리 수익 극대화",
        ]

    def pts(items):
        return "".join(f"<li>{p}</li>" for p in items)

    return f"""
    <div class="strat-grid">
      <div class="strat-card" style="border-top:3px solid #3B82F6">
        <div class="strat-hd">
          <span class="strat-lbl" style="color:#3B82F6">단기</span>
          <span class="strat-period">1~5일</span>
          <span class="strat-stance">{short_stance}</span>
        </div>
        <ul class="strat-pts">{pts(short_pts)}</ul>
      </div>
      <div class="strat-card" style="border-top:3px solid #10B981">
        <div class="strat-hd">
          <span class="strat-lbl" style="color:#10B981">중기</span>
          <span class="strat-period">1~3개월</span>
          <span class="strat-stance">{mid_stance}</span>
        </div>
        <div class="strat-chips">{chips}</div>
        <ul class="strat-pts">{pts(mid_pts)}</ul>
      </div>
      <div class="strat-card" style="border-top:3px solid #F59E0B">
        <div class="strat-hd">
          <span class="strat-lbl" style="color:#F59E0B">장기</span>
          <span class="strat-period">6개월+</span>
          <span class="strat-stance">{long_stance}</span>
        </div>
        <ul class="strat-pts">{pts(long_pts)}</ul>
      </div>
    </div>"""


# ── 지수 카드 ──────────────────────────────

def render_index_cards(index):
    order = ["SPY","QQQ","DIA","IWM"]
    names  = {"SPY":"S&P 500","QQQ":"Nasdaq 200","DIA":"Dow Jones","IWM":"Russell 2000"}
    bgs    = {"SPY":"#FFF5F5","QQQ":"#F5F8FF","DIA":"#FFFDF5","IWM":"#F5FFF8"}
    html = ""
    for sym in order:
        d = index.get(sym, {})
        if not d: continue
        chg   = d.get("change_pct", 0)
        color = "#EF4444" if chg >= 0 else "#3B82F6"
        bg    = bgs.get(sym, "#F9FAFB")
        price = f"{d.get('price',0):,.2f}"
        cs    = chg_sign(chg)
        html += (
            f'<div class="kpi" style="background:{bg}">' +
            f'<div class="kpi-lbl">{names.get(sym,sym)} ({sym})</div>' +
            f'<div class="kpi-val" style="color:{color}">{price}</div>' +
            f'<div class="kpi-sub" style="color:{color}">{cs}</div>' +
            f'</div>'
        )
    vix = index.get("VIX", {})
    if vix:
        chg   = vix.get("change_pct", 0)
        # VIX 하락 = 공포 감소 = 파랑(좋음), VIX 상승 = 공포 증가 = 빨강(나쁨)
        color = "#EF4444" if chg > 0 else "#3B82F6"
        price = f"{vix.get('price',0):.2f}"
        cs    = chg_sign(chg)
        html += (
            f'<div class="kpi" style="background:#F8F5FF">' +
            f'<div class="kpi-lbl">VIX 공포지수</div>' +
            f'<div class="kpi-val" style="color:{color}">{price}</div>' +
            f'<div class="kpi-sub" style="color:{color}">{cs}</div>' +
            f'</div>'
        )
    return html


def render_kpi_row(u, label):
    sf        = u.get("sector_flow", [])
    total_amt = sum(s["amount"] for s in sf)
    top_gain  = (u.get("top_gainers") or [{}])[0]
    top_lose  = (u.get("top_losers")  or [{}])[0]
    highs_cnt = u.get("highs_count", 0)
    mom_cnt   = len(u.get("momentum", []))
    highs     = u.get("highs", [])

    # 신고가 chip 생성
    high_chips = ""
    for r in highs[:20]:
        pc    = chg_cls(r.get("change_pct", 0))
        color = sec_color(r.get("sector", "Unknown"))
        cs    = chg_sign(r.get("change_pct", 0))
        tk    = r["ticker"]
        sec   = r.get("sector", "")[:8]
        high_chips += (
            f'<span class="hl-chip">' +
            f'<span class="hl-nm">{tk}</span>' +
            f'<span class="bx-sec" style="background:{color};margin:0 4px">{sec}</span>' +
            f'<span class="hl-pct {pc}">{cs}</span>' +
            f'</span>'
        )
    if not high_chips:
        high_chips = '<span style="color:#9CA3AF;font-size:11px">신고가 종목 없음</span>'

    row = (
        f'<div class="kpi-row" id="kpi-row-{label}">' +
        f'<div class="kpi"><div class="kpi-lbl">{label} 총 거래대금</div>' +
        f'<div class="kpi-val">{fmt_amount(total_amt)}</div>' +
        f'<div class="kpi-sub">{u.get("total",0)}개 종목</div></div>' +
        f'<div class="kpi"><div class="kpi-lbl">최고 상승</div>' +
        f'<div class="kpi-val" style="color:#EF4444">{chg_sign(top_gain.get("change_pct",0))}</div>' +
        f'<div class="kpi-sub">{top_gain.get("ticker","—")}</div></div>' +
        f'<div class="kpi"><div class="kpi-lbl">최대 하락</div>' +
        f'<div class="kpi-val" style="color:#3B82F6">{chg_sign(top_lose.get("change_pct",0))}</div>' +
        f'<div class="kpi-sub">{top_lose.get("ticker","—")}</div></div>' +
        f'<div class="kpi"><div class="kpi-lbl">52주 신고가</div>' +
        f'<div class="kpi-val" style="color:#3B82F6">{highs_cnt}개</div>' +
        f'<div class="kpi-sub">모멘텀 {mom_cnt}개</div></div>' +
        f'</div>' +
        f'<div class="high-inline">{high_chips}</div>'
    )
    return row



# ── 섹터 ETF 바 ───────────────────────────

def render_etf_strip(sector_etf):
    items = sorted(sector_etf.items(), key=lambda x: x[1]["change_pct"], reverse=True)
    max_abs = max(abs(v["change_pct"]) for _, v in items) if items else 1
    html = ""
    for sym, d in items:
        cc    = chg_cls(d["change_pct"])
        bar_w = int(abs(d["change_pct"]) / max_abs * 100)
        fill  = "#EF4444" if d["change_pct"] >= 0 else "#3B82F6"
        html += f"""
        <div class="etf-row">
          <div class="etf-nm">{d['name']}</div>
          <div class="etf-bar-wrap"><div class="etf-bar" style="width:{bar_w}%;background:{fill}"></div></div>
          <div class="etf-chg {cc}">{chg_sign(d['change_pct'])}</div>
        </div>"""
    return html


# ── 크로스 시그널 ─────────────────────────

def render_cross(cross):
    if not cross:
        return "<p style='color:#9CA3AF;padding:16px'>당일 크로스 시그널 없음</p>"
    chips = ""
    for r in cross[:20]:
        pc    = chg_cls(r.get("change_pct",0))
        color = sec_color(r.get("sector","Unknown"))
        chips += f"""
        <div class="bx-row">
          <span class="bx-nm">{r['ticker']}</span>
          <span class="bx-sec" style="background:{color}">{r.get('sector','')[:12]}</span>
          <div class="bx-r">
            <span class="bx-pct {pc}">{chg_sign(r.get('change_pct',0))}</span>
            <span class="bx-vol">{fmt_amount(r.get('amount',0))}</span>
          </div>
        </div>"""
    return f'<div class="cross-desc">S&amp;P 500 <em>AND</em> Nasdaq 200 동시 52주 신고가 — {len(cross)}종목</div><div class="bx">{chips}</div>'


# ── CSS ───────────────────────────────────

CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'SF Pro Text','Helvetica Neue',sans-serif;
     background:#fff;color:#1C1C1E;font-size:13px;line-height:1.5}
.page{max-width:960px;margin:0 auto;padding:24px 20px 80px}

/* Header */
.hd-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px}
.hd-title{font-size:22px;font-weight:700;letter-spacing:-.5px}
.hd-sub{font-size:11px;color:#8E8E93;margin-top:3px}
.mkt-tabs{display:flex;gap:6px;flex-wrap:wrap}
.mkt-tab{padding:6px 18px;border-radius:20px;font-size:11px;font-weight:700;
          border:1.5px solid #D1D5DB;color:#6B7280;cursor:pointer;transition:.15s;background:#fff}
.mkt-tab.active{background:#1C1C1E;color:#fff;border-color:#1C1C1E}

/* KPI */
.kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px}
.kpi{background:#F9FAFB;border-radius:12px;padding:14px 16px}
.kpi-lbl{font-size:10px;color:#8E8E93;font-weight:500;margin-bottom:5px}
.kpi-val{font-size:22px;font-weight:700;letter-spacing:-.5px}
.kpi-val.up,.kpi-sub.up{color:#EF4444}
.kpi-val.dn,.kpi-sub.dn{color:#3B82F6}
.kpi-val.blue{color:#3B82F6}
.kpi-sub{font-size:10px;margin-top:3px}

/* Section */
.sec{margin-top:26px}
.sec-title{font-size:13px;font-weight:700;color:#1C1C1E;margin-bottom:12px;
            padding-left:10px;border-left:3px solid #3B82F6}

/* Tab */
.tab{display:none}.tab.active{display:block}

/* Sector bar */
.sb-block{margin-bottom:14px;padding-bottom:12px;border-bottom:1px solid #F3F4F6}
.sb-block:last-child{border-bottom:none;margin-bottom:0}
.sb-hd{display:flex;justify-content:space-between;align-items:center;margin-bottom:7px}
.sb-left{display:flex;align-items:center;gap:6px}
.sb-ic{font-size:14px}
.sb-nm{font-size:12.5px;font-weight:700;color:#1C1C1E}
.sb-right{display:flex;align-items:center;gap:7px}
.sb-amt{font-size:13px;font-weight:700;color:#1C1C1E}
.sb-badge{font-size:10px;font-weight:600;color:#6B7280;background:#F3F4F6;padding:2px 8px;border-radius:20px}
.sb-badge.up{color:#EF4444;background:#EF444415}
.sb-badge.dn{color:#3B82F6;background:#3B82F615}
.sb-track{background:#F3F4F6;border-radius:4px;height:6px;overflow:hidden;margin-bottom:8px}
.sb-fill{height:100%;border-radius:4px}
.st-pills{display:flex;flex-wrap:wrap;gap:4px}
.st-pill{display:inline-flex;align-items:center;gap:4px;background:#fff;
          border:1px solid #E5E7EB;border-radius:8px;padding:3px 9px}
.st-name{font-size:11px;font-weight:500;color:#374151}
.st-sep{font-size:10px;color:#D1D5DB}
.st-amt{font-size:10px;color:#9CA3AF}
.st-pct{font-size:10.5px;font-weight:700}
.st-pct.up{color:#EF4444}.st-pct.dn{color:#3B82F6}.st-pct.neu{color:#9CA3AF}

/* Scorecard */
.sc-table{width:100%;border-collapse:collapse;font-size:11.5px}
.sc-table thead th{background:#F9FAFB;color:#6B7280;font-size:10px;font-weight:600;
                    padding:7px 10px;text-align:left;border-bottom:1px solid #E5E7EB}
.sc-table tbody tr:hover{background:#FAFAFA}
.sc-table td{padding:8px 10px;border-bottom:1px solid #F3F4F6;vertical-align:middle}
.sc-rk{font-weight:700;color:#3B82F6;width:24px}
.sc-sc{font-weight:600;white-space:nowrap}
.sc-am{color:#374151}
.sc-br{display:flex;align-items:center;gap:6px;min-width:110px}
.sc-track{flex:1;background:#F3F4F6;border-radius:3px;height:5px;overflow:hidden}
.sc-fill{height:100%;border-radius:3px}
.sc-val{font-size:10px;color:#6B7280;width:22px;text-align:right}
.sc-sh{color:#9CA3AF;font-size:10.5px}
.sc-ch{font-size:10.5px;font-weight:600}
.sc-ch.up{color:#EF4444}.sc-ch.dn{color:#3B82F6}.sc-ch.neu{color:#9CA3AF}

/* 4 boxes */
.box-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.bx{background:#fff;border:1px solid #E5E7EB;border-radius:12px;padding:14px 16px}
.bx-hd{font-size:11px;font-weight:700;color:#374151;margin-bottom:10px;display:flex;align-items:center;gap:5px}
.bx-row{display:grid;grid-template-columns:1fr auto auto;align-items:center;
         gap:6px;padding:5px 0;border-bottom:1px solid #F9FAFB}
.bx-row:last-child{border-bottom:none}
.bx-nm{font-size:12px;font-weight:600;color:#1C1C1E;font-family:monospace}
.bx-sec{font-size:9px;font-weight:600;color:#fff;padding:2px 6px;border-radius:4px;white-space:nowrap}
.bx-r{display:flex;align-items:center;gap:5px}
.bx-pct{font-size:11.5px;font-weight:700}
.bx-pct.up{color:#EF4444}.bx-pct.dn{color:#3B82F6}.bx-pct.neu{color:#9CA3AF}
.bx-vol{font-size:9.5px;color:#9CA3AF}

/* Highs */
.hl-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.hl-sec{background:#F9FAFB;border-radius:10px;padding:12px}
.hl-sec-hd{display:flex;justify-content:space-between;align-items:center;
             margin-bottom:8px;padding-left:6px}
.hl-sec-nm{font-size:11.5px;font-weight:700;color:#1C1C1E}
.hl-sec-cnt{font-size:10px;color:#9CA3AF}
.hl-chips{display:flex;flex-wrap:wrap;gap:4px}
.hl-chip{display:inline-flex;align-items:center;gap:5px;background:#fff;
          border:1px solid #E5E7EB;border-radius:8px;padding:3px 8px}
.hl-nm{font-size:11px;font-weight:500;color:#374151;font-family:monospace}
.hl-pct{font-size:10.5px;font-weight:700}
.hl-pct.up{color:#EF4444}.hl-pct.dn{color:#3B82F6}

/* Regime */
.rg-tags{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px}
.rg-tag{font-size:11px;font-weight:600;padding:4px 12px;border-radius:20px}
.rg-txt{font-size:12px;color:#374151;line-height:1.7;background:#F9FAFB;
         border-radius:10px;padding:12px 14px}

/* Strategy */
.strat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.strat-card{background:#fff;border:1px solid #E5E7EB;border-radius:12px;padding:14px 16px}
.strat-hd{display:flex;align-items:center;gap:6px;margin-bottom:10px;flex-wrap:wrap}
.strat-lbl{font-size:12px;font-weight:700}
.strat-period{font-size:10px;color:#9CA3AF;background:#F3F4F6;padding:2px 8px;border-radius:20px}
.strat-stance{font-size:10.5px;color:#6B7280;font-weight:500}
.strat-pts{padding-left:14px;display:flex;flex-direction:column;gap:5px}
.strat-pts li{font-size:11.5px;color:#374151;line-height:1.5}
.strat-chips{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:8px}
.st-chip{font-size:10px;font-weight:600;color:#3B82F6;background:#3B82F615;
          border:1px solid #3B82F630;padding:2px 8px;border-radius:20px}

/* ETF strip */
.etf-grid{display:grid;grid-template-columns:1fr 1fr;gap:0 20px}
.etf-row{display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid #F9FAFB}
.etf-nm{width:180px;font-size:11.5px;color:#374151;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.etf-bar-wrap{flex:1;height:5px;background:#F3F4F6;border-radius:3px;overflow:hidden}
.etf-bar{height:100%;border-radius:3px}
.etf-chg{width:52px;font-size:11.5px;font-weight:600;text-align:right}
.etf-chg.up{color:#EF4444}.etf-chg.dn{color:#3B82F6}

/* Cross */
.cross-desc{font-size:12px;color:#374151;margin-bottom:12px;padding:10px 14px;
             background:#3B82F610;border-radius:10px;border:1px solid #3B82F630}
.cross-desc em{font-style:normal;font-weight:700;color:#3B82F6}

/* 신고가 인라인 */
.high-inline{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px;
             padding:12px 14px;background:#F9FAFB;border-radius:10px;
             border:1px solid #E5E7EB}

/* up/dn global - 한국식: 상승=빨강, 하락=파랑 */
.up{color:#EF4444}.dn{color:#3B82F6}.neu{color:#9CA3AF}

@media(max-width:700px){
  .kpi-row{grid-template-columns:1fr 1fr}
  .box-grid,.hl-grid,.strat-grid{grid-template-columns:1fr}
  .etf-grid{grid-template-columns:1fr}
  .etf-nm{width:130px}
}
"""

JS = """
function sw(tab, btn) {
  document.querySelectorAll('.mkt-tab').forEach(t => t.classList.remove('active'));
  btn.classList.add('active');
  ['sp500','nasdaq100','cross'].forEach(function(id) {
    document.getElementById('tab-' + id).classList.remove('active');
  });
  document.getElementById('tab-' + tab).classList.add('active');
}
"""


# ── HTML 조립 ─────────────────────────────

def generate_html(analyzed):
    date_str   = analyzed.get("date", str(datetime.date.today()))
    index      = analyzed.get("index", {})
    sector_etf = analyzed.get("sector_etf", {})
    sp500      = analyzed.get("sp500", {})
    nasdaq100  = analyzed.get("nasdaq100", {})
    cross      = analyzed.get("cross", [])

    def tab_content(u, tab_id, label):
        if not u:
            return f'<div class="tab" id="tab-{tab_id}"><p style="color:#9CA3AF">데이터 없음</p></div>'
        active = "active" if tab_id == "sp500" else ""
        return f"""
        <div class="tab {active}" id="tab-{tab_id}">
          {render_kpi_row(u, label)}

          <div class="sec">
            <div class="sec-title">섹터 자금흐름 — {label}</div>
            {render_sector_flow(u.get('sector_flow',[]), u.get('top_amount',[]))}
          </div>

          <div class="sec">
            <div class="sec-title">섹터 강도 스코어카드 — {label}</div>
            {render_scorecard(u.get('sector_flow',[]))}
          </div>

          <div class="sec">
            <div class="sec-title">주요 종목 현황 — {label}</div>
            {render_4boxes(u)}
          </div>

          <div class="sec">
            <div class="sec-title">52주 신고가 종목 — {label}</div>
            {render_highs_by_sector(u.get('highs',[]))}
          </div>

          <div class="sec">
            <div class="sec-title">시장 레짐 신호 — {label}</div>
            {render_regime(u, label)}
          </div>

          <div class="sec">
            <div class="sec-title">시간 지평별 전략 — {label}</div>
            {render_strategy(u, label)}
          </div>
        </div>"""

    cross_active = ""
    cross_tab = f"""
    <div class="tab" id="tab-cross">
      <div class="sec">
        <div class="sec-title">⚡ 크로스 시그널 — S&amp;P500 ∩ Nasdaq200 동시 신고가</div>
        {render_cross(cross)}
      </div>
    </div>"""

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{date_str} US Market Daily Report</title>
<style>{CSS}</style>
</head>
<body>
<div class="page">

  <div class="hd-top">
    <div>
      <div class="hd-title">🇺🇸 US Market Daily Report</div>
      <div class="hd-sub">{date_str} · EST Close 기준</div>
    </div>
    <div class="mkt-tabs">
      <button class="mkt-tab active" onclick="sw('sp500',this)">S&amp;P 500</button>
      <button class="mkt-tab" onclick="sw('nasdaq100',this)">Nasdaq 200</button>
      <button class="mkt-tab" onclick="sw('cross',this)">⚡ 크로스</button>
    </div>
  </div>

  <!-- 지수 카드 -->
  <div class="kpi-row">
    {render_index_cards(index)}
  </div>

  <!-- 섹터 ETF -->
  <div class="sec">
    <div class="sec-title">섹터 ETF 등락</div>
    <div class="etf-grid">
      {render_etf_strip(sector_etf)}
    </div>
  </div>

  {tab_content(sp500,    'sp500',    'S&P 500')}
  {tab_content(nasdaq100,'nasdaq100','Nasdaq 200')}
  {cross_tab}

</div>
<script>{JS}</script>
</body>
</html>"""


def build_report(analyzed):
    date_str = analyzed.get("date", str(datetime.date.today()))
    html = generate_html(analyzed)

    out_path = DOCS_DIR / f"report_{date_str}.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ 리포트 생성: {out_path}")
    return str(out_path)


if __name__ == "__main__":
    from pathlib import Path
    import json
    from us_market.analyzer import analyze

    latest = Path(__file__).parent.parent / "data" / "market_latest.json"
    with open(latest) as f:
        raw = json.load(f)
    analyzed = analyze(raw)
    build_report(analyzed)
