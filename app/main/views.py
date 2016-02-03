from flask import render_template, url_for, redirect

from flask.ext.login import login_required, current_user

from app import db
from app.main import main
from app.models import Task

from app.main.forms import TaskRequestForm


@main.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if not (current_user.is_admin or current_user.is_maintenance):
        return redirect(url_for('main.task_request'))
    tasks = []
    if current_user.is_admin:
        tasks = Task.query.order_by(Task.date_requested.desc()).all()
        return render_template('main/index.html', tasks=tasks, tasks_info={})
    elif current_user.is_maintenance:
        assigned = current_user.assigned.all()
        return render_template('main/index.html', tasks=assigned)


@main.route('/task-requests', methods=['GET', 'POST'])
@login_required
def task_request():
    form = TaskRequestForm()
    if form.validate_on_submit():
        task = Task(
            requested_by_id=current_user.id,
            facility_id=form.facility.data,
            description=form.description.data,
            detailed_info=form.detailed_info.data
        )
        db.session.add(task)
        return redirect(url_for('main.index'))
    return render_template('main/task-request.html', form=form)


@main.route('/view-task/<int:task_id>')
@login_required
def view_task(task_id):
    task = Task.query.get_or_404(task_id)

    return render_template('main/task-detail.html', task=task)
