#!/usr/bin/env python3
"""Part 5 data pipeline — per-day, per-SKU metrics for the WHOLE catalogue.

WHY THIS REPLACED the old top-20-lists-per-day payload:
the old file stored only each day's top-20 lists, so a user-selected date RANGE could not be
aggregated (the top-20 of a range is not the union of daily top-20s). This pipeline stores every
SKU's 4 metrics for every day, so the page can compute, for ANY range:
  * top-20 movers by ΔGMV / ΔQty / ΔCustomers, gainers and losers
  * the absolute GMV / Qty / Customers / Orders totals for that range
  * the comparison vs the same range shifted back 7 days (WoW)
Nothing is pre-aggregated and nothing is pre-ranked → "all the data is ready" for whatever the user
picks.

STORAGE: one file per calendar month, `data/sku_p5/sku-YYYY-MM.js`. A closed month is written once
and never touched again, so daily churn is limited to the current month (~1 MB/day) instead of
rewriting the entire history. Loaded on demand by the page.

    python3 sku_p5_extract.py --from 2026-09-13 --to 2026-09-15     # a range
    python3 sku_p5_extract.py --days 1                              # daily incremental (yesterday)
    python3 sku_p5_extract.py                                       # full history 2025-01-01 -> yesterday
    python3 sku_p5_extract.py --report                              # month sizes / coverage
"""
import argparse
import csv
import io
import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import date, datetime, timedelta

import requests
import urllib3

urllib3.disable_warnings()

REPO = '/home/chanlm/.hermes/liteapp-dashboard'
OUTDIR = f'{REPO}/data/sku_p5'
SERVER = 'https://inhouse-analytics.hktv.com.hk'
CRED = '/home/chanlm/.hermes/MD/credentials/tableau credentials.txt'
SCOPE = 'WebMobile'
FLOOR = '2025-01-01'
CHUNK = 20          # days per request — measured safe (20 days = 64 MB / ~93 s)
RESPFMT = '%d %B %Y'


def view_id():
    src = open('/home/chanlm/.hermes/profiles/boo/scripts/sku_movers_daily.py', encoding='utf-8').read()
    m = re.search(r"VIEW_ID\s*=\s*['\"]([^'\"]+)", src)
    if not m:
        raise SystemExit('cannot resolve the Part-5 view id from sku_movers_daily.py')
    return m.group(1)


def creds():
    c = dict(l.strip().split('=', 1) for l in open(CRED) if '=' in l and not l.startswith('#'))
    return c['USERNAME'], c['PASSWORD']


def signin():
    u, p = creds()
    s = requests.Session()
    r = s.post(f'{SERVER}/api/3.20/auth/signin', verify=False, timeout=60,
               json={'credentials': {'name': u, 'password': p, 'site': {'contentUrl': ''}}})
    r.raise_for_status()
    tok, site = re.search(r'token="([^"]+)"', r.text), re.search(r'site id="([^"]+)"', r.text)
    if not (tok and site):
        raise RuntimeError('signin: no token/site')
    return s, tok.group(1), site.group(1)


def fetch_chunk(session, token, site, days, meta=None):
    """{day_iso: {sku: [gmv, qty, cust, ord]}} for `days` in ONE request."""
    want = {d.isoformat() for d in days}
    r = session.get(f'{SERVER}/api/3.20/sites/{site}/views/{view_id()}/data',
                    headers={'X-Tableau-Auth': token},
                    params={'format': 'csv', 'vf_Order Date (day)': ','.join(sorted(want))},
                    verify=False, timeout=900)
    r.raise_for_status()
    out = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0, 0.0, 0.0]))
    for x in csv.DictReader(io.StringIO(r.content.decode('utf-8', 'replace'))):
        if x['sales_application'] != SCOPE:
            continue
        try:                                     # filter values are ISO, response values are long form
            iso = datetime.strptime(x['Day of Order Date (day)'], RESPFMT).date().isoformat()
        except ValueError:
            continue                             # skips the 'All' aggregate block
        if iso not in want:
            continue
        try:
            v = float((x['Measure Values'] or '0').replace(',', '') or 0)
        except ValueError:
            continue
        if meta is not None and x['sku_id'] not in meta:
            b, n = x['brand_chi'] or '', x['sku_name_chi'] or ''
            if b or n:
                meta[x['sku_id']] = (b, n)
        e = out[iso][x['sku_id']]
        m = x['Measure Names']
        if m == 'GMV':
            e[0] += v
        elif m == 'quantity':
            e[1] += v
        elif m == 'Cust #':
            e[2] += v
        elif m == 'Parent Order #':
            e[3] += v
    return out


def month_of(iso):
    return iso[:7]


def read_month(path):
    """Read a month store back out of the .js wrapper.

    NOTE: the file is JS (`window.SKU_P5=...;SKU_P5["M"]={...};`), NOT JSON — json.load() on it
    raises "Expecting value: line 1 column 1", which is exactly how the first backfill crashed on
    the one month that already existed (2026-09) after finishing the other 608 days.
    """
    if not os.path.exists(path):
        return {'s': [], 'd': {}}
    txt = open(path, encoding='utf-8').read()
    m = re.search(r'SKU_P5\["[^"]+"\]=(\{.*?\});\s*$', txt, re.DOTALL)
    return json.loads(m.group(1)) if m else {'s': [], 'd': {}}


