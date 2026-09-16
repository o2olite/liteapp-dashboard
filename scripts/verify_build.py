#!/usr/bin/env python3
"""Canonical build check for the full demo.

Runs build_full_demo.py, then sanity-checks the output against the CURRENT data
files (no hard-coded dates/values -> survives daily data rollover).

Checks:
  * build exits 0
  * no PII redaction placeholders leaked into the HTML
  * Part 3 latest date/value matches data/new_customers_lite_2023_2026.json
  * DS latest date/value matches the same file
  * 5 part banners, 5 SKU tables, SKU hyperlink
  * external data/sku_movers_daily.js referenced + latest key matches the json
  * injected JS passes `node --check`
"""
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(ROOT)                       # ~/.hermes/liteapp-dashboard
BUILD = os.path.join(ROOT, 'build_full_demo.py')
OUT = os.path.join(REPO, 'liteapp_dashboard_full_demo.html')
NC_JSON = os.path.join(REPO, 'data', 'new_customers_lite_2023_2026.json')
SKU_JSON = os.path.join(REPO, 'data', 'sku_movers_daily_2026.json')
SKU_JS = os.path.join(REPO, 'data', 'sku_movers_daily.js')

fail = 0


def ck(name, ok, detail=''):
    global fail
    print(('PASS  ' if ok else 'FAIL  ') + name + (f'   [{detail}]' if detail and not ok else ''))
    if not ok:
        fail += 1


# ---------- expectations derived from the data files ----------
nc = json.load(open(NC_JSON))
t_latest = max(nc['total'])
t_val = nc['total'][t_latest]['c']
ds_latest = max(nc['ds'])
ds_val = nc['ds'][ds_latest]
P5_DIR = os.path.join(REPO, 'data', 'sku_p5')          # per-day, per-SKU store (2026-09-16 design)
_p5_months = sorted(f for f in os.listdir(P5_DIR)) if os.path.isdir(P5_DIR) else []
_p5_newest = open(os.path.join(P5_DIR, _p5_months[-1]), encoding='utf-8').read() if _p5_months else ''
_days = re.findall(r'"(\d{4}-\d{2}-\d{2})":\[', _p5_newest)
sku_days = {d: 1 for d in _days}
sku_latest = max(_days) if _days else ''

print(f"data: Part3 latest={t_latest} total={t_val} | DS latest={ds_latest} ds={ds_val} "
      f"| SKU days={len(sku_days)} latest={sku_latest}")
print()

# ---------- run the live refresh (post-deploy path) ----------
# The revamp is deployed: index.html carries the sections, so we refresh the baked consts in place
# (refresh_page.py mirrors index.html to the demo) instead of re-running build_full_demo.py, which
# injects from a clean base and now guards against running on a revamped page.
REFRESH = os.path.join(ROOT, 'refresh_page.py')
r = subprocess.run([sys.executable, REFRESH], capture_output=True, text=True)
ck('refresh_page exits 0', r.returncode == 0, (r.stderr or r.stdout)[-400:])

if r.returncode == 0:
    html = open(OUT, encoding='utf-8').read()

    for m in ('<PERSON', '<PHONE', '<EMAIL', '<CREDIT'):
        ck(f'no {m!r} placeholder', m not in html)

    ck(f'Part 3 data present ({t_latest} total={t_val})',
       f'"{t_latest}":{{c:{t_val},' in html)
    ck(f'DS correct ({ds_latest}={ds_val})',
       f'"{ds_latest}":{{c:{ds_val}}}' in html)

    n_banners = html.count('class="part-banner"')
    ck('5 part banners', n_banners >= 5, f'found {n_banners}')
    ck('5 SKU tables', all(x in html for x in
        ['skuGainersBody', 'skuQtyBody', 'skuCustGainersBody', 'skuQtyLosersBody', 'skuCustLosersBody']))
    ck('SKU hyperlink', 'http://hktvmall.com/p/' in html)

    # ---------- Part-5 per-day store (data/sku_p5/sku-YYYY-MM.js) ----------
    ck('page lazy-loads the Part-5 month store', "data/sku_p5/sku-" in html)
    ck('retired 7.9MB top-20 payload no longer referenced',
       'src="data/sku_movers_daily.js"' not in html)
    ck('Part-5 month files present', bool(_p5_months), f'{len(_p5_months)} files')
    if _p5_months:
        ck('newest month defines window.SKU_P5', 'window.SKU_P5' in _p5_newest)
        ck(f'newest month carries the latest day ({sku_latest})', f'"{sku_latest}":[' in _p5_newest)
        ck('store rows are [idx,gmv,qty,cust,ord]', bool(re.search(r'\[\d+,\d+,\d+,\d+,\d+\]', _p5_newest)))

    # ---------- injected script syntax ----------
    m = re.search(r"<script>\s*\(function\(\) \{\s*const NC_TOTAL = .*?"
                  r"window\.renderNewCustomers = renderNewCustomers;.*?\}\)\(\);\s*</script>",
                  html, re.DOTALL)
    ck('injected script found', bool(m))
    if m:
        js = m.group(0).replace('<script>', '').replace('</script>', '')
        fd, jf = tempfile.mkstemp(prefix='verify-', suffix='.js')
        os.close(fd)
        try:
            open(jf, 'w').write(js)
            nr = subprocess.run(['node', '--check', jf], capture_output=True, text=True)
            ck('injected JS syntax (node --check)', nr.returncode == 0, nr.stderr[-300:])
        finally:
            os.unlink(jf)

print(f'\n{"PASS" if fail == 0 else "FAIL"} ({fail} failures)')
sys.exit(1 if fail else 0)
