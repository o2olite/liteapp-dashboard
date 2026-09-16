#!/usr/bin/env python3
"""Build full demo = production index.html + Part3 + Part4 + category WoW + English traffic."""
import json, re, sys
from sku_movers_js import write_js

BASE = '/home/chanlm/.hermes/liteapp-dashboard/index.html'
OUT = '/home/chanlm/.hermes/liteapp-dashboard/liteapp_dashboard_full_demo.html'

html = open(BASE).read()

# GUARD (2026-09-16): this builder injects the revamp sections from a CLEAN base. Running it on a
# page that already has them duplicates every section. Post-deploy, refresh in place instead:
#   python3 scripts/refresh_page.py
if 'class="sku-section"' in html and '--force' not in sys.argv:
    raise SystemExit('REFUSING: index.html already contains the revamp sections. '
                     'Use scripts/refresh_page.py (in-place const refresh) or pass --force.')

# ---------- 1. Load fresh data ----------
nc = json.load(open('/home/chanlm/.hermes/liteapp-dashboard/data/new_customers_lite_2023_2026.json'))
sku_daily = json.load(open('/home/chanlm/.hermes/liteapp-dashboard/data/sku_movers_daily_2026.json'))
_sku_days = sku_daily['days']
SKU_LATEST_DATE = sorted(_sku_days)[-1]

def js_map(m):
    parts = []
    for d in sorted(m.keys()):
        e = m[d]
        parts.append(f'"{d}":{{c:{e["c"]},o:{e["o"]},g:{e["g"]}}}')
    return '{' + ','.join(parts) + '}'

NC_TOTAL_JS = js_map(nc['total'])
NC_ONLINE_JS = js_map(nc['online'])
NC_POS_JS = js_map(nc['pos'])
NC_DS_JS = '{' + ','.join(f'"{d}":{{c:{v}}}' for d, v in sorted(nc['ds'].items())) + '}'

# Part 5 payload — emitter shared with the daily cron (scripts/sku_movers_js.py)
write_js('/home/chanlm/.hermes/liteapp-dashboard/data/sku_movers_daily.js', _sku_days)

# ---------- 2. Traffic -> English (longest-first to avoid substring clobbering) ----------
traffic_en = [
    ('近 30 日流量走勢（每日）', '30-day Traffic Trend (daily)'),
    ('流量走勢（每日）', 'Traffic Trend (daily)'),
    ('30 日流量走勢', '30-day Traffic Trend'),
    ('流量走勢', 'Traffic Trend'),
    ('🚀 應用流量 App Traffic', '🚀 App Traffic'),
    ('📅 近 30 日', '📅 Last 30 days'),
    ('訪客人數 Unique Visitors', 'Unique Visitors'),
    ('瀏覽次數 Sessions', 'Sessions'),
    ('裝置數 Unique Devices', 'Unique Devices'),
    ('人均瀏覽 Sessions / Visitor', 'Sessions / Visitor'),
    ('✱ 星期三 = 流量高峰（會員日），同 Online GMV 週三爆升同步。', '✱ Wednesday = traffic peak (member day), in sync with the Wednesday Online GMV spike.'),
    ('📅 所選時段無流量數據', '📅 No traffic data for selected period'),
    ('⚠️ 所選時段無流量數據', '⚠️ No traffic data for selected period'),
    ("'單日'", "'single day'"),
    ("'日均 · ' + nDays + ' 日平均'", "'daily average (avg daily) · ' + nDays + ' days'"),
    ("'（單日）'", "'(single day)'"),
    ('📊 數據期間：', '📊 Data period:'),
    ("% vs 上週'", "% vs last week'"),
    ('流量資料由 ', 'Traffic data available from '),
    (' 起；較早日期無數據。', ' onward; earlier dates have no data.'),
]
for old, new in traffic_en:
    html = html.replace(old, new)

# Traffic "avg daily" label on KPI headers (multi-day)
_tl_anchor = "if (headEl) headEl.textContent = '📊 Data period:' + periodTxt;"
_tl_new = _tl_anchor + """
        const avgSuffix = (nDays === 1) ? '' : ' (avg daily)';
        document.querySelectorAll('#trafficKpis .kpi-card h3').forEach(function(el){
            if (!el.getAttribute('data-base')) el.setAttribute('data-base', el.textContent);
            el.textContent = el.getAttribute('data-base') + avgSuffix;
        });"""
html = html.replace(_tl_anchor, _tl_new, 1)

