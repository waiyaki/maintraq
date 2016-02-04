from flask import render_template, url_for, redirect, abort, flash, request, current_app

from flask.ext.login import login_required, current_user

from app import db
from app.main import main
from app.models import Task, User, TaskStatus
from app.utils import send_email

from app.main.forms import (
    TaskRequestForm, MaintainerTaskUpdateForm, AdminTaskUpdateForm, RejectTaskForm
)


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
        # Notify admin
        admin = User.query.filter_by(email=current_app.config['MAINTRAQ_ADMIN']).first()
        send_mail(task, created=True, user=admin)
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
            if task.assigned_to_id:
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
            # Cache state before, will need it to send emails.
            assigned_to = task.assigned_to_id
            resolved = task.resolved
            done = task.progress
            confirmed = task.confirmed
            # Update data contained within specific fields according to user rights.
            if current_user.is_admin:
                task.acknowledged = form.acknowledged.data
                task.confirmed = form.confirmed.data
                task.assigned_to_id = form.assigned_to_id.data
                task.progress = form.progress.data
                task.facility_id = form.facility.data
                task.resolved = form.resolved.data
                task.progress = form.progress.data
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

            # Resolve what emails to send, if any.
            if assigned_to != task.assigned_to_id:
                # Notify the new assigned staff of the assignment.
                send_mail(task, assigned=True)
            if not resolved and task.resolved:
                # If this was just marked as resolved by admin, inform the user.
                send_mail(task, resolved=True)
            if done != task.progress and task.progress == TaskStatus.DONE:
                # If a maintainer just completed a task, notify the admin.
                # Don't notify though, if the admin's responsible for the update.
                if not current_user.is_admin:
                    admin = User.query.filter_by(email=current_app.config['MAINTRAQ_ADMIN']).first()
                    send_mail(task, done=True, user=admin, updated_by=current_user)

            if not confirmed and task.confirmed:
                send_mail(task, confirmed=True)
            return redirect(url_for('main.view_task', task_id=task.id))
        else:
            flash("Your form has some errors. Please correct them and try again.")

    return render_template('main/task-update.html', task=task, form=form)


@main.route('/tasks/reject/<int:task_id>', methods=['GET', 'POST'])
@login_required
def reject_task(task_id):
    if not current_user.is_admin:
        abort(403)
    task = Task.query.get_or_404(task_id)
    form = RejectTaskForm()

    if request.method == 'POST':
        temp = {
            'description': task.description,
            'date_requested': task.date_requested,
            'facility': task.facility,
            'requested_by': task.requested_by.email,
            'requested_by_name': task.requested_by.username,
            'reasons': form.rejection_reasons.data
        }
        db.session.delete(task)
        db.session.commit()
        send_mail(task=temp, rejected=True)
        return redirect(url_for('main.index'))
    return render_template('main/task-reject.html', task=task, form=form)


def send_mail(
        task, assigned=False, created=False, user=None,
        resolved=False, done=False, rejected=False, confirmed=False, **kwargs):
    if assigned:
        # Notify whoever was assigned via email
        send_email(
            task.assigned_to.email,
            "New Maintenance Task Assignment",
            'main/email/new-assignment',
            task=task
        )
    elif created:
        # Notify the admin of the new task.
        send_email(
            current_app.config['MAINTRAQ_ADMIN'],
            "New Maintenance Request",
            "main/email/new-task-request",
            task=task, user=user
        )
    elif resolved:
        send_email(
            task.requested_by.email,
            "Maintenance Request Resolved",
            "main/email/resolved",
            task=task
        )
    elif done:
        send_email(
            current_app.config['MAINTRAQ_ADMIN'],
            "Newly Completed Maintenance Task",
            "main/email/task-complete",
            task=task, user=user, **kwargs
        )
    elif rejected:
        send_email(
            task['requested_by'],
            "Maintenance Request Rejected",
            "main/email/task-rejected",
            task=task
        )
    elif confirmed:
        send_email(
            task.requested_by.email,
            "Maintenance Request Confirmed",
            "main/email/task-confirmed",
            task=task
        )
