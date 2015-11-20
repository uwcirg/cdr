import os


class BaseConfig(object):
    PROJECT = "cdr"
    MONGODB_SETTINGS = {'DB': 'cdr'}

    # Get app root path, also can use flask.root_path.
    # ../../config.py
    PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    DEBUG = False
    TESTING = False

    ADMINS = ['pbugni@uw.edu']
    SECRET_KEY = 'override with a secret key'
    LOG_FOLDER = os.path.join('/tmp', 'logs')


class DefaultConfig(BaseConfig):
    DEBUG = True


class TestConfig(BaseConfig):
    TESTING = True
    MONGODB_SETTINGS = {'DB': 'cdr_test'}
