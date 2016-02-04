from flask.ext.wtf import Form

from wtforms import SubmitField, SelectField, StringField, TextAreaField, BooleanField
from wtforms.validators import Required, Length, ValidationError
from wtforms_components import read_only

from app.models import Facility, User, TaskStatus


class CommonTaskDetailsForm(Form):
    description = StringField("Description", validators=[Required(), Length(10, 255)])
    detailed_info = TextAreaField("Detailed Information")
    facility = SelectField("Facility", coerce=int)

    def __init__(self, *args, **kwargs):
        super(CommonTaskDetailsForm, self).__init__(*args, **kwargs)
        self.facility.choices = [
            (fac.id, fac.name) for fac in Facility.query.order_by(Facility.name).all()
        ]


class TaskRequestForm(CommonTaskDetailsForm):
    submit = SubmitField("Submit")

    def __init__(self, *args, **kwargs):
        super(TaskRequestForm, self).__init__(*args, **kwargs)


class MaintainerTaskUpdateForm(CommonTaskDetailsForm):
    acknowledged = BooleanField("Acknowledge Task Assignment Received")
    progress = SelectField('Task Status', coerce=int)
    submit = SubmitField("Update")

    def __init__(self, *args, **kwargs):
        super(MaintainerTaskUpdateForm, self).__init__(*args, **kwargs)
        self.progress.choices = [
            (TaskStatus.NOT_STARTED, "Not Started"),
            (TaskStatus.STARTED, "Started"),
            (TaskStatus.PENDING, "In Progress"),
            (TaskStatus.DONE, "Done")
        ]
        read_only(self.facility)
        read_only(self.description)
        read_only(self.detailed_info)


class AdminTaskUpdateForm(CommonTaskDetailsForm):
    confirmed = BooleanField("Confirm Task Request")
    assigned_to_id = SelectField("Assigned To", coerce=int)
    acknowledged = BooleanField("Acknowledge Receipt by Assignee")
    progress = SelectField("Task Status", coerce=int)
    resolved = BooleanField("Resolved")
    submit = SubmitField("Update")

    def __init__(self, *args, **kwargs):
        super(AdminTaskUpdateForm, self).__init__(*args, **kwargs)
        self.assigned_to_id.choices = [
            (u.id, u.username) for u in User.query.filter_by(
                is_maintenance=True).order_by(User.username).all()
        ]
        self.progress.choices = [
            (TaskStatus.NOT_STARTED, "Not Started"),
            (TaskStatus.STARTED, "Started"),
            (TaskStatus.PENDING, "In Progress"),
            (TaskStatus.DONE, "Done")
        ]

    def validate_assigned_to_id(self, field):
        id = field.data
        if not User.query.filter_by(id=int(id), is_maintenance=True).first():
            raise ValidationError("Selected choice is not a valid user.")


class RejectTaskForm(Form):
    rejection_reasons = TextAreaField("Comments about this rejection.")
