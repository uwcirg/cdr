import os
env = os.environ

TESTDB_PATH = '/tmp/cdr_test.db'



class BaseConfig(object):
    PROJECT = "cdr"
    MONGODB_SETTINGS = {
        'db': 'cdr',
        'host': env.get('CDR_DB_1_PORT_27017_TCP_ADDR', 'localhost'),
        'port': 27017
    }

    # Get app root path, also can use flask.root_path.
    # ../../config.py
    PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    DEBUG = False
    TESTING = False

    ADMINS = ['pbugni@uw.edu']
    SECRET_KEY = 'override with a secret key'
    LOG_FOLDER = os.path.join('/tmp', 'logs')
    SQLALCHEMY_DATABASE_URI = (
        'postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}/{PGDATABASE}'.format(
            PGUSER=env.get('PGUSER'), PGPASSWORD=env.get('PGPASSWORD'),
            PGHOST=env.get('PGHOST', 'localhost'),
            PGDATABASE=env.get('PGDATABASE')))
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DefaultConfig(BaseConfig):
    DEBUG = True


class TestConfig(BaseConfig):
    TESTING = True

    TEST_DATABASE_URI = 'sqlite:///' + TESTDB_PATH
    SQLALCHEMY_DATABASE_URI = TEST_DATABASE_URI

    MONGODB_SETTINGS = {'DB': 'cdr_test'}