# ---------- 3. CSS for Part 3/4 ----------
part_css = """
        /* ===== Part section banners (unified) ===== */
        .part-banner { background: #0f172a; color: #fff; padding: 12px 20px; border-radius: 8px; font-size: 15px; font-weight: 700; margin: 28px 0 14px; display: flex; align-items: center; gap: 12px; }
        .part-num { background: #3b82f6; padding: 3px 12px; border-radius: 4px; font-size: 13px; letter-spacing: 0.5px; white-space: nowrap; }
        .part-title { font-size: 15px; font-weight: 700; color: #fff; }
        .part-desc { font-size: 12px; font-weight: 400; color: #94a3b8; }
        .part-badge { margin-left: auto; background: rgba(255,255,255,0.15); padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 500; white-space: nowrap; }
        /* ===== Part 3: New Customers ===== */
        .nc-section { margin: 28px 0; }
        .nc-header { background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%); color: #fff; border-radius: 12px; padding: 16px 24px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
        .nc-header h2 { color: #fff; margin: 0; font-size: 18px; }
        .nc-header .badge { background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 999px; font-size: 13px; }
        .nc-kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 18px; }
        .nc-kpi { background: #fff; padding: 18px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); border-top: 4px solid #3949ab; }
        .nc-kpi h3 { font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
        .nc-kpi .period { font-size: 11px; color: #94a3b8; margin-bottom: 8px; }
        .nc-kpi .value { font-size: 26px; font-weight: 700; color: #1e293b; }
        .nc-kpi .change { font-size: 12px; margin-top: 4px; }
        .nc-kpi .change.up { color: #16a34a; } .nc-kpi .change.down { color: #dc2626; }
        .nc-chart-card { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); margin-bottom: 18px; }
        .nc-chart-card h3 { font-size: 15px; color: #1e293b; margin-bottom: 12px; }
        .nc-table-wrap { background: #fff; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); overflow: hidden; margin-bottom: 24px; }
        .nc-table-wrap h3 { padding: 16px 20px; font-size: 15px; color: #1e293b; border-bottom: 1px solid #e2e8f0; }
        .nc-scroll { overflow-x: auto; }
        .nc-table { width: 100%; border-collapse: collapse; font-size: 13px; }
        .nc-table th { background: #1a237e; color: white; padding: 9px 8px; text-align: center; font-size: 11px; text-transform: uppercase; }
        .nc-table th.gh { background: #303f9f; }
        .nc-table td { padding: 9px 8px; border-bottom: 1px solid #e2e8f0; text-align: center; }
        .nc-table tbody tr:nth-child(odd) { background: #f8fafc; } .nc-table tbody tr:nth-child(even) { background: #f1f5f9; }
        .nc-pos { color: #16a34a; } .nc-neg { color: #dc2626; } .nc-neutral { color: #94a3b8; }
        .nc-legend { background: #e8eaf6; color: #1a237e; padding: 10px 16px; border-radius: 8px; margin-top: 12px; font-size: 12px; line-height: 1.6; }
        .nc-avail { font-size: 11.5px; color: #475569; background: #f1f5f9; border-left: 3px solid #94a3b8; padding: 7px 12px; border-radius: 4px; margin: -4px 0 16px; }
        @media (max-width: 900px) { .nc-kpis { grid-template-columns: repeat(2, 1fr); } }

        /* ===== Part 4: SKU movers ===== */
        .sku-section { margin: 28px 0; }
        .sku-header { background: linear-gradient(135deg, #4a148c 0%, #7b1fa2 100%); color: #fff; border-radius: 12px; padding: 16px 24px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
        .sku-header h2 { color: #fff; margin: 0; font-size: 18px; }
        .sku-header .badge { background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 999px; font-size: 13px; }
        .sku-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-bottom: 18px; }
        @media (max-width: 900px) { .sku-grid { grid-template-columns: 1fr; } }
        .sku-table-wrap { background: #fff; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); overflow: hidden; }
        .sku-table-wrap h3 { padding: 14px 18px; font-size: 14px; border-bottom: 1px solid #e2e8f0; }
        .sku-table-wrap h3.gain { color: #16a34a; } .sku-table-wrap h3.loss { color: #dc2626; }
        .sku-table { width: 100%; border-collapse: collapse; font-size: 12px; }
        .sku-table th { background: #4a148c; color: white; padding: 8px 6px; text-align: center; font-size: 10px; text-transform: uppercase; }
        .sku-table td { padding: 7px 6px; border-bottom: 1px solid #e2e8f0; text-align: center; }
        .sku-table td.l { text-align: left; } .sku-table td.lb { text-align: left; font-weight: 600; }
        .sku-table td.sku-name { max-width: 300px; white-space: normal; word-break: break-word; font-size: 11px; }
        .sku-table td.sku-id { max-width: 120px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 10px; }
        .sku-table-wrap { overflow-x: auto; }
        .sku-table tbody tr:nth-child(odd) { background: #f8fafc; } .sku-table tbody tr:nth-child(even) { background: #f1f5f9; }
        .sku-link { color: #7b1fa2; text-decoration: none; font-family: 'SF Mono', Monaco, monospace; font-size: 11px; }
        .sku-link:hover { text-decoration: underline; }
        .sku-warn { color: #f59e0b; font-size: 12px; }
        .sku-brand-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 10px; }
        .sku-brand-chip { background: #fff; border-radius: 10px; padding: 11px 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); display: flex; align-items: center; }
        .sku-brand-chip .rank { background: #7b1fa2; color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; flex: none; }
        .sku-brand-chip .name { flex: 1; margin-left: 9px; font-weight: 600; color: #1e293b; font-size: 13px; }
        .sku-brand-chip .gmv { color: #64748b; font-weight: 700; font-size: 12px; }
"""

