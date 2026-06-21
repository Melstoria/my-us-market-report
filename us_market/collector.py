"""
collector.py
S&P 500 + Nasdaq 100 일별 데이터 수집 (yfinance 기반)
"""

import json
import time
import datetime
import yfinance as yf
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


# ──────────────────────────────────────────
# 1. 유니버스 (하드코딩 — Wikipedia IP 차단 우회)
# ──────────────────────────────────────────

def get_sp500_tickers() -> list:
    return [
        "AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","BRK-B","TSLA","AVGO",
        "JPM","LLY","UNH","XOM","V","MA","COST","HD","PG","JNJ",
        "ABBV","BAC","NFLX","CRM","WMT","CVX","MRK","KO","PEP","ORCL",
        "AMD","ACN","TMO","LIN","MCD","CSCO","ABT","DHR","TXN","NEE",
        "PM","ISRG","IBM","GE","INTU","AMGN","CAT","SPGI","NOW","QCOM",
        "RTX","GS","HON","UNP","BKNG","SYK","VRTX","T","AMAT","LOW",
        "PFE","BLK","AXP","SCHW","C","UBER","DE","ETN","ADI","TJX",
        "REGN","PANW","LRCX","PLD","MU","BA","MMC","SBUX","CB","SO",
        "MDLZ","ADP","CI","SHW","DUK","CME","FI","KLAC","BMY","BSX",
        "WM","SNPS","CDNS","ZTS","MCK","ICE","EOG","ITW","GILD","CMG",
        "CVS","NOC","USB","APH","GD","MPC","HCA","MCO","EMR","MAR",
        "TGT","PSA","PH","ORLY","AON","WELL","HLT","INTC","MSI","CEG",
        "FCX","CL","CTAS","PCAR","ECL","COF","TDG","OKE","ELV","NSC",
        "CARR","JCI","AIG","WMB","FDX","NKE","PYPL","VLO","NXPI","CHTR",
        "ROP","FICO","MRVL","MNST","FTNT","WDAY","SLB","GM","F","O",
        "RSG","PAYX","HES","KHC","A","ODFL","CPRT","FAST","AEP","EXC",
        "DXCM","IDXX","KMB","MRNA","VRSK","BIIB","PPG","PSX","GEHC","XEL",
        "GWW","AME","DHI","NUE","EW","ADSK","ACGL","MTD","OTIS","AWK",
        "CTSH","BKR","ANSS","ON","DD","IRM","FANG","ROK","DLTR","ZBH",
        "MKC","LH","WAB","EBAY","KEYS","TTWO","ENPH","ALB","WBA","MTCH",
        "EA","MDB","NET","SNOW","PLTR","RBLX","COIN","DDOG","ZS","CRWD",
        "TEAM","ABNB","GFS","SMCI","HOOD","ARM","DASH","TTD","OKTA","DOCU",
    ]


def get_nasdaq100_tickers() -> list:
    return [
        "MSFT","AAPL","NVDA","AMZN","META","TSLA","GOOGL","GOOG","AVGO","COST",
        "NFLX","AMD","ASML","CSCO","ADP","TMUS","INTU","CMCSA","BKNG","AMGN",
        "ISRG","VRTX","REGN","PEP","MU","PANW","SNPS","KLAC","MELI","ADI",
        "LRCX","CDNS","GILD","ABNB","CRWD","MDLZ","CEG","FTNT","KDP","MAR",
        "MRVL","ORLY","PYPL","CSGP","MNST","CHTR","NXPI","PCAR","WDAY","DXCM",
        "CPRT","ADSK","FANG","ROST","IDXX","TEAM","ODFL","KHC","VRSK","EXC",
        "XEL","FAST","GEHC","CTSH","BIIB","ZS","DLTR","ANSS","TTWO","DDOG",
        "ILMN","MTCH","WBA","ENPH","ALGN","ON","SIRI","PAYX","EA","MCHP",
        "EBAY","AMAT","MDB","OKTA","DOCU","NET","SNOW","PLTR","RBLX","COIN",
        "GFS","SMCI","HOOD","ARM","DASH","TTD","LULU","RIVN","ZM","PDD",
    ]


# ──────────────────────────────────────────
# 2. 시장 데이터 수집
# ──────────────────────────────────────────

