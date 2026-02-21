from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)


def create_app(config_name="default"):
    app = Flask(__name__)

    # ── Config ─────────────────────────────────────────────────────────────
    from app.config import config
    app.config.from_object(config[config_name])

    # ── Extensions ─────────────────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    CORS(app, origins=app.config["CORS_ORIGINS"], supports_credentials=True)

    # ── JWT Callbacks ───────────────────────────────────────────────────────
    from app.utils.jwt_callbacks import register_jwt_callbacks
    register_jwt_callbacks(jwt)

    # ── Blueprints ──────────────────────────────────────────────────────────
    from app.api.auth        import auth_bp
    from app.api.dashboard   import dashboard_bp
    from app.api.vehicles    import vehicles_bp
    from app.api.drivers     import drivers_bp
    from app.api.trips       import trips_bp
    from app.api.maintenance import maintenance_bp
    from app.api.expenses    import expenses_bp
    from app.api.analytics   import analytics_bp
    from app.api.ai          import ai_bp

    prefix = "/api/v1"
    app.register_blueprint(auth_bp,        url_prefix=f"{prefix}/auth")
    app.register_blueprint(dashboard_bp,   url_prefix=f"{prefix}/dashboard")
    app.register_blueprint(vehicles_bp,    url_prefix=f"{prefix}/vehicles")
    app.register_blueprint(drivers_bp,     url_prefix=f"{prefix}/drivers")
    app.register_blueprint(trips_bp,       url_prefix=f"{prefix}/trips")
    app.register_blueprint(maintenance_bp, url_prefix=f"{prefix}/maintenance")
    app.register_blueprint(expenses_bp,    url_prefix=f"{prefix}/expenses")
    app.register_blueprint(analytics_bp,   url_prefix=f"{prefix}/analytics")
    app.register_blueprint(ai_bp,          url_prefix=f"{prefix}/ai")

    # ── Health Check ────────────────────────────────────────────────────────
    @app.get("/health")
    def health():
        return {"status": "ok", "version": "1.0.0"}

    return app
