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
    """S&P 500 전체 티커 (501개 하드코딩)"""
    return [
        "MMM","AOS","ABT","ABBV","ACN","ADBE","AMD","AES","AFL","A","APD","ABNB","AKAM","ALB","ARE",
        "ALGN","ALLE","LNT","ALL","GOOGL","GOOG","MO","AMZN","AMCR","AEE","AAL","AEP","AXP","AIG",
        "AMT","AWK","AMP","AME","AMGN","APH","ADI","ANSS","AON","APA","AAPL","AMAT","APTV","ACGL",
        "ADM","ANET","AJG","AIZ","T","ATO","ADSK","ADP","AZO","AVB","AVY","AXON","BKR","BALL","BAC",
        "BK","BBWI","BAX","BDX","BRK-B","BBY","BIO","TECH","BIIB","BLK","BX","BA","BCO","BSX","BMY",
        "AVGO","BR","BRO","BF-B","BLDR","BG","CDNS","CZR","CPT","CPB","COF","CAH","KMX","CCL","CARR",
        "CTLT","CAT","CBOE","CBRE","CDW","CE","COR","CNC","CNX","CDAY","CF","CRL","SCHW","CHTR","CVX",
        "CMG","CB","CHD","CI","CINF","CTAS","CSCO","C","CFG","CLX","CME","CMS","KO","CTSH","CL","CMCSA",
        "CMA","CAG","COP","ED","STZ","CEG","COO","CPRT","GLW","CPAY","CTVA","CSGP","COST","CTRA","CCI",
        "CSX","CMI","CVS","DHI","DHR","DRI","DVA","DAY","DECK","DE","DAL","DVN","DXCM","FANG","DLR",
        "DFS","DG","DLTR","D","DPZ","DOV","DOW","DTE","DUK","DD","EMN","ETN","EBAY","ECL","EIX",
        "EW","EA","ELV","EMR","ENPH","ETR","EOG","EPAM","EQT","EFX","EQIX","EQR","ESS","EL","ETSY",
        "EG","ES","EXC","EXPE","EXPD","EXR","XOM","FFIV","FDS","FICO","FAST","FRT","FDX","FIS",
        "FITB","FSLR","FE","FI","FMC","F","FTNT","FTV","FOXA","FOX","BEN","FCX","GRMN","IT","GE","GEHC",
        "GEN","GNRC","GD","GIS","GM","GPC","GILD","GPN","GL","GDDY","GS","HAL","HIG","HAS","HCA","DOC",
        "HSIC","HSY","HES","HPE","HLT","HOLX","HD","HON","HRL","HST","HWM","HPQ","HUBB","HUM","HBAN",
        "HII","IBM","IEX","IDXX","ITW","INCY","IR","PODD","INTC","ICE","IFF","IP","IPG","INTU","ISRG",
        "IVZ","INVH","IQV","IRM","JBHT","JBL","JKHY","J","JNJ","JCI","JPM","JNPR","K","KVUE","KDP",
        "KEY","KEYS","KMB","KIM","KMI","KLAC","KHC","KR","LHX","LH","LRCX","LW","LVS","LDOS","LEN",
        "LLY","LIN","LYV","LKQ","LMT","L","LOW","LULU","LYB","MTB","MRO","MPC","MKTX","MAR","MMC",
        "MLM","MAS","MA","MTCH","MKC","MCD","MCK","MDT","MET","META","MTD","MGM","MCHP","MU","MSFT",
        "MAA","MRNA","MHK","MOH","TAP","MDLZ","MPWR","MNST","MCO","MS","MOS","MSI","MSCI","NDAQ",
        "NTAP","NFLX","NWL","NEM","NWSA","NWS","NEE","NKE","NI","NDSN","NSC","NTRS","NOC","NCLH",
        "NRG","NUE","NVDA","NVR","NXPI","ORLY","OXY","ODFL","OMC","ON","OKE","ORCL","OTIS","PCAR",
        "PKG","PANW","PH","PAYX","PAYC","PYPL","PNR","PEP","PFE","PCG","PM","PSX","PNW","PNC",
        "POOL","PPG","PPL","PFG","PG","PGR","PRU","PEG","PTC","PSA","PHM","QRVO","PWR","QCOM","DGX",
        "RL","RJF","RTX","O","REG","REGN","RF","RSG","RMD","RVTY","ROK","ROL","ROP","ROST","RCL",
        "SPGI","CRM","SBAC","SLB","STX","SEE","SRE","NOW","SHW","SPG","SWKS","SJM","SW","SNA","SOLV",
        "SO","LUV","SWK","SBUX","STT","STLD","STE","SYK","SMCI","SYF","SNPS","SYY","TMUS","TROW",
        "TTWO","TPR","TRGP","TGT","TEL","TDY","TFX","TER","TSLA","TXN","TXT","TMO","TJX","TSCO",
        "TT","TDG","TRV","TRMB","TFC","TYL","TSN","USB","UBER","UDR","ULTA","UNP","UAL","UPS","URI",
        "UNH","UHS","VLO","VTR","VLTO","VRSN","VRSK","VZ","VRTX","VTRS","VICI","V","VST","VMC",
        "WRB","GWW","WAB","WBA","WMT","DIS","WBD","WM","WAT","WEC","WFC","WELL","WST","WDC","WY",
        "WHR","WMB","WTW","WYNN","XEL","XYL","YUM","ZBRA","ZBH","ZTS",
    ]


