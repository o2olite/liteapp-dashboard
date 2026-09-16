#!/usr/bin/env python3
"""Single source of truth for the Part-3 (new customers) + SKU-latest constants baked into the
dashboard HTML.

The deployed page carries them as inline consts. This module rebuilds them from the data files and
re-injects them IN PLACE by regex — the same pattern the pipeline already uses for
salesData / CAT_DATA_RAW / TRAFFIC_DATA, so the daily chain can refresh Part 3 without re-running
the whole page build.

    python3 nc_consts.py --check <file.html>     # report the dates currently baked in
    python3 nc_consts.py <file.html>             # re-inject from the data files (in place)
"""
import argparse
import json
import os
import re
import sys

REPO = '/home/chanlm/.hermes/liteapp-dashboard'
NC = f'{REPO}/data/new_customers_lite_2023_2026.json'
SKU = f'{REPO}/data/sku_movers_daily_2026.json'          # legacy top-20 payload (retired)
SKU_P5 = f'{REPO}/data/sku_p5'                          # per-day, per-SKU store (current)


def _sku_latest():
    """Newest day in the per-day store (falls back to the legacy payload)."""
    try:
        months = sorted(f[:-3] for f in os.listdir(SKU_P5) if f.startswith('sku-') and f.endswith('.js'))
        if months:
            txt = open(f'{SKU_P5}/sku-{months[-1]}.js', encoding='utf-8').read()
            days = re.findall(r'"(\d{4}-\d{2}-\d{2})":\[', txt)
            if days:
                return max(days)
    except OSError:
        pass
    return sorted(json.load(open(SKU, encoding='utf-8'))['days'])[-1]


def consts(nc=None, sku_latest=None):
    """{const_name: js_literal} — keys unquoted, matching the existing page."""
    nc = nc or json.load(open(NC, encoding='utf-8'))
    if sku_latest is None:
        sku_latest = _sku_latest()

    c3 = lambda m: '{' + ','.join(f'"{d}":{{c:{e["c"]},o:{e["o"]},g:{e["g"]}}}'
                                  for d, e in sorted(m.items())) + '}'
    c1 = lambda m: '{' + ','.join(f'"{d}":{{c:{v}}}' for d, v in sorted(m.items())) + '}'
    return {'NC_TOTAL': c3(nc['total']), 'NC_ONLINE': c3(nc['online']), 'NC_POS': c3(nc['pos']),
            'NC_DS': c1(nc['ds']), 'SKU_LATEST_DATE': f"'{sku_latest}'"}


def inject(html, c=None):
    """Replace every baked const. Idempotent: re-running yields identical output."""
    c = c or consts()
    hits = 0
    for name, literal in c.items():
        pat = re.compile(r'((?:const|var|let)\s+' + name + r'\s*=\s*)[^\n]*?;')
        html, n = pat.subn(lambda m: m.group(1) + literal + ';', html, count=1)
        hits += n
    return html, hits


def report(html):
    """{const: (first_date, last_date, n_days)} — what is currently baked in."""
    out = {}
    for name in ('NC_TOTAL', 'NC_ONLINE', 'NC_POS', 'NC_DS'):
        m = re.search(r'(?:const|var|let)\s+' + name + r'\s*=\s*\{.*?\};', html, re.DOTALL)
        dates = re.findall(r'"(\d{8})":', m.group(0)) if m else []
        out[name] = (dates[0], dates[-1], len(dates)) if dates else None
    m = re.search(r"SKU_LATEST_DATE\s*=\s*'([\d-]+)'", html)
    out['SKU_LATEST_DATE'] = m.group(1) if m else None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('html')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    html = open(a.html, encoding='utf-8').read()
    if a.check:
        for k, v in report(html).items():
            print(f'  {k:16s} {v}')
        return 0
    html, n = inject(html)
    if n != 5:
        print(f'ABORT: expected 5 consts, replaced {n} — file left untouched', file=sys.stderr)
        return 2
    open(a.html, 'w', encoding='utf-8').write(html)
    print(f'injected {n} consts')
    return 0


if __name__ == '__main__':
    sys.exit(main())
