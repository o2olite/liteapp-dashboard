# Lite App Daily Sales Dashboard

⚠️ **SECURITY RULE**: When accessing OIX, PSOS, or CSIS systems - ONLY access explicitly requested pages/sections. Strictly forbidden from accessing any other data. This protects PII and sensitive information.

---

## Live Dashboard
📊 **URL**: https://o2olite.github.io/liteapp-dashboard

🔄 **Auto-updates**: Daily at 10:00 AM HKT

## Data Source
- **Tableau Server**: https://inhouse-analytics.hktv.com.hk
- **Workbook**: sales-pris
- **View**: forai-by lite-sales app

## Development Files
Main development happens at:
```
~/.hermes/tasks/lite app dashboard/
├── liteapp_dashboard.html
├── README.md
└── skills/
    └── liteapp-dashboard-development.SKILL.md
```

## Deployment
```bash
# Copy to git repo
cp ~/.hermes/tasks/lite\ app\ dashboard/liteapp_dashboard.html ~/.hermes/liteapp-dashboard/index.html

# Commit and push
cd ~/.hermes/liteapp-dashboard
git add index.html
git commit -m "Update: description"
git push origin main
```

## Last Updated
2026-07-14