# ---------- 4. Part 3/4 HTML ----------
part_html = """
    <!-- ===== Part 3: New Customers Performance ===== -->
    <div class="nc-section">
        <div class="part-banner"><span class="part-num">Part 3</span><span class="part-title">New Customers Performance</span><span class="part-badge" id="ncDateBadge">—</span></div>
        <div class="nc-kpis">
            <div class="nc-kpi" style="border-top-color:#3949ab;"><h3>Total New Customers (Unique)</h3><div class="period" id="ncTotalPeriod">—</div><div class="value" id="ncTotal">N/A</div><div class="change" id="ncTotalCh">—</div></div>
            <div class="nc-kpi" style="border-top-color:#4caf50;"><h3>Online New Customers</h3><div class="period" id="ncOnlinePeriod">—</div><div class="value" id="ncOnline">N/A</div><div class="change" id="ncOnlineCh">—</div></div>
            <div class="nc-kpi" style="border-top-color:#ff9800;"><h3>POS Shop New Customers</h3><div class="period" id="ncShopPeriod">—</div><div class="value" id="ncShop">N/A</div><div class="change" id="ncShopCh">—</div></div>
            <div class="nc-kpi" style="border-top-color:#e91e63;"><h3>DS New Customers</h3><div class="period" id="ncDSPeriod">—</div><div class="value" id="ncDS">N/A</div><div class="change" id="ncDSCh">—</div></div>
        </div>
        <div class="nc-avail" id="ncAvail">—</div>
        <div class="nc-chart-card">
            <h3 id="ncChartTitle">Daily New Customers by Channel</h3>
            <div style="position: relative; height: 340px; width: 100%;"><canvas id="ncChart"></canvas></div>
            <div class="nc-legend">Total (Unique) = dashed blue — unique across all channels (not a sum)<br>Online = green | POS Shop = orange | DS = pink<br>Comparison: vs same day last week (WoW)</div>
        </div>
        <div class="nc-table-wrap">
            <h3 id="ncTableTitle">Daily New Customers Details</h3>
            <div class="nc-scroll">
            <table class="nc-table" id="ncTable">
                <thead><tr>
                    <th rowspan="2">Date</th><th rowspan="2">Weekday</th>
                    <th colspan="2" class="gh">Online</th><th colspan="2" class="gh">POS Shop</th>
                    <th colspan="2" class="gh">DS</th><th colspan="2" class="gh">Total (Unique)</th>
                </tr><tr>
                    <th>Cust</th><th>WoW</th><th>Cust</th><th>WoW</th><th>Cust</th><th>WoW</th><th>Cust</th><th>WoW</th>
                </tr></thead>
                <tbody id="ncTableBody"></tbody>
            </table>
            </div>
        </div>
    </div>

    <!-- ===== Part 5: Product-Level SKU Movers (LITE) ===== -->
    <div class="sku-section">
        <div class="part-banner"><span class="part-num">Part 5</span><span class="part-title">Product-Level SKU Movers (LITE)</span><span class="part-badge" id="skuDateBadge">—</span></div>
        <div class="nc-legend" style="margin-bottom:14px;">% WoW = GMV change vs same weekday last week, relative to last week's GMV. ⚠ = single-unit sale (high-ticket, low volume — e.g. one aircon/phone).</div>
        <div class="sku-grid">
            <div class="sku-table-wrap">
                <h3 class="gain">▲ Top 20 GMV Gainers (vs same weekday last week)</h3>
                <table class="sku-table"><thead><tr><th>#</th><th>Brand</th><th>SKU</th><th>SKU ID</th><th>Δ GMV</th><th>% WoW</th><th>GMV today</th><th>Δ Qty</th><th>Δ Cust</th></tr></thead><tbody id="skuGainersBody"></tbody></table>
            </div>
            <div class="sku-table-wrap">
                <h3 class="gain">▲ Top 20 QTY Gainers (vs same weekday last week)</h3>
                <table class="sku-table"><thead><tr><th>#</th><th>Brand</th><th>SKU</th><th>SKU ID</th><th>Δ Qty</th><th>Qty today</th><th>Δ GMV</th><th>Δ Cust</th></tr></thead><tbody id="skuQtyBody"></tbody></table>
            </div>
        </div>
        <div class="sku-grid">
            <div class="sku-table-wrap">
                <h3 class="gain">▲ Top 20 by Customers Gainers (vs same weekday last week)</h3>
                <table class="sku-table"><thead><tr><th>#</th><th>Brand</th><th>SKU</th><th>SKU ID</th><th>Δ Cust</th><th>Δ GMV</th><th>Δ Qty</th></tr></thead><tbody id="skuCustGainersBody"></tbody></table>
            </div>
            <div class="sku-table-wrap">
                <h3 class="loss">▼ Top 20 QTY Losers (vs same weekday last week)</h3>
                <table class="sku-table"><thead><tr><th>#</th><th>Brand</th><th>SKU</th><th>SKU ID</th><th>Δ Qty</th><th>Qty today</th><th>Δ GMV</th><th>Δ Cust</th></tr></thead><tbody id="skuQtyLosersBody"></tbody></table>
            </div>
        </div>
        <div class="sku-table-wrap" style="margin-bottom:0;">
            <h3 class="loss">▼ Top 20 by Customers Losers (vs same weekday last week)</h3>
            <table class="sku-table"><thead><tr><th>#</th><th>Brand</th><th>SKU</th><th>SKU ID</th><th>Δ Cust</th><th>Δ GMV</th><th>Δ Qty</th></tr></thead><tbody id="skuCustLosersBody"></tbody></table>
        </div>
    </div>

"""

