from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)

    CORS(app, origins=["http://localhost:5173"])
   
    from .routes.project import project_bp
    from .routes.venv import venv_bp

    app.register_blueprint(project_bp)
    app.register_blueprint(venv_bp)

    return app