def get_nasdaq100_tickers() -> list:
    """Nasdaq 200 티커 — Nasdaq100 + 나스닥 상장 중형 기술/바이오/성장주 100개"""
    return [
        # ── Nasdaq 100 ──
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
        # ── 추가 나스닥 중형 기술주 ──
        "AFRM","GTLB","HUBS","MNDY","CFLT","DKNG","IONQ","RGTI","QUBT","ACHR",
        "JOBY","RXRX","SOUN","ASTS","VKTX","ARDX","ARWR","BHVN","CELH","CHPT",
        "CLSK","CLOV","COIN","CRSP","CYTK","DMTK","EDIT","EGIO","ETON","EXAI",
        "FATE","FCEL","FLNC","FORM","FROG","GENI","GEVO","GLBE","GLPG","GOSS",
        "GOVX","GRBK","GRPN","GTLB","HIMS","HOLX","HOLO","HROW","IMVT","INFA",
        "INST","IONQ","IOVA","IRON","ITRI","KIND","KROS","KVYO","LAZR","LMND",
        "LPLA","LPSN","LUNG","MAPS","MARA","MBLY","MDXG","MIRM","MKSI","MLNK",
        "MNKD","MODN","MRUS","MSTR","NARI","NCNO","NKLA","NOVA","NRDS","NTLA",
        "NVAX","NVCR","NVTS","NWTN","OABI","OPEN","OPRA","OSCR","PACB","PATH",
        "PAYO","PCVX","PDCO","PHAT","PINC","PNTG","POWI","PRCT","PRGS","PRTA",
    ]

# ──────────────────────────────────────────
# 2. 시장 데이터 수집
# ──────────────────────────────────────────

def fetch_index_data() -> dict:
    """실제 지수 데이터 — ticker.history() 방식"""
    index_map = {
        "^GSPC": {"key": "SPY",  "name": "S&P 500"},
        "^NDX":  {"key": "QQQ",  "name": "Nasdaq 100"},
        "^DJI":  {"key": "DIA",  "name": "Dow Jones"},
        "^RUT":  {"key": "IWM",  "name": "Russell 2000"},
        "^VIX":  {"key": "VIX",  "name": "VIX (공포지수)"},
    }
    result = {}

    for sym, meta in index_map.items():
        try:
            hist = yf.Ticker(sym).history(period="5d", interval="1d", auto_adjust=True)
            hist = hist.dropna(subset=["Close"])
            if len(hist) < 2:
                continue
            today = float(hist["Close"].iloc[-1])
            prev  = float(hist["Close"].iloc[-2])
            result[meta["key"]] = {
                "name":       meta["name"],
                "price":      round(today, 2),
                "change_pct": round((today - prev) / prev * 100, 2),
                "volume":     0,
            }
        except Exception:
            continue

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
