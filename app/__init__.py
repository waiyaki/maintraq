from flask import Flask

from flask.ext.mail import Mail
from flask.ext.moment import Moment
from flask.ext.login import LoginManager
from flask.ext.bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy

from config import config


mail = Mail()
db = SQLAlchemy()
moment = Moment()
bootstrap = Bootstrap()
login_manager = LoginManager()

# inform your login manager where the login view is located else @login_required
# will not be able to locate it.
login_manager.login_view = 'auth.login'

# Keep track of clients IP address and browser, log out if they change.
login_manager.session_protection = 'strong'


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    config[config_name].init_app(app)

    db.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    bootstrap.init_app(app)
    login_manager.init_app(app)

    from .main import main as main_blueprint
    from .auth import auth as auth_blueprint
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)

    return app
