from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)

    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024

    CORS(app, origins=["http://localhost:5173", "http://localhost:5000", "http://localhost", "http://127.0.0.1:5173", "http://127.0.0.1:5000", "http://127.0.0.1"])
   
    from .routes.project import project_bp
    from .routes.venv import venv_bp
    from .routes.fix import fix_bp
    from .routes.report import report_bp

    app.register_blueprint(project_bp)
    app.register_blueprint(venv_bp)
    app.register_blueprint(fix_bp)
    app.register_blueprint(report_bp)

    return app