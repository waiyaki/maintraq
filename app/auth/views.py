from flask import render_template, url_for, redirect, request, flash

from flask.ext.login import current_user, login_user, login_required, logout_user

from .. import db
from . import auth
from app.models import User
from app.utils import send_email
from .forms import (
    LoginForm, RegistrationForm, PasswordResetRequestForm, ChangePasswordForm,
    PasswordResetForm, ChangeEmailForm
)


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


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            flash('Your password has been updated.')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid password')
    return render_template('auth/change_password.html', form=form)


@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_confirmation_token()
            send_email(
                user.email, 'Reset Your Password', 'auth/email/reset_password',
                user=user, token=token, next=request.args.get('next')
            )
            flash("An email with instructions to reset your password has been sent to you.")
            return redirect(url_for('auth.login'))
        else:
            flash("Unable to find an account associated with that email address")
            return redirect(url_for('auth.password_reset_request'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            flash('Unable to find an account associated with that email address.')
            return redirect(url_for('main.index'))

        if user.reset_password(token, form.password.data):
            flash("Your password has been updated.")
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            send_email(
                new_email,
                'Confirm your email address', 'auth/email/change_email',
                user=current_user, token=token
            )
            flash("An email with instructions to confirm your new email address " +
                  "has been sent to you.")
            return redirect(url_for('main.index'))
        else:
            flash("Invalid email or password")
    return render_template('auth/change_email.html', form=form)


@auth.route('/change-email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        flash("Your email address has been updated.")
    else:
        flash("Invalid request")
    return redirect(url_for('main.index'))
