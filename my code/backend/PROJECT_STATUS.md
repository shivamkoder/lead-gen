# PPC Affiliate Platform — Project Status

**Last updated:** Status overview for deployability, completeness, and missing pieces.

---

## Is it deployable?

**Yes, with a few steps.** The backend is deployable to **Render** (or any host with PostgreSQL + Python). You must:

1. Set environment variables (see **Deployment checklist** below).
2. Run database migrations (or use a fresh DB so `db.create_all()` creates tables).
3. Optionally wire your frontend to the API (current HTML pages do **not** call the backend yet).

---

## What’s complete

### Backend (Flask API)

| Area | Status | Notes |
|------|--------|--------|
| **Auth** | Done | Register, login, logout, `/me`; session-based (Flask-Login). |
| **Roles** | Done | `user`, `client`, `affiliate`, `admin` in User model. |
| **Client (advertiser)** | Done | Register as client, CRUD campaigns, dashboard, dashboard poll. |
| **Affiliate** | Done | Register, profile, list/join campaigns, tracking link, earnings, payouts, dashboard poll. |
| **PPC tracking** | Done | `GET /t/<campaign_id>?aff=<affiliate_id>` — validate click, record, redirect, update spend/earnings. |
| **Click validation** | Done | Bot filter (User-Agent), duplicate filter (same fingerprint in 60 min). |
| **Models** | Done | User, Client, Affiliate, Campaign, Click, Lead, Conversion, Payout, Analytics. |
| **Admin** | Done | Dashboard, users, campaigns, leads, payouts, analytics (legacy lead/conversion). |
| **Demo (no auth)** | Done | Fake client/affiliate dashboards and stats + poll endpoints. |
| **Realtime polling** | Done | `/api/client/dashboard/poll`, `/api/affiliate/dashboard/poll` + `static/js/polling.js`. |
| **Procfile** | Done | `web: gunicorn run:app` for Render. |
| **CORS** | Done | Enabled for `/api/*` (origins `*`). |

### Frontend (current state)

| Item | Status | Notes |
|------|--------|--------|
| **Landing / marketing pages** | Partial | Root has `index.html`, `signup.html`, `login.html`, etc., but they are **not** the PPC product (e.g. “Multi-Tab Redirect”, “LeadFlow”). |
| **API integration** | Missing | No HTML file uses `fetch()` to call `/api/auth`, `/api/client`, or `/api/affiliate`. Forms do not POST to the Flask API. |
| **Client dashboard UI** | Missing | No HTML page that shows campaigns, clicks, spend and uses `/api/client/dashboard` or poll. |
| **Affiliate dashboard UI** | Missing | No HTML page that shows earnings, links, and uses `/api/affiliate` or poll. |
| **Static assets** | Backend only | `backend/static/js/polling.js` exists; no shared or frontend-specific structure. |

---

## What’s missing or incomplete

### 1. Frontend ↔ backend wiring

- **Signup / login:** Existing `signup.html` and `login.html` do **not** send requests to `POST /api/auth/register` or `POST /api/auth/login`. You need to add JS that submits to the API and stores or uses the session (e.g. cookie).
- **Dashboards:** No pages that call `/api/client/dashboard`, `/api/affiliate/earnings`, or the poll endpoints. You need at least:
  - **Client dashboard:** Page that lists campaigns and shows clicks/spend (and optionally uses `polling.js` on `/api/client/dashboard/poll`).
  - **Affiliate dashboard:** Page that shows earnings, valid clicks, and tracking links (and optionally uses `polling.js` on `/api/affiliate/dashboard/poll`).
- **Role choice:** Signup does not set `role` to `client` or `affiliate`; the API accepts `role` in `POST /api/auth/register`. You may want a post-login “become client” / “become affiliate” flow and call `POST /api/client/register` or `POST /api/affiliate/register`.

### 2. Database migrations

- **Migrations folder:** Only `migrations/__init__.py` exists; no migration scripts.
- **Effect:** On a **new** database, `db.create_all()` in `create_app()` creates all tables, including the new `Click` and new Campaign columns. On an **existing** DB, you must run:
  - `flask db migrate -m "Add Click and PPC fields"`
  - `flask db upgrade`
- **Recommendation:** Run `flask db init` (if not already), then `migrate` + `upgrade` before or right after first deploy.

### 3. Deployment / production details

- **DATABASE_URL:** On Render, the URL may use the `postgres://` scheme. SQLAlchemy 2 expects `postgresql://`. You may need to rewrite it in code or set `DATABASE_URL` to `postgresql://...` in the Render dashboard.
- **SECRET_KEY:** Must be set in production (e.g. `SECRET_KEY`, `JWT_SECRET_KEY`).
- **Session cookies:** If the frontend is on a different subdomain, you may need to set `SESSION_COOKIE_DOMAIN` and `SESSION_COOKIE_SAMESITE` (e.g. `Lax`) so the browser sends cookies to the API.
- **Build command:** On Render, use something like: `pip install -r requirements.txt` (no frontend build if you serve static HTML elsewhere).

### 4. Optional / nice-to-have

- **Password reset:** Auth has placeholder routes; no real email or token flow.
- **Email verification:** Not implemented.
- **Rate limiting:** Decorator exists but is a no-op; no Redis/in-memory limit.
- **Stricter fraud:** No VPN/proxy check, no per-IP rate limit on `/t/`.
- **JWT for SPA:** If you later use a separate SPA (different origin), you may want JWT instead of (or in addition to) session cookies.

---

## Deployment checklist (e.g. Render)

1. **Repo:** Backend code in Git; connect Render to the repo (e.g. `backend/` as root or set root to repo root and start command from `backend/`).
2. **Environment variables:**
   - `FLASK_ENV=production`
   - `SECRET_KEY=<strong random secret>`
   - `DATABASE_URL=postgresql://...` (Render provides this; fix scheme if it gives `postgres://`)
   - Optional: `JWT_SECRET_KEY`, `HOST`, `PORT`, `DEBUG=False`
3. **Build:** `pip install -r requirements.txt` (from directory that contains `requirements.txt`).
4. **Start:** From Procfile: `gunicorn run:app` (run from directory containing `run.py` and `app` package).
5. **Database:** Create a PostgreSQL DB on Render; run migrations once (e.g. `flask db upgrade`) or rely on `db.create_all()` on first request if DB is empty.
6. **Static files:** Flask serves `static/` (e.g. `polling.js`). If the frontend is a separate site, point it at the deployed API base URL for all `/api/*` and `/t/*` calls.

---

## Summary

| Question | Answer |
|----------|--------|
| **Backend feature-complete for PPC?** | Yes: tracking, clicks, campaigns, client/affiliate flows, polling, demo. |
| **Frontend integrated with API?** | No. HTML pages exist but do not call the backend. |
| **Deployable as API-only?** | Yes. Set env vars, run migrations (or use fresh DB), deploy with gunicorn. |
| **Ready for real users end-to-end?** | After you add: (1) frontend that uses auth + client/affiliate APIs, and (2) production env + DB migrations. |

So: **the backend is in good shape and deployable.** To have a fully working product, add frontend pages that call the API (signup, login, client dashboard, affiliate dashboard) and complete the deployment checklist above.
