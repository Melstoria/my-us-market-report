# my-us-market-report

S&P 500 + Nasdaq 100 일간 시장 리포트 자동 생성기

## 구조

```
my-us-market-report/
├── .github/workflows/daily-report.yml   # GitHub Actions (매일 06:30 KST)
├── us_market/
│   ├── collector.py   # yfinance 데이터 수집
│   ├── analyzer.py    # 신고가·거래대금·모멘텀 분석
│   └── reporter.py    # HTML 리포트 생성
├── data/
│   ├── market_latest.json        # 최신 원시 데이터
│   ├── market_YYYY-MM-DD.json    # 일별 원시 데이터
│   └── sector_cache.json         # 섹터 정보 캐시
├── docs/
│   ├── index.html                # GitHub Pages (최신)
│   └── report_YYYY-MM-DD.html   # 일별 리포트
├── run_local.py      # 로컬 수동 실행
└── requirements.txt
```

## GitHub Pages 설정

Settings → Pages → Source: `Deploy from a branch` → Branch: `main` / `docs`

## 수집 데이터

- **지수**: SPY, QQQ, DIA, IWM, VIX
- **섹터 ETF**: XLK, XLF, XLE, XLV, XLY, XLP, XLI, XLB, XLRE, XLU, XLC
- **S&P 500**: ~503종목 (Wikipedia 파싱)
- **Nasdaq 100**: 100종목 (Wikipedia 파싱)

## 리포트 구성

| 탭 | 내용 |
|----|------|
| S&P 500 | 섹터 자금흐름 / 거래대금 Top30 / 52주 신고가 / 모멘텀 / 등락률 Top10 |
| Nasdaq 100 | 동일 |
| ⚡ 크로스 시그널 | 두 지수 동시 신고가 돌파 — 최강 모멘텀 |

## 로컬 실행

```bash
pip install -r requirements.txt
python run_local.py
```
