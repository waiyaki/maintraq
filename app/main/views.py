from flask import render_template, url_for, redirect, abort, flash, request

from flask.ext.login import login_required, current_user

from app import db
from app.main import main
from app.models import Task

from app.main.forms import TaskRequestForm, MaintainerTaskUpdateForm, AdminTaskUpdateForm


@main.route('/', methods=['GET', 'POST'])
@login_required
def index():
    tasks = []
    if current_user.is_admin:
        tasks = Task.query.order_by(Task.date_requested.desc()).all()
        return render_template('main/index.html', tasks=tasks, tasks_info={})
    elif current_user.is_maintenance:
        assigned = current_user.assigned.all()
        return render_template('main/index.html', tasks=assigned)
    else:
        tasks = current_user.tasks.filter_by(
            confirmed=False).order_by(Task.date_requested.desc()).all()
        return render_template('main/index.html', tasks=tasks)


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
        db.session.commit()     # Commit here to get access to task id
        return redirect(url_for('main.view_task', task_id=task.id))
    return render_template('main/task-request.html', form=form)


@main.route('/view-task/<int:task_id>')
@login_required
def view_task(task_id):
    task = Task.query.get_or_404(task_id)
    if not (current_user.is_admin or current_user.is_maintenance):
        if task.requested_by_id != current_user.id:
            abort(403)
    return render_template('main/task-detail.html', task=task)


@main.route('/update-task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    # Should we do this? Let's find out.
    if not (current_user.is_admin or current_user.is_maintenance):
        if task.requested_by_id != current_user.id:
            abort(403)
        if current_user.is_maintenance and task.assigned_to_id != current_user.id:
            abort(403)

    # Get the appropriate form for this user.
    if current_user.is_admin:
        form = AdminTaskUpdateForm()
    elif current_user.is_maintenance:
        form = MaintainerTaskUpdateForm()
    else:
        form = TaskRequestForm()

    if request.method == "GET":
        # Prepopulate the form fields with the correct data for a GET request.
        if current_user.is_admin:
            form.acknowledged.data = task.acknowledged
            form.confirmed.data = task.confirmed
            form.assigned_to_id.data = task.assigned_to_id
            form.progress.data = task.progress
        elif current_user.is_maintenance:
            form.acknowledged.data = task.acknowledged
            form.progress.data = task.progress
        # Define form fields common to all forms.
        form.description.data = task.description
        form.detailed_info.data = task.detailed_info
        form.facility.data = task.facility.id

    elif request.method == "POST":
        if form.validate_on_submit():
            # Update data contained within specific fields according to user rights.
            if current_user.is_admin:
                task.acknowledged = form.acknowledged.data
                task.confirmed = form.confirmed.data
                task.assigned_to_id = form.assigned_to_id.data
                task.progress = form.progress.data
                task.facility_id = form.facility.data
            elif current_user.is_maintenance:
                if not form.acknowledged.data and form.progress.data != task.progress:
                    # This guy updated progess but did not acknowledge receipt.
                    # Let's kindly do that for them.
                    form.acknowledged.data = True
                task.acknowledged = form.acknowledged.data
                task.progress = form.progress.data
            # Common fields
            task.description = form.description.data
            task.detailed_info = form.detailed_info.data
            db.session.add(task)
            db.session.commit()
            flash("Task update successful.")
            return redirect(url_for('main.view_task', task_id=task.id))
        else:
            flash("Your form has some errors. Please correct them and try again.")

    return render_template('main/task-update.html', task=task, form=form)