# ---------- 5. Inject CSS + HTML (with Part banners + reorder) ----------
html = html.replace('</style>', part_css + '\n    </style>', 1)

# Part 1 / Part 2 banners
html = html.replace('<h2 id="achievementTitle">',
    '<div class="part-banner"><span class="part-num">Part 1</span><span class="part-title">Achievement Rate This Month</span><span class="part-desc">Monthly target progress</span></div><h2 id="achievementTitle">', 1)
html = html.replace('<h2>📊 Overall Performance',
    '<div class="part-banner"><span class="part-num">Part 2</span><span class="part-title">Overall Performance</span><span class="part-desc">Overall + Online + POS + Daily GMV + Weekday + Sales table + Traffic</span></div><h2>📊 Overall Performance', 1)

# Rename SKU movers -> Part 5, split Part 3 (before category) vs Part 5 (before script)
part_html = part_html.replace('Part 4: Product-Level SKU Movers', 'Part 5: Product-Level SKU Movers')
part3_html, part5_html = part_html.split('    <!-- ===== Part 5: Product-Level SKU Movers', 1)
part5_html = '    <!-- ===== Part 5: Product-Level SKU Movers' + part5_html

# Part 3 (New Customers) -> before Category; Part 4 banner -> before Category
html = html.replace('<div class="cat-section">',
    part3_html + '\n    <div class="part-banner"><span class="part-num">Part 4</span><span class="part-title">Daily Online Sales by Category</span><span class="part-desc">GMV + Customers by Category</span></div>\n    <div class="cat-section">', 1)

# Part 5 (SKU movers) -> before first script
html = html.replace('\n    <script>\n', part5_html + '\n    <script>\n', 1)

# ---------- 6. Category 3-row restructure ----------
_full_anchor = """        for (const date of CAT_DATA.last7) {
            const row = document.createElement('tr');
            const td0 = document.createElement('td');
            td0.textContent = fmtDate(date);
            row.appendChild(td0);
            const tdW = document.createElement('td');
            tdW.textContent = fmtWeekday(date);
            row.appendChild(tdW);
            const total = (CAT_DATA.tableData[date]._t || {}).g || 0;
            for (const cat of CAT_DATA.cats) {
                const td = document.createElement('td');
                const catEntry = CAT_DATA.tableData[date][cat];
                const val = catEntry ? catEntry.g : 0;
                const amt = fmtHKD(val);
                const pct = fmtPct(val, total);
                if (amt) {
                    const cls = cat === '超級市場' ? 'cat-amount cat-highlight' : 'cat-amount';
                    td.innerHTML = '<div class="' + cls + '">' + amt + '</div>' + (pct ? '<div class="cat-pct">' + pct + '</div>' : '');
                } else {
                    td.innerHTML = '<div class="cat-dash">-</div>';
                }
                row.appendChild(td);
            }
            const tdT = document.createElement('td');
            tdT.innerHTML = '<div class="cat-amount cat-highlight">' + fmtHKD(total) + '</div>';
            row.appendChild(tdT);
            gmvBody.appendChild(row);
        }"""
