# PPC Affiliate Platform — Implementation Summary

Your backend is aligned with the **Pay-Per-Click (PPC)** platform design. Below is what was added/changed and how to use it.

---

## What Was Implemented

### 1. **Public tracking endpoint** (main PPC entry point)
- **URL:** `GET /t/<campaign_id>?aff=<affiliate_id>`
- **Behaviour:** Validates click (bot + duplicate check), records it, updates campaign spend and affiliate earnings, then redirects to the campaign `offer_url`.
- **Duplicate rule:** Same visitor (IP + user-agent + campaign + affiliate) within **60 minutes** counts as one valid click.
- **Bot filter:** Requests with bot-like User-Agent are recorded but not paid.

### 2. **Click model and Campaign PPC fields**
- **`Click`** table: `campaign_id`, `affiliate_id`, `ip_address`, `user_agent`, `fingerprint_hash`, `is_valid`, `payout_amount`, `created_at`.
- **Campaign:** `affiliate_cpc` (what you pay per valid click), `total_clicks`, `total_spend` (denormalized for dashboards).

### 3. **Client (advertiser) API** — `/api/client`
- `POST /api/client/register` — register as client.
- `GET /api/client/campaigns` — list my campaigns (with clicks/spend).
- `POST /api/client/campaigns` — create campaign (name, offer_url, budget, cost_per_click, optional affiliate_cpc).
- `GET /api/client/campaigns/<id>` — campaign detail + PPC stats.
- `PUT /api/client/campaigns/<id>` — update campaign.
- `GET /api/client/dashboard` — summary (total clicks, total spend, campaigns).

### 4. **Affiliate link format**
- **Link format:** `https://yourdomain.com/t/<campaign_id>?aff=<affiliate_id>`
- **Endpoint:** `GET /api/affiliate/links/<campaign_id>` returns this URL and `affiliate_cpc`.

### 5. **Affiliate earnings**
- **PPC:** Each valid click adds `campaign.affiliate_cpc` to the affiliate’s `total_earnings` and `pending_payout`.
- **GET /api/affiliate/earnings** now includes `valid_clicks`.

### 6. **Demo (no auth)**
- `GET /api/demo/dashboard/client` — fake client dashboard.
- `GET /api/demo/dashboard/affiliate` — fake affiliate dashboard.
- `GET /api/demo/stats` — fake platform stats.

### 7. **Realtime polling**
- **Client:** `GET /api/client/dashboard/poll` — lightweight JSON (summary + campaigns with clicks/spend). Poll every 5–10 s.
- **Affiliate:** `GET /api/affiliate/dashboard/poll` — lightweight JSON (valid_clicks, total_earnings, pending_payout, commission_rate). Poll every 5–10 s.
- **Demo:** `GET /api/demo/dashboard/client/poll` and `GET /api/demo/dashboard/affiliate/poll` — same shape, no auth.
- **JS helper:** `static/js/polling.js` — use `DashboardPolling.startPolling(url, intervalMs, callback)` or `DashboardPolling.autoStart()` with `data-poll-url` and `data-poll-interval` on a container and `data-poll-bind="path.to.key"` on elements (e.g. `summary.total_clicks`, `valid_clicks`, `total_earnings`).

### 8. **Procfile**
- `web: gunicorn run:app` for Render (or any gunicorn host).

---

## Database migration

New table and columns must be applied:

```bash
cd backend
flask db migrate -m "Add Click model and PPC fields on Campaign"
flask db upgrade
```

If you use `db.create_all()` on a fresh DB, the new tables/columns are created automatically; for an existing DB, run the migration above.

---

## PPC flow (recap)

1. **Client:** Registers → creates campaign (target URL, budget, client CPC, optional affiliate CPC) → gets tracking link pattern.
2. **Affiliate:** Registers → chooses campaign → gets link `https://yourdomain.com/t/<campaign_id>?aff=<affiliate_id>`.
3. **Visitor:** Clicks link → server validates (no bot, no duplicate in 60 min) → records valid click → updates campaign spend and affiliate balance → redirects to offer URL.
4. **Monetization:** Client pays `cost_per_click` per click; affiliate earns `affiliate_cpc` per valid click; your margin = `cost_per_click - affiliate_cpc`.

---

## Optional next steps (from your doc)

- **Realtime dashboard:** AJAX polling or Flask-SocketIO for live clicks/earnings.
- **Render checklist:** env vars (`DATABASE_URL`, `SECRET_KEY`), run migrations on deploy, use Procfile.
- **Stricter fraud:** VPN/proxy checks, rate limits per IP, optional server-side fingerprinting.