def fetch_index_data() -> dict:
    """주요 지수 ETF 데이터 (VIX는 ^VIX)"""
    etf_syms = ["SPY", "QQQ", "DIA", "IWM"]
    etf_names = {"SPY": "S&P 500", "QQQ": "Nasdaq 100", "DIA": "Dow Jones", "IWM": "Russell 2000"}
    result = {}

    raw = yf.download(etf_syms, period="5d", interval="1d", progress=False, auto_adjust=True)
    close = raw["Close"]
    for sym in etf_syms:
        try:
            prices = close[sym].dropna()
            if len(prices) < 2:
                continue
            today = float(prices.iloc[-1])
            prev  = float(prices.iloc[-2])
            result[sym] = {
                "name":       etf_names[sym],
                "price":      round(today, 2),
                "change_pct": round((today - prev) / prev * 100, 2),
                "volume":     0,
            }
        except Exception:
            continue

    # VIX 별도 처리
    try:
        vix = yf.download("^VIX", period="5d", interval="1d", progress=False, auto_adjust=True)
        vix_close = vix["Close"].dropna()
        if len(vix_close) >= 2:
            today = float(vix_close.iloc[-1])
            prev  = float(vix_close.iloc[-2])
            result["VIX"] = {
                "name":       "VIX (공포지수)",
                "price":      round(today, 2),
                "change_pct": round((today - prev) / prev * 100, 2),
                "volume":     0,
            }
    except Exception:
        pass

    return result


def fetch_universe_data(tickers: list, batch_size: int = 50) -> pd.DataFrame:
    all_data = []
    valid_tickers = [t for t in tickers if isinstance(t, str) and t.strip()]

    for i in range(0, len(valid_tickers), batch_size):
        batch = valid_tickers[i:i+batch_size]
        print(f"  배치 수집 중: {i+1}~{i+len(batch)} / {len(valid_tickers)}")
        try:
            raw = yf.download(
                batch, period="1y", interval="1d",
                progress=False, auto_adjust=True, group_by="ticker",
            )
            for ticker in batch:
                try:
                    df_t = raw if len(batch) == 1 else raw[ticker]
                    df_t = df_t.dropna(subset=["Close"])
                    if len(df_t) < 2:
                        continue
                    close_today = float(df_t["Close"].iloc[-1])
                    close_prev  = float(df_t["Close"].iloc[-2])
                    high_52w    = float(df_t["High"].max())
                    vol_today   = float(df_t["Volume"].iloc[-1])
                    amount      = close_today * vol_today
                    chg_pct     = (close_today - close_prev) / close_prev * 100
                    is_52w_high = close_today >= high_52w * 0.995

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
        time.sleep(1)

    return pd.DataFrame(all_data)


def enrich_sector(df: pd.DataFrame, tickers: list) -> pd.DataFrame:
    sector_map = {}
    cache_path = DATA_DIR / "sector_cache.json"

    if cache_path.exists():
        with open(cache_path) as f:
            sector_map = json.load(f)

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

    with open(cache_path, "w") as f:
        json.dump(sector_map, f)

    df["sector"] = df["ticker"].map(sector_map).fillna("Unknown")
    return df


# ──────────────────────────────────────────
# 3. 섹터 ETF
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
    result = {}
    raw = yf.download(list(SECTOR_ETFS.keys()), period="5d", interval="1d", progress=False, auto_adjust=True)
    close = raw["Close"]
    for sym, name in SECTOR_ETFS.items():
        try:
            prices = close[sym].dropna()
            today = float(prices.iloc[-1])
            prev  = float(prices.iloc[-2])
            result[sym] = {"name": name, "change_pct": round((today - prev) / prev * 100, 2)}
        except Exception:
            continue
    return result


# ──────────────────────────────────────────
# 4. 메인
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
    sp500_df  = enrich_sector(sp500_df,  sp500_tickers)
    ndx100_df = enrich_sector(ndx100_df, ndx100_tickers)

    output = {
        "date":       today_str,
        "index":      index_data,
        "sector_etf": sector_etf_data,
        "sp500":      sp500_df.to_dict(orient="records"),
        "nasdaq100":  ndx100_df.to_dict(orient="records"),
    }

    out_path = DATA_DIR / f"market_{today_str}.json"
    with open(out_path, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    latest_path = DATA_DIR / "market_latest.json"
    with open(latest_path, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 저장 완료: {out_path}")
    print(f"   S&P500: {len(sp500_df)}개 / Nasdaq100: {len(ndx100_df)}개")
    return output


if __name__ == "__main__":
    collect_all()