_full_new = """        for (const date of CAT_DATA.last7) {
            const total = (CAT_DATA.tableData[date]._t || {}).g || 0;
            let r1 = '<tr><td>' + fmtDate(date) + '</td><td>' + fmtWeekday(date) + '</td>';
            for (const cat of CAT_DATA.cats) {
                const val = (CAT_DATA.tableData[date][cat] || {}).g || 0;
                r1 += val ? ('<td><div class="cat-amount' + (cat === '超級市場' ? ' cat-highlight' : '') + '">' + fmtHKD(val) + '</div></td>') : '<td><div class="cat-dash">-</div></td>';
            }
            r1 += '<td><div class="cat-amount cat-highlight">' + fmtHKD(total) + '</div></td></tr>';
            let r2 = '<tr class="cat-sub-row"><td></td><td class="cat-subhead">% of all</td>';
            for (const cat of CAT_DATA.cats) {
                const val = (CAT_DATA.tableData[date][cat] || {}).g || 0;
                r2 += '<td>' + (val ? '<div class="cat-pct">' + fmtPct(val, total) + '</div>' : '<div class="cat-dash">-</div>') + '</td>';
            }
            r2 += '<td><div class="cat-pct">100%</div></td></tr>';
            let r3 = '<tr class="cat-sub-row"><td></td><td class="cat-subhead">WoW %</td>';
            for (const cat of CAT_DATA.cats) {
                r3 += '<td>' + (fmtCatWoW(CAT_DATA.tableData, date, cat) || '<div class="cat-dash">-</div>') + '</td>';
            }
            r3 += '<td>' + (fmtCatWoW(CAT_DATA.tableData, date, '_t') || '<div class="cat-dash">-</div>') + '</td></tr>';
            gmvBody.innerHTML += r1 + r2 + r3;
        }"""
if _full_anchor in html:
    html = html.replace(_full_anchor, _full_new, 1)
    print("category 3-row restructure: OK")
else:
    print("category 3-row restructure: FAILED (anchor not found)")

helper_anchor = """        function fmtDate(d) {
            const parts = d.split('-');
            return parseInt(parts[2]) + '/' + parseInt(parts[1]);
        }"""
helper_insert = """        function fmtCatWoW(tableData, date, cat) {
            const d = new Date(date + 'T00:00:00');
            d.setDate(d.getDate() - 7);
            const prev = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
            const prevEntry = tableData[prev] && tableData[prev][cat];
            const prevVal = prevEntry ? prevEntry.g : 0;
            const curVal = (tableData[date] && tableData[date][cat]) ? tableData[date][cat].g : 0;
            if (!prevVal) return '';
            const pct = (curVal - prevVal) / prevVal * 100;
            let cls = 'cat-wow';
            if (pct > 0.05) cls += ' cat-wow-up';
            else if (pct < -0.05) cls += ' cat-wow-down';
            return '<div class="' + cls + '">' + (pct >= 0 ? '+' : '') + pct.toFixed(1) + '%</div>';
        }
        function fmtDate(d) {
            const parts = d.split('-');
            return parseInt(parts[2]) + '/' + parseInt(parts[1]);
        }"""
html = html.replace(helper_anchor, helper_insert, 1)

wow_css = """        .cat-table .cat-wow { color: #64748b; font-size: 10px; margin-top: 1px; }
        .cat-table .cat-wow-up { color: #16a34a; }
        .cat-table .cat-wow-down { color: #dc2626; }
        .cat-table .cat-sub-row td { padding: 2px 6px; font-size: 10px; }
        .cat-table .cat-subhead { color: #94a3b8; font-style: italic; font-size: 10px; text-align: left; }
        .cat-export-btn {"""
html = html.replace("""        .cat-export-btn {""", wow_css, 1)

# ---------- 7. Wire renderNewCustomers/renderSkuMovers into applyFilters ----------
wire_anchor = """            const catDates = baseFiltered.map(d => d.date).sort();
            renderCategorySection(catDates);
            renderTraffic(catDates);
        }"""
wire_new = """            const catDates = baseFiltered.map(d => d.date).sort();
            renderCategorySection(catDates);
            renderTraffic(catDates);
            if (window.renderNewCustomers) window.renderNewCustomers(catDates);
            if (window.renderSkuMovers) window.renderSkuMovers(catDates);
        }"""
if wire_anchor in html:
    html = html.replace(wire_anchor, wire_new, 1)
    print("applyFilters wiring: OK")
else:
    print("applyFilters wiring: FAILED")

