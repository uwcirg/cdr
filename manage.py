import alembic.config
import click
from flask_migrate import Migrate
import json
import os

from cdr import create_app
from cdr.extensions import sdb

app = create_app()


MIGRATIONS_DIR = os.path.join(app.root_path, 'migrations')
migrate = Migrate(app, sdb, directory=MIGRATIONS_DIR)


def _run_alembic_command(args):
    """Helper to manage working directory and run given alembic commands"""
    # Alembic looks for the alembic.ini file in CWD
    # hop over there and then return to CWD
    cwd = os.getcwd()
    os.chdir(MIGRATIONS_DIR)

    alembic.config.main(argv=args)

    os.chdir(cwd)  # restore cwd


def stamp_db():
    """Run the alembic command to stamp the db with the current head"""
    # if the alembic_version table exists, this db has been stamped,
    # don't update to head, as it would potentially skip steps.
    if db.engine.dialect.has_table(db.engine.connect(), 'alembic_version'):
        return

    _run_alembic_command(['--raiseerr', 'stamp', 'head'])


@app.cli.command('initdb')
def initdb():
    """Initialize database (if necessary"""
    if not sdb.engine.dialect.has_table(sdb.engine.connect(), 'alembic_version'):
        sdb.create_all()


@click.option(
    '--config_key',
    '-c',
    help='Return a single config value, or empty string if value is None'
)
@app.cli.command()
def config(config_key):
    """List current flask configuration values in JSON"""

    if config_key:
        # Remap None values to an empty string
        print(app.config.get(config_key, '') or '')
        return
    print(json.dumps(
        # Skip un-serializable values
        {k: v for k, v in app.config.items() if isinstance(v, str)},
        indent=2,
    ))
