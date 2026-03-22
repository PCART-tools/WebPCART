from flask import Flask
from flask_cors import CORS
import secrets
import os
from flask.sessions import SecureCookieSessionInterface

def create_app():
    app = Flask(__name__)

    # 设置secret key
    if os.environ.get('FLASK_ENV') == 'production':
        app.secret_key = os.environ.get('FLASK_SECRET_KEY')
        if not app.secret_key:
            raise ValueError("FLASK_SECRET_KEY environment variable is required in production")
    else:
        app.secret_key = 'webpcart-fixed-secret-key-for-development'
    
    # 配置session cookie
    if os.environ.get('FLASK_ENV') == 'production':
        app.config.update(
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE='None', 
            SESSION_COOKIE_SECURE=True,      
            SESSION_COOKIE_PATH='/',
        )
    else:
        app.config.update(
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE='Lax',
            SESSION_COOKIE_SECURE=False,
            SESSION_COOKIE_PATH='/',
        )

    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024

    CORS(app,
        origins=["http://localhost:5173", "http://localhost:5000", "http://localhost:8080", "http://localhost", "http://127.0.0.1:5173", "http://127.0.0.1:5000", "http://127.0.0.1:8080", "http://127.0.0.1"],
        supports_credentials=True)
   
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
        from flask import session, request
        import uuid
        
        print(f"=== SESSION DEBUG ===")
        print(f"Request URL: {request.url}")
        print(f"Request cookies: {dict(request.cookies)}")
        
        # 尝试手动解析 session
        try:
            session_data = dict(session)
            print(f"Session data: {session_data}")
            if 'user_id' in session_data:
                print(f"Existing user_id: {session_data['user_id']}")
            else:
                new_id = str(uuid.uuid4())
                session['user_id'] = new_id
                print(f"New user_id generated: {new_id}")
        except Exception as e:
            print(f"Session parsing error: {e}")
            print(f"Clearing invalid session and generating new user_id")
            session.clear()
            new_id = str(uuid.uuid4())
            session['user_id'] = new_id
            print(f"New user_id after error: {new_id}")

    return app