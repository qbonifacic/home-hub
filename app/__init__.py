import os
import secrets

from flask import Flask
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address, default_limits=[])
csrf = CSRFProtect()


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'),
        static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'),
    )
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    limiter.init_app(app)
    csrf.init_app(app)

    @app.after_request
    def security_headers(resp):
        resp.headers['X-Frame-Options'] = 'DENY'
        resp.headers['X-Content-Type-Options'] = 'nosniff'
        return resp

    from .auth import auth_bp
    from .dashboard import dashboard_bp
    from .meals import meals_bp
    from .chores import chores_bp
    from .shopping import shopping_bp
    from .schedule import schedule_bp
    from .reminders import reminders_bp
    from .cards import cards_bp
    from .chat import chat_bp
    from .health import health_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(meals_bp)
    app.register_blueprint(chores_bp)
    app.register_blueprint(shopping_bp)
    app.register_blueprint(schedule_bp)
    app.register_blueprint(reminders_bp)
    app.register_blueprint(cards_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(health_bp)

    return app