js_code = """function fmtDateNC(yyyymmdd) {
            const m = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
            return +yyyymmdd.slice(6,8) + ' ' + m[+yyyymmdd.slice(4,6)-1] + ' ' + yyyymmdd.slice(0,4);
        }
        function toNC(dateStr) { return String(dateStr).replace(/-/g, ''); }
        function weekdayName(yyyymmdd) {
            const n = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
            return n[new Date(Date.UTC(+yyyymmdd.slice(0,4), +yyyymmdd.slice(4,6)-1, +yyyymmdd.slice(6,8))).getUTCDay()];
        }
        function wowPct(map, d) {
            const cur = map[d], prev = map[shiftDate(d, -7)];
            if (!cur || !prev || prev.c === 0) return null;
            return (cur.c - prev.c) / prev.c * 100;
        }

        // ---- KPI: single day (default) ----
        function setKpiDay(valId, chId, periodId, map, dateKey) {
            const rec = map[dateKey];
            document.getElementById(valId).textContent = rec ? rec.c.toLocaleString() : '—';
            document.getElementById(periodId).textContent = 'As of ' + fmtDateNC(dateKey);
            const pct = wowPct(map, dateKey);
            const el = document.getElementById(chId);
            if (pct === null) { el.textContent = '—'; el.className = 'change'; return; }
            el.textContent = (pct >= 0 ? '+' : '') + pct.toFixed(1) + '% vs same day last week';
            el.className = 'change ' + (pct >= 0 ? 'up' : 'down');
        }
        // ---- KPI: period lump-sum (filtered) ----
        function setKpiSum(valId, chId, periodId, map, dates) {
            let sum = 0, prevSum = 0, n = 0;
            dates.forEach(function(d) {
                if (map[d] !== undefined) { sum += map[d].c; n++; }
                const pd = shiftDate(d, -7);
                if (map[pd] !== undefined) prevSum += map[pd].c;
            });
            const rangeTxt = fmtDateNC(dates[0]) + ' – ' + fmtDateNC(dates[dates.length-1]);
            document.getElementById(valId).textContent = n === 0 ? '—' : sum.toLocaleString();
            document.getElementById(periodId).textContent = n === 0 ? rangeTxt + ' (no data)' : rangeTxt;
            const el = document.getElementById(chId);
            if (n === 0 || prevSum === 0) { el.textContent = '—'; el.className = 'change'; return; }
            const pct = (sum - prevSum) / prevSum * 100;
            el.textContent = (pct >= 0 ? '+' : '') + pct.toFixed(1) + '% vs previous ' + dates.length + ' days';
            el.className = 'change ' + (pct >= 0 ? 'up' : 'down');
        }

        let ncChartInstance = null;
        function renderNcChart(dates) {
            const ctx = document.getElementById('ncChart').getContext('2d');
            if (ncChartInstance) ncChartInstance.destroy();
            const labels = dates.map(d => +d.slice(4,6) + '/' + +d.slice(6,8));
            ncChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        { label: 'Total (Unique)', data: dates.map(d => NC_TOTAL[d] ? NC_TOTAL[d].c : null), borderColor: '#3949ab', backgroundColor: 'transparent', borderWidth: 3, borderDash: [8,4], tension: 0.3, pointRadius: 2, fill: false, spanGaps: true },
                        { label: 'Online', data: dates.map(d => NC_ONLINE[d] ? NC_ONLINE[d].c : null), borderColor: '#4caf50', backgroundColor: 'transparent', borderWidth: 2, tension: 0.3, pointRadius: 2, fill: false, spanGaps: true },
                        { label: 'POS Shop', data: dates.map(d => NC_POS[d] ? NC_POS[d].c : null), borderColor: '#ff9800', backgroundColor: 'transparent', borderWidth: 2, tension: 0.3, pointRadius: 2, fill: false, spanGaps: true },
                        { label: 'DS', data: dates.map(d => NC_DS[d] !== undefined ? NC_DS[d].c : null), borderColor: '#e91e63', backgroundColor: 'transparent', borderWidth: 2, tension: 0.3, pointRadius: 2, fill: false, spanGaps: true }
                    ]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    plugins: { legend: { position: 'top', labels: { usePointStyle: true, padding: 18, font: { size: 12 } } }, tooltip: { callbacks: { label: function(c) { if (c.parsed.y === null) return null; return c.dataset.label + ': ' + c.parsed.y.toLocaleString(); } } } },
                    scales: { y: { beginAtZero: true, ticks: { font: { size: 11 } }, grid: { color: 'rgba(0,0,0,0.05)' } }, x: { ticks: { font: { size: 10 }, maxRotation: 45, autoSkip: true, maxTicksLimit: 20 }, grid: { display: false } } }
                }
            });
        }

        function renderNcTable(dates) {
            const tbody = document.getElementById('ncTableBody');
            const desc = dates.slice().reverse();
            tbody.innerHTML = desc.map(d => {
                function cell(map) {
                    const v = map[d] !== undefined ? map[d].c : undefined;
                    if (v === undefined) return '<td class="nc-neutral">—</td>';
                    return '<td><strong>' + v.toLocaleString() + '</strong></td>';
                }
                function wowCell(map) {
                    const pct = wowPct(map, d);
                    if (pct === null) return '<td class="nc-neutral">—</td>';
                    const cls = pct >= 0 ? 'nc-pos' : 'nc-neg';
                    return '<td class="' + cls + '">' + (pct >= 0 ? '+' : '') + pct.toFixed(1) + '%</td>';
                }
                return '<tr><td>' + d.slice(0,4) + '-' + d.slice(4,6) + '-' + d.slice(6,8) + '</td><td>' + weekdayName(d) + '</td>' +
                    cell(NC_ONLINE) + wowCell(NC_ONLINE) + cell(NC_POS) + wowCell(NC_POS) +
                    cell(NC_DS) + wowCell(NC_DS) + cell(NC_TOTAL) + wowCell(NC_TOTAL) + '</tr>';
            }).join('');
        }

        function renderNewCustomers(dateList) {
            const touched = window._filterUserTouched;
            const dates = (touched && dateList && dateList.length) ? dateList.map(toNC).sort() : LAST7.slice();
            // Cards
            if (!touched) {
                setKpiDay('ncTotal', 'ncTotalCh', 'ncTotalPeriod', NC_TOTAL, LATEST);
                setKpiDay('ncOnline', 'ncOnlineCh', 'ncOnlinePeriod', NC_ONLINE, LATEST);
                setKpiDay('ncShop', 'ncShopCh', 'ncShopPeriod', NC_POS, LATEST);
                setKpiDay('ncDS', 'ncDSCh', 'ncDSPeriod', NC_DS, DS_LATEST);
                document.getElementById('ncDateBadge').textContent = 'As of ' + fmtDateNC(LATEST);
            } else {
                setKpiSum('ncTotal', 'ncTotalCh', 'ncTotalPeriod', NC_TOTAL, dates);
                setKpiSum('ncOnline', 'ncOnlineCh', 'ncOnlinePeriod', NC_ONLINE, dates);
                setKpiSum('ncShop', 'ncShopCh', 'ncShopPeriod', NC_POS, dates);
                setKpiSum('ncDS', 'ncDSCh', 'ncDSPeriod', NC_DS, dates);
                document.getElementById('ncDateBadge').textContent = fmtDateNC(dates[0]) + ' – ' + fmtDateNC(dates[dates.length-1]);
            }
            // Availability note — states the real data ranges baked in (earlier dates show —)
            const _ncK = Object.keys(NC_TOTAL).sort(), _psk = Object.keys(NC_DS).sort();
            document.getElementById('ncAvail').textContent =
                'Data available: Total / Online / POS from ' + fmtDateNC(_ncK[0]) +
                ' · DS from ' + fmtDateNC(_psk[0]) + '. Dates outside these ranges show —.';
            // Chart + table
            document.getElementById('ncChartTitle').textContent = 'Daily New Customers by Channel (' + fmtDateNC(dates[0]) + ' – ' + fmtDateNC(dates[dates.length-1]) + ')';
            document.getElementById('ncTableTitle').textContent = 'Daily New Customers Details (' + fmtDateNC(dates[0]) + ' – ' + fmtDateNC(dates[dates.length-1]) + ', ' + dates.length + ' days)';
            renderNcChart(dates);
            renderNcTable(dates);
        }

        function renderSkuMovers(dateList) {
            const _endDate = (dateList && dateList.length) ? dateList.slice().sort().slice(-1)[0] : SKU_LATEST_DATE;
            const _movers = SKU_MOVERS[_endDate] || SKU_MOVERS[SKU_LATEST_DATE];
            if (!_movers) { document.getElementById('skuDateBadge').textContent = '📅 SKU 數據未載入'; return; }   // payload missing — degrade, never throw
            const _shown = SKU_MOVERS[_endDate] ? _endDate : SKU_LATEST_DATE;
            document.getElementById('skuDateBadge').textContent = '📅 ' + _shown + ' vs same weekday last week';
            const fmt = n => (n >= 0 ? '+' : '') + Math.round(n).toLocaleString('en-US');
            const link = sku => '<a class="sku-link" href="http://hktvmall.com/p/' + sku + '" target="_blank" rel="noopener">' + sku + '</a>';
            function pctCell(m) {
                if (m[8] === null || m[8] === undefined) return '<td class="nc-neutral">n/a</td>';
                var cls = m[8] >= 0 ? 'nc-pos' : 'nc-neg';
                return '<td class="' + cls + '">' + (m[8] >= 0 ? '+' : '') + m[8] + '%</td>';
            }
            function warnQty(m, idx) { return (m[idx] < 2) ? ' <span class="sku-warn" title="single-unit sale">⚠</span>' : ''; }
            function gmvRow(m, i) {
                return '<tr><td>' + (i+1) + '</td><td class="lb">' + m[1] + warnQty(m, 6) + '</td><td class="l sku-name">' + m[2] + '</td><td class="l sku-id">' + link(m[0]) + '</td><td class="nc-pos">' + fmt(m[3]) + '</td>' + pctCell(m) + '<td>' + Math.round(m[4]).toLocaleString('en-US') + '</td><td>' + fmt(m[5]) + '</td><td>' + fmt(m[7]) + '</td></tr>';
            }
            function qtyRow(m, i) {
                return '<tr><td>' + (i+1) + '</td><td class="lb">' + m[1] + '</td><td class="l sku-name">' + m[2] + '</td><td class="l sku-id">' + link(m[0]) + '</td><td class="nc-pos">' + fmt(m[5]) + '</td><td>' + Math.round(m[6]).toLocaleString('en-US') + '</td><td>' + fmt(m[3]) + '</td><td>' + fmt(m[7]) + '</td></tr>';
            }
            function custRow(m, i) {
                return '<tr><td>' + (i+1) + '</td><td class="lb">' + m[1] + '</td><td class="l sku-name">' + m[2] + '</td><td class="l sku-id">' + link(m[0]) + '</td><td class="nc-pos">' + fmt(m[7]) + '</td><td>' + fmt(m[3]) + '</td><td>' + fmt(m[5]) + '</td></tr>';
            }
            function qtyLosersRow(m, i) {
                return '<tr><td>' + (i+1) + '</td><td class="lb">' + m[1] + '</td><td class="l sku-name">' + m[2] + '</td><td class="l sku-id">' + link(m[0]) + '</td><td class="nc-neg">' + fmt(m[5]) + '</td><td>' + Math.round(m[6]).toLocaleString('en-US') + '</td><td>' + fmt(m[3]) + '</td><td>' + fmt(m[7]) + '</td></tr>';
            }
            function custLosersRow(m, i) {
                return '<tr><td>' + (i+1) + '</td><td class="lb">' + m[1] + '</td><td class="l sku-name">' + m[2] + '</td><td class="l sku-id">' + link(m[0]) + '</td><td class="nc-neg">' + fmt(m[7]) + '</td><td>' + fmt(m[3]) + '</td><td>' + fmt(m[5]) + '</td></tr>';
            }
            document.getElementById('skuGainersBody').innerHTML = (_movers.g || []).map(gmvRow).join('');
            document.getElementById('skuQtyBody').innerHTML = (_movers.q || []).map(qtyRow).join('');
            document.getElementById('skuCustGainersBody').innerHTML = (_movers.c || []).map(custRow).join('');
            document.getElementById('skuQtyLosersBody').innerHTML = (_movers.ql || []).map(qtyLosersRow).join('');
            document.getElementById('skuCustLosersBody').innerHTML = (_movers.cl || []).map(custLosersRow).join('');
        }"""

