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
        for f in files:
            date_str = f.stem
            try:
                d     = datetime.date.fromisoformat(date_str)
                label = d.strftime("%Y년 %m월 %d일 (%a)")
            except:
                label = date_str
            rows += f'<a class="report-row" href="{prefix}/{f.name}">{label}</a>\n'
        return rows

    daily     = get_files("daily")
    biweekly  = get_files("biweekly")
    monthly   = get_files("monthly")
    quarterly = get_files("quarterly")

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>US Market Report Archive</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'SF Pro Text',sans-serif;
     background:#fff;color:#1C1C1E;font-size:13px;line-height:1.5}}
.page{{max-width:860px;margin:0 auto;padding:32px 20px 80px}}
.hd{{display:flex;justify-content:space-between;align-items:center;margin-bottom:32px}}
.title{{font-size:22px;font-weight:700;letter-spacing:-.5px}}
.title span{{color:#EF4444}}
.badge{{font-size:11px;color:#8E8E93;background:#F3F4F6;padding:4px 12px;border-radius:20px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}
.sec-title{{font-size:12px;font-weight:700;color:#6B7280;margin-bottom:10px;
            padding-left:8px;border-left:3px solid #3B82F6;text-transform:uppercase;letter-spacing:.5px}}
.report-list{{display:flex;flex-direction:column;gap:5px;margin-bottom:8px}}
.report-row{{display:block;padding:10px 14px;background:#F9FAFB;
             border:1px solid #E5E7EB;border-radius:10px;
             text-decoration:none;color:#1C1C1E;font-size:12.5px;transition:.15s}}
.report-row:hover{{background:#EFF6FF;border-color:#3B82F6;color:#1C1C1E}}
.empty{{color:#9CA3AF;font-size:12px;padding:10px 14px}}
</style>
</head>
<body>
<div class="page">
  <div class="hd">
    <div class="title">🇺🇸 US Market <span>Report</span></div>
    <div class="badge">매일 06:30 KST 업데이트</div>
  </div>

  <div class="grid">
    <div>
      <div class="sec-title">📅 일간 리포트</div>
      <div class="report-list">{file_rows(daily[:20], 'daily')}</div>
    </div>
    <div>
      <div class="sec-title">📊 격주 리포트</div>
      <div class="report-list">{file_rows(biweekly, 'biweekly')}</div>

      <div class="sec-title" style="margin-top:20px">📆 월간 리포트</div>
      <div class="report-list">{file_rows(monthly, 'monthly')}</div>

      <div class="sec-title" style="margin-top:20px">🗓 분기 리포트</div>
      <div class="report-list">{file_rows(quarterly, 'quarterly')}</div>
    </div>
  </div>
</div>
</body>
</html>"""

    idx = DOCS_DIR / "index.html"
    with open(idx,"w",encoding="utf-8") as f: f.write(html)
    print(f"✅ 인덱스: {idx}")


if __name__ == "__main__":
    build_index()
