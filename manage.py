import os

from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand

from app.models import User
from app import create_app, db

app = create_app(os.getenv('MAINTRAQ_CONFIG') or 'production')
migrate = Migrate(app, db)
manager = Manager(app)


def make_shell_context():
    return dict(app=app, db=db, User=User)

manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def deploy():
    """Deployment tasks."""
    pass

if __name__ == '__main__':
    manager.run()
