# Lead Gen Platform

Lead generation marketing platform built with Flask. Handles redirects, click tracking, and traffic validation.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the server:
   ```bash
   python backend/app.py
   ```

3. Access the dashboard at `http://localhost:5000`

## Architecture

- **Backend**: Flask application with modular routes and services (routes are auto‑discovered from the `backend/routes` package)
- **Database**: SQLAlchemy ORM with PostgreSQL support
- **Frontend**: Simple dashboard with real-time stats
- **Middleware**: Request logging and bot detection
- **Tracking service**: `services/tracker.py` validates clicks, enforces budgets, prevents duplicates, and updates payouts
- **Redirects**: `/r/<slug>` endpoint logs clicks, filters bots, persists events, and sends visitors to campaign URLs
  * passes affiliate id with `?aid=` query param, returns `X-Click-Status` header on duplicates

## Project Structure

```
backend/
  app.py                    # Application entry point
  routes/                   # API endpoints
  services/                 # Business logic layer
  database/                 # Models and DB setup
  middleware/               # Request interceptors
  utils/                    # Helper functions
frontend/                   # Frontend assets
tests/                      # Test suite
```

## Redirect Flow

1. Visitor hits `/r/<campaign-slug>`.
2. Middleware captures IP and user agent.
3. `traffic_filter` checks for bots or invalid traffic.
4. `tracker` service writes a click record to the database.
5. `redirect_engine` determines final target (currently campaign URL).
6. User is redirected with an HTTP 302 response.

## Deployment

Deploy to Render using the provided `render.yaml`
