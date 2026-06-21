"""
run_local.py
로컬 수동 실행용 (테스트·긴급 업데이트)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from us_market.collector import collect_all
from us_market.analyzer  import analyze
from us_market.reporter  import build_report


def main():
    print("🇺🇸 US Market Report — 로컬 실행")
    raw      = collect_all()
    analyzed = analyze(raw)
    path     = build_report(analyzed)
    print(f"\n✅ 완료! 브라우저에서 열기:\n   {path}")


if __name__ == "__main__":
    main()
