#!/usr/bin/env python3
"""Refresh the baked Part-3/SKU consts in the DEPLOYED page, then mirror it to the review demo.

This is the post-deploy refresh path: once index.html carries the revamp sections, Part 3 is kept
current by re-injecting its consts in place (scripts/nc_consts.py) — NOT by re-running
build_full_demo.py, which injects from a clean base and would duplicate the sections.
"""
import shutil
import sys

from nc_consts import inject

REPO = '/home/chanlm/.hermes/liteapp-dashboard'
PAGE = f'{REPO}/index.html'
DEMO = f'{REPO}/liteapp_dashboard_full_demo.html'


def refresh(mirror=True):
    html = open(PAGE, encoding='utf-8').read()
    if 'class="sku-section"' not in html:
        raise SystemExit('REFUSING: index.html has no revamp sections — deploy the revamp first.')
    html, n = inject(html)
    if n != 5:
        raise SystemExit(f'ABORT: expected 5 consts, replaced {n} — page left untouched')
    open(PAGE, 'w', encoding='utf-8').write(html)
    if mirror:
        shutil.copy2(PAGE, DEMO)
    return n


if __name__ == '__main__':
    print(f'refreshed {refresh()} consts (+ mirrored to the review demo)')
