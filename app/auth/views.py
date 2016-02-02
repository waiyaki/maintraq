from flask import render_template, url_for, redirect, request, flash

from flask.ext.login import current_user, login_user, login_required, logout_user

from .. import db
from . import auth
from app.models import User
from app.utils import send_email
from .forms import LoginForm, RegistrationForm


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            next = request.args.get('next')
            return redirect(next or url_for('main.index'))
        flash('Invalid username or password')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data,
                    phonenumber=form.phonenumber.data,
                    phonenumber_locale=form.phonenumber_locale)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(
            user.email, 'Confirm Your Account', 'auth/email/confirm',
            user=user, token=token
        )
        flash("A confirmation email has been sent to you.")
        login_user(user, form.password.data)
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('Welcome, {}! Your account has been confirmed, thanks!'.format(current_user.username))
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('main.index'))


# filter out unconfirmed accounts before fulfilling requests.
@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()  # Update last seen.
        if not current_user.confirmed and request.endpoint[:5] != 'auth.':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account', 'auth/email/confirm',
               user=current_user, token=token)
    flash("A new confirmation has been sent to you via email")
    return redirect(url_for('main.index'))
