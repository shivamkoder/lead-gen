import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from backend.app.extensions import db, migrate, login_manager, cors, socketio


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), 'backend', 'app', 'templates'),
        static_folder=os.path.join(os.path.dirname(__file__), 'backend', 'app', 'static')
    )

    flask_env = os.getenv('FLASK_ENV', 'development')
    is_production = flask_env == 'production'

    # ── Secret Key ────────────────────────────────────────────────────────────
    secret_key = os.getenv('SECRET_KEY')
    if not secret_key:
        if is_production:
            raise RuntimeError(
                "FATAL: SECRET_KEY is not set. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        import warnings
        warnings.warn("SECRET_KEY not set — using insecure dev default.", stacklevel=2)
        secret_key = 'dev-insecure-secret-do-not-use-in-production'
    app.config['SECRET_KEY'] = secret_key

    # ── Database URL (fix Render postgres:// → postgresql://) ─────────────────
    db_url = os.getenv('DATABASE_URL', 'sqlite:///dev.db')
    if db_url.startswith('postgres://'):
        db_url = 'postgresql://' + db_url[len('postgres://'):]
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ── Session / Cookie ──────────────────────────────────────────────────────
    app.config['SESSION_COOKIE_SECURE']   = is_production
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    # Only set SESSION_COOKIE_DOMAIN when explicitly configured (avoids breaking localhost)
    cookie_domain = os.getenv('SESSION_COOKIE_DOMAIN')
    if cookie_domain:
        app.config['SESSION_COOKIE_DOMAIN'] = cookie_domain

    # ── Password reset TTL ────────────────────────────────────────────────────
    app.config['PASSWORD_RESET_SALT']    = 'password-reset-salt'
    app.config['PASSWORD_RESET_MAX_AGE'] = int(os.getenv('PASSWORD_RESET_MAX_AGE', 3600))

    # ── CORS — locked to ALLOWED_ORIGINS in production ────────────────────────
    # Dev default: permissive localhost.  Production: set ALLOWED_ORIGINS env var.
    # e.g.  ALLOWED_ORIGINS=https://yourapp.com,https://www.yourapp.com
    raw_origins = os.getenv('ALLOWED_ORIGINS', '')
    if raw_origins:
        allowed_origins = [o.strip() for o in raw_origins.split(',') if o.strip()]
    elif is_production:
        allowed_origins = []   # blocks all cross-origin; same-origin frontend still works
        import warnings
        warnings.warn(
            "ALLOWED_ORIGINS is not set in production. Cross-origin API requests will be "
            "blocked. Set ALLOWED_ORIGINS=https://yourdomain.com to allow your frontend.",
            stacklevel=2
        )
    else:
        allowed_origins = [
            'http://localhost:3000', 'http://localhost:5000',
            'http://127.0.0.1:5000', 'http://127.0.0.1:3000',
        ]

    # ── Rate Limiter ──────────────────────────────────────────────────────────
    # Redis in production (set REDIS_URL); in-memory fallback for dev/single-worker.
    # Warning: memory:// is per-process — won't share across Gunicorn workers.
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    redis_url = os.getenv('REDIS_URL')
    if is_production and not redis_url:
        import warnings
        warnings.warn(
            "REDIS_URL is not set. Rate limiting uses in-memory storage, which is "
            "not shared across Gunicorn workers. Add Redis and set REDIS_URL.",
            stacklevel=2
        )

    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["500 per day", "100 per hour"],
        storage_uri=redis_url if redis_url else 'memory://',
    )
    # Expose limiter so blueprints can add custom limits: @limiter.limit("10/minute")
    app.extensions['limiter'] = limiter

    # ── Init extensions ───────────────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    cors_origins = allowed_origins if allowed_origins else "*"
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": cors_origins,
            "supports_credentials": True,   # required for session cookies cross-origin
        }
    })
    socketio.init_app(app, cors_allowed_origins=cors_origins)

    # ── Register blueprints ───────────────────────────────────────────────────
    from backend.app.routes.pages     import pages_bp
    from backend.app.routes.auth      import auth_bp
    from backend.app.routes.admin     import admin_bp
    from backend.app.routes.affiliate import affiliate_bp
    from backend.app.routes.client    import client_bp
    from backend.app.routes.tracking  import tracking_bp
    from backend.app.routes.demo      import demo_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp,      url_prefix='/api/auth')
    app.register_blueprint(admin_bp,     url_prefix='/api/admin')
    app.register_blueprint(affiliate_bp, url_prefix='/api/affiliate')
    app.register_blueprint(client_bp,    url_prefix='/api/client')
    app.register_blueprint(tracking_bp)
    app.register_blueprint(demo_bp,      url_prefix='/api/demo')

    @app.route('/health')
    def health():
        return {"status": "ok"}, 200

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
