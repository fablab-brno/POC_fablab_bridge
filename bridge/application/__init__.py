from pathlib import Path
import os
from flask import Flask
from flask_cors import CORS

from .services.extensions import swagger


def create_app() -> Flask:
    """Create application factory
    """
    app = Flask("classmarker_fabman_bridge", template_folder=Path(os.getcwd(), "templates"))
    app.config.from_object("application.configs.flask_config_file")

    CORS(app)

    register_extensions(app)
    register_blueprints(app)

    return app


def register_extensions(app: Flask) -> None:
    """Register Flask extensions."""
    # mail.init_app(app)
    swagger.init_app(app)

    return None


def register_blueprints(app: Flask) -> None:
    """Register Flask api."""
    from application.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return None