# ---------- 8. Part 3/5 JS ----------
part_js = """    <script>
    (function() {
        const NC_TOTAL = %s;
        const NC_ONLINE = %s;
        const NC_POS = %s;
        const NC_DS = %s;
        const SKU_MOVERS = window.SKU_MOVERS_DAILY || {};   // payload may fail to load
        const SKU_LATEST_DATE = '%s';
        const LAST7 = Object.keys(NC_TOTAL).sort().slice(-7);
        const LATEST = Object.keys(NC_TOTAL).sort().slice(-1)[0];
        const DS_LATEST = Object.keys(NC_DS).sort().slice(-1)[0];
        function shiftDate(d, n) {
            const y = +d.slice(0,4), m = +d.slice(4,6)-1, dd = +d.slice(6,8);
            const dt = new Date(Date.UTC(y, m, dd + n));
            return dt.getUTCFullYear() + String(dt.getUTCMonth()+1).padStart(2,'0') + String(dt.getUTCDate()).padStart(2,'0');
        }
%s
        window.renderNewCustomers = renderNewCustomers;
        window.renderSkuMovers = renderSkuMovers;
        renderNewCustomers();
        renderSkuMovers();
    })();
    </script>
""" % (NC_TOTAL_JS, NC_ONLINE_JS, NC_POS_JS, NC_DS_JS, SKU_LATEST_DATE, js_code)

html = html.replace('</body>', '<script src="data/sku_movers_daily.js"></script>\n' + part_js + '\n</body>', 1)

# ---------- 9. Write ----------
open(OUT, 'w').write(html)
print("Wrote:", OUT, len(html), "bytes")
print("NC total:", len(nc['total']), "| DS:", len(nc['ds']))
print("SKU days:", len(_sku_days), "latest:", SKU_LATEST_DATE)
