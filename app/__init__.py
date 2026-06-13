import logging
import os
from flask import Flask, jsonify
from app.config import config
from app.extensions import db, migrate, jwt, cors


def create_app(config_name: str = None) -> Flask:
    config_name = config_name or os.getenv("FLASK_ENV", "development")
    cfg = config.get(config_name, config["default"])

    # Validate critical secrets before the app starts
    cfg.validate()

    app = Flask(__name__)
    app.config.from_object(cfg)

    _setup_logging(app)
    _init_extensions(app)
    _register_blueprints(app)
    _load_ml_model(app)
    _register_error_handlers(app)

    return app


def _setup_logging(app: Flask):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def _init_extensions(app: Flask):
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    allowed = app.config.get("ALLOWED_ORIGINS", ["*"])
    cors.init_app(app, resources={r"/api/*": {"origins": allowed}})

    with app.app_context():
        from app.models import user, patient, prediction, chat_message  # noqa: F401
        db.create_all()


def _register_blueprints(app: Flask):
    from app.routes.auth_routes import auth_bp
    from app.routes.patient_routes import patient_bp
    from app.routes.prediction_routes import prediction_bp
    from app.routes.chat_routes import chat_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(chat_bp)


def _load_ml_model(app: Flask):
    from app.services import ml_service
    model_path = app.config.get("MODEL_PATH", "model.pkl")
    try:
        ml_service.load_model(model_path)
    except Exception as exc:
        app.logger.error(f"[startup] Could not load ML model: {exc}")


def _register_error_handlers(app: Flask):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"success": False, "message": "Bad request.", "error": str(e)}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"success": False, "message": "Unauthorized."}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"success": False, "message": "Forbidden."}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "message": "Resource not found."}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"success": False, "message": "Internal server error."}), 500

    @jwt.unauthorized_loader
    def missing_token(reason):
        return jsonify({"success": False, "message": f"Missing token: {reason}"}), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return jsonify({"success": False, "message": f"Invalid token: {reason}"}), 422

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_data):
        return jsonify({"success": False, "message": "Token has expired."}), 401
