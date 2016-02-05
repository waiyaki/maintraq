from flask import flash
from flask.ext.wtf import Form

from wtforms import SubmitField, SelectField, StringField, TextAreaField, BooleanField, HiddenField
from wtforms.validators import Required, Length, ValidationError, Regexp, Email
from wtforms_components import read_only
import phonenumbers
from phonenumbers import phonenumberutil
from phonenumbers import carrier

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
        if not User.query.filter_by(id=id, is_maintenance=True).first():
            flash("No user has been assigned to this task.")


class RejectTaskForm(Form):
    rejection_reasons = TextAreaField("Comments about this rejection.")


class FacilityForm(Form):
    name = StringField("Facility Name", validators=[Required()])
    submit = SubmitField("Create")

    def validate_name(self, field):
        if Facility.query.filter_by(name=field.data).first():
            raise ValidationError("This Facility exists.")


class EditProfileAdminForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64), Email()])
    username = StringField(
        'Username',
        validators=[Required(), Length(1, 64),
                    Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                           'Usernames should only contain letters, numbers, dots or underscores'
                           )
                    ]
    )
    name = StringField('Real Name', validators=[Length(0, 64)])
    phonenumber = StringField(
        "Mobile Phone Number (prefix with country code)")
    phonenumber_locale = HiddenField()
    is_admin = BooleanField("Is Admin")
    is_maintenance = BooleanField("Is Maintenance")
    submit = SubmitField('Update')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError('Email is already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError("Username is taken")

    def validate_phonenumber(self, field):
        data = field.data
        print("DATA: ", data)
        if not data:
            # Don't validate if nothing was provided
            return field
        try:
            if not data.startswith('+'):
                # Maybe they forgot this?
                data = '+' + data
            parsed = phonenumbers.parse(data)
        except:
            flash("Please ensure you prefix the phone number with your country code.")
            raise ValidationError("This is not a valid phone number")
        user = User.query.filter_by(phonenumber=data).first()
        if user and user.id != self.user.id:
            raise ValidationError("Phone number already on record.")
        if not phonenumbers.is_valid_number(parsed):
            flash("Please ensure you prefix the phone number with your country code.")
            raise ValidationError("This is not a valid phone number")

        if not carrier._is_mobile(phonenumberutil.number_type(parsed)):
            raise ValidationError("This phone number doesn't look like a mobile phone number")
        self.phonenumber_locale = phonenumbers.region_code_for_country_code(parsed.country_code)
