from flask import render_template

from flask.ext.login import login_required, current_user

from app.main import main
from app.models import Task


@main.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if current_user.is_admin:
        tasks = Task.query.order_by(Task.date_requested.desc()).all()
    elif current_user.is_maintenance:
        tasks = Task.query.filter_by(user=current_user).all()
    return render_template('main/index.html', tasks=tasks)
