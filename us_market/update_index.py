"""
update_index.py — 아카이브 목록 페이지
"""
import datetime
from pathlib import Path

DOCS_DIR = Path(__file__).parent.parent / "docs"


def build_index():
    def get_files(subdir):
        d = DOCS_DIR / subdir
        return sorted(d.glob("*.html"), reverse=True) if d.exists() else []

    def file_rows(files, prefix):
        if not files:
            return '<p class="empty">리포트 없음</p>'
        rows = ""
        for f in files[:30]:
            date_str = f.stem
            try:
                d     = datetime.date.fromisoformat(date_str)
                label = d.strftime("%Y.%m.%d 일간 리포트")
            except:
                label = date_str
            rows += f'<a class="report-row" href="{prefix}/{f.name}">📊 {label}</a>\n'
        return rows

    def period_rows(files, prefix, fmt):
        if not files:
            return '<p class="empty">리포트 없음</p>'
        rows = ""
        for f in files[:10]:
            date_str = f.stem
            try:
                d = datetime.date.fromisoformat(date_str)
                label = d.strftime(fmt)
            except:
                label = date_str
            rows += f'<a class="report-row" href="{prefix}/{f.name}">📊 {label}</a>\n'
        return rows

    daily     = get_files("daily")
    biweekly  = get_files("biweekly")
    monthly   = get_files("monthly")
    quarterly = get_files("quarterly")

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M KST")

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>US Market Report Hub</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'SF Pro Text',sans-serif;
     background:#0d1117;color:#e6edf3;font-size:13px;line-height:1.5}}
.page{{max-width:800px;margin:0 auto;padding:32px 20px 80px}}
.hd{{margin-bottom:32px}}
.title{{font-size:22px;font-weight:700;letter-spacing:-.5px;margin-bottom:4px}}
.title span{{color:#EF4444}}
.sub{{font-size:11px;color:#8b949e}}
.sec-title{{font-size:11px;font-weight:700;color:#8b949e;margin:24px 0 10px;
            padding-left:8px;border-left:3px solid #3B82F6;
            text-transform:uppercase;letter-spacing:.5px}}
.report-list{{display:flex;flex-direction:column;gap:5px}}
.report-row{{display:block;padding:10px 14px;background:#161b22;
             border:1px solid #30363d;border-radius:10px;
             text-decoration:none;color:#e6edf3;font-size:12.5px;transition:.15s}}
.report-row:hover{{background:#1f2937;border-color:#3B82F6}}
.empty{{color:#6b7280;font-size:12px;padding:10px 0}}
.updated{{font-size:11px;color:#6b7280;margin-top:32px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-top:8px}}
@media(max-width:600px){{.grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="page">
  <div class="hd">
    <div class="title">🇺🇸 US Market <span>Report</span></div>
    <div class="sub">미국 증시 분석 리포트 · 매일 06:30 KST 업데이트</div>
  </div>

  <div class="sec-title">📅 일간 리포트</div>
  <div class="report-list">
    {file_rows(daily, 'daily')}
  </div>

  <div class="grid">
    <div>
      <div class="sec-title">📊 격주 리포트</div>
      <div class="report-list">
        {period_rows(biweekly, 'biweekly', '%Y.%m.%d 격주 리포트')}
      </div>
    </div>
    <div>
      <div class="sec-title">📆 월간 리포트</div>
      <div class="report-list">
        {period_rows(monthly, 'monthly', '%Y년 %m월 리포트')}
      </div>
    </div>
  </div>

  <div class="sec-title">🗓 분기 리포트</div>
  <div class="report-list">
    {period_rows(quarterly, 'quarterly', '%Y년 분기 리포트')}
  </div>

  <div class="updated">Updated: {now}</div>
</div>
</body>
</html>"""

    idx = DOCS_DIR / "index.html"
    with open(idx, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ 인덱스: {idx}")


if __name__ == "__main__":
    build_index()
