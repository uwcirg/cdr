from flask_script import Manager

from cdr import create_app


app = create_app()
manager = Manager(app)


@manager.command
def run():
    """Run in local machine."""
    app.run(host='0.0.0.0', threaded=True)


if __name__ == "__main__":
    manager.run()
