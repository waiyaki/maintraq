from flask.ext.wtf import Form

from wtforms import SubmitField, SelectField, StringField, TextAreaField
from wtforms.validators import Required, Length

from app.models import Facility


class TaskRequestForm(Form):
    description = StringField("Description", validators=[Required(), Length(10, 255)])
    detailed_info = TextAreaField("Detailed Information")
    facility = SelectField('Facility', coerce=int)
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(TaskRequestForm, self).__init__(*args, **kwargs)
        self.facility.choices = [
            (fac.id, fac.name) for fac in Facility.query.order_by(Facility.name).all()
        ]
