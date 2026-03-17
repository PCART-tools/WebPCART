from flask import Flask
from flask_cors import CORS
import secrets
from flask.sessions import SecureCookieSessionInterface

def create_app():
    app = Flask(__name__)

    app.secret_key = secrets.token_hex(16)
    app.session_interface = SecureCookieSessionInterface()


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

    @app.before_request
    def ensure_user_id():
        from flask import session
        import uuid
        if 'user_id' not in session or not session['user_id']:
            session['user_id'] = str(uuid.uuid4())

    return app