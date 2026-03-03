# PPC Affiliate Platform — API Reference

Base URL: same origin (e.g. `/api`). All JSON; use `Content-Type: application/json` and `Accept: application/json`. Session cookies for auth.

**Frontend:** Served by Flask at `/`, `/signup`, `/login`, `/dashboard`, `/dashboard/client`, `/dashboard/affiliate`. Uses `PPC_API` and `DashboardPolling` from `/static/js/api.js` and `/static/js/polling.js`.

---

## Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register user |
| POST | `/api/auth/login` | Login (sets session cookie) |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/me` | Current user (401 if not logged in) |

### POST /api/auth/register

**Body:** `{ "email", "username", "password", "first_name?", "last_name?", "role?" }`  
**role:** `user` \| `client` \| `affiliate` (default `user`)

**Response 201:** `{ "message", "user": { "id", "email", "username", "role" } }`

### POST /api/auth/login

**Body:** `{ "email", "password", "remember?" }`

**Response 200:** `{ "message", "user": { "id", "email", "username", "role" } }`

### GET /api/auth/me

**Response 200:** `{ "user": { "id", "email", "username", "first_name", "last_name", "role", "is_active", "created_at" } }`  
**Response 401:** Not authenticated

---

## Client (Advertiser)

All require login. After signup with `role: "client"`, call `POST /api/client/register` once to create Client record.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/client/register` | Register as client (create Client record) |
| GET | `/api/client/campaigns` | List my campaigns |
| POST | `/api/client/campaigns` | Create campaign |
| GET | `/api/client/campaigns/<id>` | Get campaign + stats |
| PUT | `/api/client/campaigns/<id>` | Update campaign |
| GET | `/api/client/dashboard` | Dashboard summary + campaigns |
| GET | `/api/client/dashboard/poll` | Lightweight poll for realtime |
| WS  | `dashboard_update` event | Realtime socket.io event; clients auto-join `client_<id>` room |

### POST /api/client/register

**Body:** `{ "company_name?", "website?", "industry?" }`

**Response 201:** `{ "message", "client": { "id", "company_name", "website" } }`

### POST /api/client/campaigns

**Body:** `{ "name", "offer_url" (or "target_url"), "budget?", "cost_per_click", "affiliate_cpc?" }`

**Response 201:** `{ "message", "campaign": { "id", "name", "offer_url", "cost_per_click", "affiliate_cpc", "budget", "status", "tracking_link_example" } }`

### GET /api/client/dashboard

**Response 200:** `{ "client", "summary": { "total_campaigns", "active_campaigns", "total_clicks", "total_spend" }, "campaigns": [...] }`

### GET /api/client/dashboard/poll

**Response 200:** `{ "ts", "summary": { ... }, "campaigns": [ { "id", "name", "status", "total_clicks", "total_spend" } ] }`

---

## Affiliate

All require login. Call `POST /api/affiliate/register` once to create Affiliate record.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/affiliate/register` | Register as affiliate |
| GET | `/api/affiliate/profile` | My profile |
| GET | `/api/affiliate/campaigns` | Available campaigns |
| POST | `/api/affiliate/campaigns/<id>/join` | Get tracking link for campaign |
| GET | `/api/affiliate/links/<campaign_id>` | Get my tracking link |
| GET | `/api/affiliate/earnings` | Earnings + valid_clicks |
| GET | `/api/affiliate/dashboard/poll` | Lightweight poll for realtime |
| WS  | `dashboard_update` event | Realtime socket.io event; clients auto-join `affiliate_<id>` room |

### GET /api/affiliate/links/<campaign_id>

**Response 200:** `{ "campaign_id", "tracking_url", "referral_code", "affiliate_cpc" }`  
Tracking URL format: `{origin}/t/{campaign_id}?aff={affiliate_id}`

### GET /api/affiliate/earnings

**Response 200:** `{ "earnings": { "total_earnings", "pending_payout", "valid_clicks", "total_leads", "converted_leads", "pending_leads", "commission_rate" } }`

### GET /api/affiliate/dashboard/poll

**Response 200:** `{ "ts", "valid_clicks", "total_earnings", "pending_payout", "commission_rate" }`

---

## Tracking (public, no auth)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/t/<campaign_id>?aff=<affiliate_id>` | Record click, redirect to offer URL |

---

## Demo (no auth)

| Method | Endpoint |
|--------|----------|
| GET | `/api/demo/dashboard/client` |
| GET | `/api/demo/dashboard/affiliate` |
| GET | `/api/demo/dashboard/client/poll` |
| GET | `/api/demo/dashboard/affiliate/poll` |
| GET | `/api/demo/stats` |
