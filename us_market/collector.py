"""
collector.py
S&P 500 + Nasdaq 100 일별 데이터 수집 (yfinance 기반)
"""

import json
import time
import datetime
import requests
import yfinance as yf
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


# ──────────────────────────────────────────
# 1. 유니버스 수집
# ──────────────────────────────────────────

def get_sp500_tickers() -> list[str]:
    """Wikipedia에서 S&P 500 티커 파싱"""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    df = tables[0]
    tickers = df["Symbol"].str.replace(".", "-", regex=False).tolist()
    return tickers


def get_nasdaq100_tickers() -> list[str]:
    """Wikipedia에서 Nasdaq 100 티커 파싱"""
    url = "https://en.wikipedia.org/wiki/Nasdaq-100"
    tables = pd.read_html(url)
    # Nasdaq-100 구성종목 테이블 찾기
    for t in tables:
        if "Ticker" in t.columns or "Symbol" in t.columns:
            col = "Ticker" if "Ticker" in t.columns else "Symbol"
            tickers = t[col].dropna().str.replace(".", "-", regex=False).tolist()
            if len(tickers) > 80:
                return tickers
    # fallback: QQQ holdings via ETF
    return _get_qqq_holdings()


def _get_qqq_holdings() -> list[str]:
    """QQQ 구성종목 fallback (iShares 공개 데이터)"""
    url = "https://www.ishares.com/us/products/239726/ISHARES-NASDAQ-100-ETF/1467271812596.ajax?fileType=json&fileName=IVV_holdings&dataType=fund"
    # 실패 시 하드코딩 Top 100 사용
    fallback = [
        "MSFT","AAPL","NVDA","AMZN","META","TSLA","GOOGL","GOOG","AVGO","COST",
        "NFLX","AMD","ASML","CSCO","ADP","TMUS","INTC","INTU","CMCSA","BKNG",
        "AMGN","ISRG","VRTX","REGN","PEP","MU","PANW","SNPS","KLAC","MELI",
        "ADI","LRCX","CDNS","GILD","ABNB","CRWD","MDLZ","CEG","FTNT","KDP",
        "MAR","MRVL","ORLY","PYPL","CSGP","MNST","CHTR","NXPI","PCAR","WDAY",
        "DXCM","CPRT","ADSK","FANG","ROST","IDXX","TEAM","ODFL","KHC","VRSK",
        "EXC","XEL","FAST","GEHC","CTSH","BIIB","ZS","SGEN","GFS","DLTR",
        "ANSS","TTWO","DDOG","ZM","ILMN","MTCH","WBA","LCID","RIVN","ENPH",
        "ALGN","ON","SPLK","SIRI","PAYX","EA","MCHP","JD","PDD","BIDU",
        "EBAY","AMAT","MDB","OKTA","DOCU","NET","SNOW","PLTR","RBLX","COIN",
    ]
    return fallback[:100]


# ──────────────────────────────────────────
# 2. 시장 데이터 수집
# ──────────────────────────────────────────

def fetch_index_data() -> dict:
    """주요 지수 ETF 데이터"""
    indices = {
        "SPY":  "S&P 500",
        "QQQ":  "Nasdaq 100",
        "DIA":  "Dow Jones",
        "IWM":  "Russell 2000",
        "VIX":  "VIX (공포지수)",
    }
    result = {}
    tickers = yf.download(
        list(indices.keys()),
        period="5d",
        interval="1d",
        progress=False,
        auto_adjust=True,
    )
    close = tickers["Close"]
    volume = tickers.get("Volume", pd.DataFrame())

    for sym, name in indices.items():
        try:
            prices = close[sym].dropna()
            if len(prices) < 2:
                continue
            today_price = float(prices.iloc[-1])
            prev_price  = float(prices.iloc[-2])
            chg_pct = (today_price - prev_price) / prev_price * 100
            result[sym] = {
                "name":       name,
                "price":      round(today_price, 2),
                "change_pct": round(chg_pct, 2),
                "volume":     int(volume[sym].iloc[-1]) if sym in volume.columns and not volume.empty else 0,
            }
        except Exception:
            continue
    return result


