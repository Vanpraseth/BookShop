import os
import secrets
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from config import (
    MAX_CONTENT_LENGTH_BYTES,
    SERVER_HOST,
    SERVER_PORT,
    TOKEN_MAX_AGE_SECONDS,
    public_config,
)
from db import initialize_database
from routes.routes import ALL_BLUEPRINTS
from utils.errors import StockError, ValidationError

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_FRONTEND_DIR = _PROJECT_ROOT / "frontend"


def _enabled(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _cors_origins():
    configured = os.environ.get("CORS_ORIGINS", "")
    if configured.strip():
        return [origin.strip() for origin in configured.split(",") if origin.strip()]
    return []


def create_app():
    app = Flask(__name__, static_folder=str(_FRONTEND_DIR), static_url_path="")
    environment = os.environ.get("APP_ENV", "development").strip().lower()
    configured_secret = os.environ.get("SECRET_KEY")
    if environment == "production" and not configured_secret:
        raise RuntimeError("SECRET_KEY is required when APP_ENV=production.")

    app.config.update(
        SECRET_KEY=configured_secret or secrets.token_hex(32),
        TOKEN_MAX_AGE=TOKEN_MAX_AGE_SECONDS,
        MAX_CONTENT_LENGTH=MAX_CONTENT_LENGTH_BYTES,
        JSON_SORT_KEYS=False,
    )

    if _enabled("TRUST_PROXY"):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    cors_origins = _cors_origins()
    if cors_origins:
        CORS(app, resources={r"/api/*": {"origins": cors_origins}})
    initialize_database()

    @app.errorhandler(ValidationError)
    def _handle_validation(e):
        return jsonify({"error": str(e)}), 400

    @app.errorhandler(StockError)
    def _handle_stock(e):
        return jsonify({"error": str(e)}), 409

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.get("/api/config")
    def application_config():
        return jsonify(public_config()), 200

    @app.get("/")
    def frontend_index():
        return send_from_directory(_FRONTEND_DIR, "index.html")

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
        )
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
            "base-uri 'self'; form-action 'self'; frame-ancestors 'none'",
        )
        if request.path.startswith("/api/"):
            response.headers.setdefault("Cache-Control", "no-store")
        return response

    for bp in ALL_BLUEPRINTS:
        app.register_blueprint(bp)

    return app


app = create_app()


if __name__ == "__main__":
    debug = _enabled("FLASK_DEBUG") and os.environ.get("APP_ENV") != "production"
    app.run(
        debug=debug,
        host=SERVER_HOST,
        port=SERVER_PORT,
    )
