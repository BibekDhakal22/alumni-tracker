from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import bcrypt

db = SQLAlchemy()

class Student(db.Model, UserMixin):
    id         = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    full_name  = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(100))
    phone      = db.Column(db.String(15), nullable=False)
    password   = db.Column(db.String(200), nullable=False)
    batch_year = db.Column(db.String(10))
    is_admin   = db.Column(db.Boolean, default=False)

    # Profile info
    job_title   = db.Column(db.String(100))
    company     = db.Column(db.String(100))
    job_sector  = db.Column(db.String(50))
    higher_edu  = db.Column(db.String(200))
    institution = db.Column(db.String(200))
    address     = db.Column(db.String(200))
    photo = db.Column(db.String(200), default='default.png')

    def set_password(self, phone_number):
        self.password = bcrypt.hashpw(
            phone_number.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, phone_number):
        return bcrypt.checkpw(
            phone_number.encode('utf-8'),
            self.password.encode('utf-8')
        )


from datetime import datetime

class Notice(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    content    = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_pinned  = db.Column(db.Boolean, default=False)

class Message(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    sender_id   = db.Column(db.Integer, db.ForeignKey('student.id'))
    sender_name = db.Column(db.String(100))
    subject     = db.Column(db.String(200), nullable=False)
    content     = db.Column(db.Text, nullable=False)
    is_read     = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)    