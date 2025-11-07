from typing import Optional, Dict, Any
from flask import Flask, jsonify
from .config import Config
from .logger import setup_logging
from .db import init_engine, get_session_factory
from .exceptions import register_exception_handlers
from .routes import accounts_bp


def create_app(config: Optional[Dict[str, Any]] = None) -> Flask:
    
    cfg = Config()
    if config:
        cfg.from_mapping(config)

    setup_logging(cfg)

    engine = init_engine(cfg.SQLALCHEMY_DATABASE_URI, echo=cfg.SQLALCHEMY_ECHO)

    from . import models
    models.Base.metadata.create_all(bind=engine)

    app = Flask(__name__)
    app.config.from_mapping(cfg.as_dict())

    app.session_factory = get_session_factory(engine)

    app.register_blueprint(accounts_bp, url_prefix="/api/v1")

    register_exception_handlers(app)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app
