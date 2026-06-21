content = open('us_market/reporter.py').read()
old = '# VIX 상승 = 공포 증가 = 파랑, VIX 하락 = 공포 감소 = 빨강\n        color = "#3B82F6" if chg > 0 else "#EF4444"'
new = '# VIX 하락 = 파랑, VIX 상승 = 빨강\n        color = "#EF4444" if chg > 0 else "#3B82F6"'
content = content.replace(old, new)
open('us_market/reporter.py', 'w').write(content)
print('done' if old not in content else 'FAILED - 텍스트를 찾지 못함')
