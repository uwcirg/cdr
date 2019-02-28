import os

from flask import Flask, request

from .config import DefaultConfig
from .api import api
from .extensions import db


# For import *
__all__ = ['create_app']

DEFAULT_BLUEPRINTS = (
    api,
)


def create_app(config=None, app_name=None, blueprints=None):
    """Create a Flask app."""

    if app_name is None:
        app_name = DefaultConfig.PROJECT
    if blueprints is None:
        blueprints = DEFAULT_BLUEPRINTS

    app = Flask(app_name)
    configure_app(app, config)
    configure_hook(app)
    configure_blueprints(app, blueprints)
    configure_extensions(app)
    configure_logging(app)

    return app


def configure_app(app, config=None):
    """Different ways of configurations."""

    # http://flask.pocoo.org/docs/api/#configuration
    app.config.from_object(DefaultConfig)

    # http://flask.pocoo.org/docs/config/#instance-folders
    app.config.from_pyfile('production.cfg', silent=True)

    if config:
        app.config.from_object(config)


def configure_extensions(app):
    db.init_app(app)


def configure_blueprints(app, blueprints):
    """Configure blueprints in views."""

    for blueprint in blueprints:
        app.register_blueprint(blueprint)


def configure_logging(app):
    """Configure file(info) and email(error) logging."""

    if app.debug or app.testing:
        # Skip debug and test mode. Just check standard output.
        return
    else:  # pragma: no cover
        import logging
        from logging.handlers import SMTPHandler

        # Set info level on logger, which might be overwritten by handers.
        # Suppress DEBUG messages.
        app.logger.setLevel(logging.INFO)

        info_log = os.path.join(app.config['LOG_FOLDER'], 'info.log')
        info_file_handler = logging.handlers.RotatingFileHandler(info_log, maxBytes=100000, backupCount=10)
        info_file_handler.setLevel(logging.INFO)
        info_file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]')
        )
        app.logger.addHandler(info_file_handler)

        # Testing
        app.logger.info("testing info.")
        app.logger.warn("testing warn.")
        app.logger.error("testing error.")

        mail_handler = SMTPHandler(app.config['MAIL_SERVER'],
                                   app.config['MAIL_USERNAME'],
                                   app.config['ADMINS'],
                                   'O_ops... %s failed!' % app.config['PROJECT'],
                                   (app.config['MAIL_USERNAME'],
                                    app.config['MAIL_PASSWORD']))
        mail_handler.setLevel(logging.ERROR)
        mail_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]')
        )
        app.logger.addHandler(mail_handler)


def configure_hook(app):
    @app.before_request
    def before_request():
        """Set to True to see details of every call"""
        if False:  # pragma: no cover
            print("HEADERS", request.headers)
            print("REQ_path", request.path)
            print("ARGS", request.args)
            print("DATA", request.data)
            print("FORM", request.form)