def fetch_universe_data(tickers: list[str], batch_size: int = 50) -> pd.DataFrame:
    """
    종목 리스트 전체 데이터 수집
    - 배치 처리로 rate limit 회피
    - 반환: DataFrame(ticker, close, prev_close, change_pct, volume, amount, 52w_high, sector)
    """
    all_data = []
    valid_tickers = [t for t in tickers if isinstance(t, str) and t.strip()]

    for i in range(0, len(valid_tickers), batch_size):
        batch = valid_tickers[i:i+batch_size]
        print(f"  배치 수집 중: {i+1}~{i+len(batch)} / {len(valid_tickers)}")
        try:
            raw = yf.download(
                batch,
                period="60d",        # 52주 고가 계산용 + 당일 데이터
                interval="1d",
                progress=False,
                auto_adjust=True,
                group_by="ticker",
            )
            for ticker in batch:
                try:
                    if len(batch) == 1:
                        df_t = raw
                    else:
                        df_t = raw[ticker]

                    df_t = df_t.dropna(subset=["Close"])
                    if len(df_t) < 2:
                        continue

                    close_today = float(df_t["Close"].iloc[-1])
                    close_prev  = float(df_t["Close"].iloc[-2])
                    high_52w    = float(df_t["High"].max())
                    vol_today   = float(df_t["Volume"].iloc[-1])
                    amount      = close_today * vol_today          # 거래대금 (USD)

                    chg_pct     = (close_today - close_prev) / close_prev * 100
                    is_52w_high = close_today >= high_52w * 0.995  # 0.5% 이내 허용

                    all_data.append({
                        "ticker":      ticker,
                        "close":       round(close_today, 2),
                        "prev_close":  round(close_prev, 2),
                        "change_pct":  round(chg_pct, 2),
                        "volume":      int(vol_today),
                        "amount":      amount,
                        "high_52w":    round(high_52w, 2),
                        "is_52w_high": is_52w_high,
                    })
                except Exception:
                    continue
        except Exception as e:
            print(f"  배치 오류: {e}")
        time.sleep(1)  # rate limit 방지

    return pd.DataFrame(all_data)


def enrich_sector(df: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    """
    yfinance info에서 섹터 정보 추가
    - 느리므로 샘플링 or 캐시 활용
    """
    sector_map = {}
    cache_path = DATA_DIR / "sector_cache.json"

    # 캐시 로드
    if cache_path.exists():
        with open(cache_path) as f:
            sector_map = json.load(f)

    # 캐시에 없는 종목만 조회
    missing = [t for t in tickers if t not in sector_map]
    print(f"  섹터 조회: {len(missing)}개 (캐시 {len(sector_map)}개 활용)")

    for i, ticker in enumerate(missing):
        try:
            info = yf.Ticker(ticker).info
            sector_map[ticker] = info.get("sector", "Unknown")
            if i % 20 == 0 and i > 0:
                time.sleep(1)
        except Exception:
            sector_map[ticker] = "Unknown"

    # 캐시 저장
    with open(cache_path, "w") as f:
        json.dump(sector_map, f)

    df["sector"] = df["ticker"].map(sector_map).fillna("Unknown")
    return df


# ──────────────────────────────────────────
# 3. 섹터 ETF 데이터
# ──────────────────────────────────────────

SECTOR_ETFS = {
    "XLK":  "Technology",
    "XLF":  "Financials",
    "XLE":  "Energy",
    "XLV":  "Healthcare",
    "XLY":  "Consumer Discretionary",
    "XLP":  "Consumer Staples",
    "XLI":  "Industrials",
    "XLB":  "Materials",
    "XLRE": "Real Estate",
    "XLU":  "Utilities",
    "XLC":  "Communication Services",
}

def fetch_sector_etf_data() -> dict:
    """섹터 ETF 등락률"""
    result = {}
    raw = yf.download(
        list(SECTOR_ETFS.keys()),
        period="5d",
        interval="1d",
        progress=False,
        auto_adjust=True,
    )
    close = raw["Close"]
    for sym, name in SECTOR_ETFS.items():
        try:
            prices = close[sym].dropna()
            today = float(prices.iloc[-1])
            prev  = float(prices.iloc[-2])
            result[sym] = {
                "name":       name,
                "change_pct": round((today - prev) / prev * 100, 2),
            }
        except Exception:
            continue
    return result


# ──────────────────────────────────────────
# 4. 메인 수집 함수
# ──────────────────────────────────────────

def collect_all() -> dict:
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    print(f"\n{'='*50}")
    print(f"US Market Data Collection: {today_str}")
    print(f"{'='*50}")

    print("\n[1/5] 지수 데이터 수집...")
    index_data = fetch_index_data()

    print("\n[2/5] 섹터 ETF 데이터 수집...")
    sector_etf_data = fetch_sector_etf_data()

    print("\n[3/5] S&P 500 유니버스 수집...")
    sp500_tickers = get_sp500_tickers()
    sp500_df = fetch_universe_data(sp500_tickers)

    print("\n[4/5] Nasdaq 100 유니버스 수집...")
    ndx100_tickers = get_nasdaq100_tickers()
    ndx100_df = fetch_universe_data(ndx100_tickers)

    print("\n[5/5] 섹터 정보 보강...")
    all_tickers = list(set(sp500_tickers + ndx100_tickers))
    sp500_df  = enrich_sector(sp500_df,  sp500_tickers)
    ndx100_df = enrich_sector(ndx100_df, ndx100_tickers)

    # 저장
    output = {
        "date":         today_str,
        "index":        index_data,
        "sector_etf":   sector_etf_data,
        "sp500":        sp500_df.to_dict(orient="records"),
        "nasdaq100":    ndx100_df.to_dict(orient="records"),
    }

    out_path = DATA_DIR / f"market_{today_str}.json"
    with open(out_path, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 최신 파일 심볼릭 복사
    latest_path = DATA_DIR / "market_latest.json"
    with open(latest_path, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 저장 완료: {out_path}")
    print(f"   S&P500: {len(sp500_df)}개 / Nasdaq100: {len(ndx100_df)}개")
    return output


if __name__ == "__main__":
    collect_all()
