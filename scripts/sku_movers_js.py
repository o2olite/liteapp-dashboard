#!/usr/bin/env python3
"""Shared emitter for the Part 5 SKU-movers JS payload.

Single source of truth for the wire format consumed by the dashboard via
`<script src="data/sku_movers_daily.js">`. Used by BOTH the demo build
(build_full_demo.py) and the daily cron (sku_movers_daily.py) so the two can
never drift apart.

Wire format per day:
    "YYYY-MM-DD": {g:[...], q:[...], c:[...], ql:[...], cl:[...]}
each row: [sku, brand, name, dgmv, gmv_cur, dqty, qty_cur, dcust, pct, qty_base]
"""
import json

GROUPS = ('top_gainers_gmv', 'top_gainers_qty', 'top_gainers_cust',
          'top_losers_qty', 'top_losers_cust')
SHORT = {'top_gainers_gmv': 'g', 'top_gainers_qty': 'q', 'top_gainers_cust': 'c',
         'top_losers_qty': 'ql', 'top_losers_cust': 'cl'}
FIELDS = ('sku', 'brand', 'name', 'dgmv', 'gmv_cur', 'dqty', 'qty_cur', 'dcust', 'pct', 'qty_base')
_STRS = ('sku', 'brand', 'name')


def movers_arr(items):
    """One mover list -> JS array literal."""
    rows = []
    for it in items:
        vals = []
        for f in FIELDS:
            if f in _STRS:
                vals.append(json.dumps(it.get(f, ''), ensure_ascii=False))
            elif f == 'pct':
                pct = it.get('pct')
                vals.append('null' if pct is None else pct)
            else:
                vals.append(it.get(f, 0))
        rows.append('[' + ','.join(str(v) for v in vals) + ']')
    return '[' + ','.join(rows) + ']'


def day_js(day):
    return '{' + ','.join('%s:%s' % (SHORT[g], movers_arr(day[g])) for g in GROUPS) + '}'


def days_js(days):
    return '{' + ','.join('"%s":%s' % (d, day_js(day)) for d, day in sorted(days.items())) + '}'


def write_js(path, days):
    """Write `window.SKU_MOVERS_DAILY = {...};` (file://-loadable, no fetch/CORS)."""
    with open(path, 'w') as f:
        f.write('window.SKU_MOVERS_DAILY = ' + days_js(days) + ';')
    return path
