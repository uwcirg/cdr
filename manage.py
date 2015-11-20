from flask.ext.script import Manager

from cdr import create_app


app = create_app()
manager = Manager(app)


@manager.command
def run():
    """Run in local machine."""
    app.run(threaded=True)


manager.add_option('-c', '--config',
                   dest="config",
                   required=False,
                   help="config file")


if __name__ == "__main__":
    manager.run()
