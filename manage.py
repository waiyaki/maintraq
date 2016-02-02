import os

from flask.ext.script import Manager

from app import create_app

app = create_app(os.getenv('MAINTRAQ_CONFIG') or 'production')
manager = Manager(app)


@manager.command
def deploy():
    """Deployment tasks."""
    pass

if __name__ == '__main__':
    manager.run()
