from datetime import datetime

from flask import current_app

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin

from . import db
from . import login_manager


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    phonenumber = db.Column(db.String(15), unique=True, index=True)
    phonenumber_locale = db.Column(db.String(4))

    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)

    is_admin = db.Column(db.Boolean, default=False)
    is_maintenance = db.Column(db.Boolean, default=False)

    # More fields for profile info
    name = db.Column(db.String(64))
    last_seen = db.Column(db.DateTime(), default=datetime.now)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        # Make user admin if they are the designated admins in the env
        if not self.is_admin and not self.is_maintenance:
            if self.email == current_app.config['MAINTRAQ_ADMIN']:
                self.is_admin = True

    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False

        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False

        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    @property
    def tasks(self):
        return Task.query.filter_by(requested_by=self)

    @property
    def assigned(self):
        return Task.query.filter_by(assigned_to=self)

    @staticmethod
    def fake(count=50):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(
                email=forgery_py.internet.email_address(),
                username=forgery_py.internet.user_name(True),
                password=forgery_py.lorem_ipsum.word(),
                confirmed=True,
                name=forgery_py.name.full_name(),
                last_seen=forgery_py.date.date(True)
            )
            db.session.add(u)
            try:
                db.session.commit()
                print("Faked: ", u)
            except IntegrityError:
                db.session.rollback()

    def __repr__(self):
        return '<User %r>' % self.username


class Facility(db.Model):
    __tablename__ = 'facilities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    tasks = db.relationship('Task', backref='facility', lazy='dynamic')

    @staticmethod
    def fake(count=50):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            f = Facility(name=forgery_py.address.state())
            db.session.add(f)
            try:
                db.session.commit()
                print("Faked: ", f)
            except IntegrityError:
                db.session.rollback()

    def __repr__(self):
        return '<Facility %s>' % self.name


class TaskStatus:
    NOT_STARTED = 0
    STARTED = 1
    PENDING = 2
    DONE = 3


class Task(db.Model):
    __tablename__ = 'tasks'
    # pk
    id = db.Column(db.Integer, primary_key=True)

    # FKs
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.id'), nullable=False)
    requested_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    requested_by = db.relationship('User', foreign_keys=[requested_by_id])
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id])

    # Fields
    description = db.Column(db.String(255), nullable=False)
    detailed_info = db.Column(db.Text())
    confirmed = db.Column(db.Boolean, default=False)
    resolved = db.Column(db.Boolean, default=False)
    acknowledged = db.Column(db.Boolean, default=False)
    updated = db.Column(db.DateTime, default=datetime.now)
    progress = db.Column(db.Integer, default=TaskStatus.NOT_STARTED)
    date_requested = db.Column(db.DateTime(), index=True, default=datetime.now)
    date_completed = db.Column(db.DateTime(), nullable=True)

    def __repr__(self):
        return "<Task {!r:.15}{} Requested On: {:%a %b %d %H:%M:%S %Y} >".format(
            self.description,
            "...'" if len(self.description) > 15 else '',
            self.date_requested
        )

    @staticmethod
    def update_updated(target, value, oldvalue, *args, **kwargs):
        # update this date every time a task is updated.
        target.updated = datetime.now()

        # If it was just completed, set that time.
        if value != oldvalue and value == TaskStatus.DONE:
            target.date_completed = datetime.now()

        db.session.add(target)

    @property
    def status(self):
        if self.progress not in (0, 1, 2, 3):
            return "Unknown"
        elif self.progress == TaskStatus.NOT_STARTED:
            return "Not Started"
        elif self.progress == TaskStatus.STARTED:
            return "Started"
        elif self.progress == TaskStatus.PENDING:
            return "In Progress"
        return "DONE"

    @staticmethod
    def fake():
        import random

        from sqlalchemy.exc import IntegrityError
        import forgery_py

        users = User.query.all()
        facilities = Facility.query.all()

        for i in range(100):
            f = random.choice(facilities)
            u1 = random.choice(users)
            t = Task(
                facility_id=f.id, requested_by_id=u1.id,
                description=forgery_py.lorem_ipsum.sentence()
            )
            db.session.add(t)
            try:
                db.session.commit()
                print("Faked: ", t)
            except IntegrityError:
                db.session.rollback()

db.event.listen(Task.progress, 'set', Task.update_updated)