def write_month(session, token, site, month, days, meta, force=False, chunk=CHUNK):
    """Write data/sku_p5/sku-YYYY-MM.js for `days` (list of date) + upsert into `meta`."""
    path = f'{OUTDIR}/sku-{month}.js'
    store = {'s': [], 'd': {}} if force else read_month(path)
    days = sorted(days)
    got = {}
    for i in range(0, len(days), chunk):
        part = days[i:i + chunk]
        t0 = time.time()
        got.update(fetch_chunk(session, token, site, part, meta))
        print(f'    {month}: {len(part)} days in {time.time() - t0:.0f}s '
              f'({part[0]}..{part[-1]})', flush=True)
    # fill in metadata for SKUs already stored (a single-day seed left ~97% blank)
    filled = 0
    for row in store['s']:
        if not (row[1] or row[2]) and row[0] in meta:
            row[1], row[2] = meta[row[0]]
            filled += 1
    if filled:
        print(f'    {month}: filled metadata for {filled} existing SKUs', flush=True)
    index = {row[0]: i for i, row in enumerate(store['s'])}
    for iso, skus in got.items():
        rows = []
        for sku, (gmv, qty, cust, ordv) in skus.items():
            if gmv <= 0 and qty <= 0:            # no activity that day
                continue
            if sku not in index:
                index[sku] = len(store['s'])
                store['s'].append([sku, meta.get(sku, ('', ''))[0], meta.get(sku, ('', ''))[1]])
            rows.append([index[sku], round(gmv), round(qty), round(cust), round(ordv)])
        store['d'][iso] = rows
    os.makedirs(OUTDIR, exist_ok=True)
    js = ('window.SKU_P5=window.SKU_P5||{};SKU_P5[' + json.dumps(month) + ']='
          + json.dumps(store, ensure_ascii=False, separators=(',', ':')) + ';')
    tmp = path + '.tmp'
    open(tmp, 'w', encoding='utf-8').write(js)
    os.replace(tmp, path)
    return path, len(store['s']), len(store['d'])


def sku_meta(session, token, site, day):
    """sku -> (brand, name) from any single day."""
    r = session.get(f'{SERVER}/api/3.20/sites/{site}/views/{view_id()}/data',
                    headers={'X-Tableau-Auth': token},
                    params={'format': 'csv', 'vf_Order Date (day)': day.isoformat()},
                    verify=False, timeout=600)
    r.raise_for_status()
    meta = {}
    for x in csv.DictReader(io.StringIO(r.content.decode('utf-8', 'replace'))):
        if x['sku_id'] not in meta:
            meta[x['sku_id']] = (x['brand_chi'] or '', x['sku_name_chi'] or '')
    return meta


def cmd_report():
    total = 0
    if not os.path.isdir(OUTDIR):
        print('no data yet'); return 0
    for f in sorted(os.listdir(OUTDIR)):
        if not f.endswith('.js'):
            continue
        p = f'{OUTDIR}/{f}'
        sz = os.path.getsize(p)
        total += sz
        txt = open(p, encoding='utf-8').read()
        days = len(re.findall(r'"\d{4}-\d{2}-\d{2}":\[', txt))
        skus = txt.count('],[')  # rough
        print(f'  {f:22s} {sz/1e6:6.2f} MB  {days} days')
    print(f'  TOTAL {total/1e6:.2f} MB')
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--from', dest='frm')
    ap.add_argument('--to', dest='to')
    ap.add_argument('--days', type=int, help='last N days (incremental)')
    ap.add_argument('--chunk', type=int, default=CHUNK)
    ap.add_argument('--force', action='store_true', help='rewrite existing months from scratch')
    ap.add_argument('--report', action='store_true')
    a = ap.parse_args()
    if a.report:
        return cmd_report()

    today = datetime.now().date()
    if a.days:
        start, end = today - timedelta(days=a.days), today - timedelta(days=1)
    elif a.frm:
        start = datetime.strptime(a.frm, '%Y-%m-%d').date()
        end = datetime.strptime(a.to, '%Y-%m-%d').date() if a.to else start
    else:
        start, end = date.fromisoformat(FLOOR), today - timedelta(days=1)
    print(f'Part-5 extract {start} -> {end} ({(end - start).days + 1} days, chunk={a.chunk})')

    session, token, site = signin()
    meta = sku_meta(session, token, site, end)      # seed; grows from every fetched row
    print(f'  sku metadata seed: {len(meta)} SKUs')

    by_month = defaultdict(list)
    d = start
    while d <= end:
        by_month[month_of(d.isoformat())].append(d)
        d += timedelta(days=1)

    for month, days in sorted(by_month.items()):
        path = f'{OUTDIR}/sku-{month}.js'
        if os.path.exists(path) and not a.force and not a.days:
            have = set(re.findall(r'"(\d{4}-\d{2}-\d{2})":\[', open(path, encoding='utf-8').read()))
            days = [x for x in days if x.isoformat() not in have]
            if not days:
                print(f'  {month}: already complete — skipped')
                continue
        p, nsku, ndays = write_month(session, token, site, month, days, meta, force=a.force, chunk=a.chunk)
        print(f'  {month}: wrote {ndays} days, {nsku} SKUs -> {os.path.getsize(p)/1e6:.2f} MB')
    print('done')
    return 0


if __name__ == '__main__':
    sys.exit(main())
