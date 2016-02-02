from flask import flash

from flask.ext.wtf import Form

import phonenumbers
from phonenumbers import phonenumberutil, carrier
from wtforms import StringField, PasswordField, BooleanField, SubmitField, HiddenField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo, ValidationError

from app.models import User


class LoginForm(Form):
    username = StringField('Username', validators=[Required(), Length(1, 64)])
    password = PasswordField('Password')
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')


class RegistrationForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64), Email()])
    username = StringField(
        'Username',
        validators=[Required(), Length(1, 64),
                    Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                           'Usernames should only contain letters, numbers, dots or underscores'
                           )
                    ]
    )
    phonenumber = StringField(
        "Mobile Phone Number (prefix with country code)", validators=[Required(), Length(9, 13)])
    phonenumber_locale = HiddenField()
    password = PasswordField(
        'Password',
        validators=[Required(), EqualTo('password2', message="The passwords did not match.")]
    )
    password2 = PasswordField('Confirm Password', validators=[Required()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('This email is already registered.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("Username is taken")

    def validate_phonenumber(self, field):
        data = field.data
        try:
            if not data.startswith('+'):
                # Maybe they forgot this?
                data = '+' + data
            parsed = phonenumbers.parse(data)
        except:
            flash("Please ensure you prefix the phone number with your country code.")
            raise ValidationError("This is not a valid phone number")

        if not phonenumbers.is_valid_number(parsed):
            flash("Please ensure you prefix the phone number with your country code.")
            raise ValidationError("This is not a valid phone number")

        if not carrier._is_mobile(phonenumberutil.number_type(parsed)):
            raise ValidationError("This phone number doesn't look like a mobile phone number")
        self.phonenumber_locale = phonenumbers.region_code_for_country_code(parsed.country_code)
