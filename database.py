# =============================================================================
# DATABASE MODELS — Alumni Tracker System
# BCA Final Year Project | TU Affiliated College, Nepal
# =============================================================================
# This file defines all database tables using SQLAlchemy ORM.
# Each class represents one table in the SQLite database (alumni.db).
# =============================================================================

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import bcrypt

# Initialize the database object (connected to Flask app in app.py)
db = SQLAlchemy()


# -----------------------------------------------------------------------------
# STUDENT TABLE
# Stores all alumni/student accounts including login credentials and profile info
# -----------------------------------------------------------------------------
class Student(db.Model, UserMixin):
    # Primary key — unique ID for each student record
    id         = db.Column(db.Integer, primary_key=True)

    # Login credentials
    student_id = db.Column(db.String(20),  unique=True, nullable=False)  # Used as username
    password   = db.Column(db.String(200), nullable=False)               # Bcrypt hashed phone number

    # Personal information
    full_name  = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(100))
    phone      = db.Column(db.String(15),  nullable=False)
    batch_year = db.Column(db.String(10))
    address    = db.Column(db.String(200))
    photo      = db.Column(db.String(200), default='default.png')  # Profile photo filename

    # Role — True for admin, False for regular alumni
    is_admin   = db.Column(db.Boolean, default=False)

    # Employment information
    job_title  = db.Column(db.String(100))
    company    = db.Column(db.String(100))
    job_sector = db.Column(db.String(50))

    # Higher education information
    higher_edu  = db.Column(db.String(200))
    institution = db.Column(db.String(200))

    def set_password(self, phone_number):
        """Hash the phone number and store it as the password."""
        self.password = bcrypt.hashpw(
            phone_number.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, phone_number):
        """Verify a phone number against the stored hashed password."""
        return bcrypt.checkpw(
            phone_number.encode('utf-8'),
            self.password.encode('utf-8')
        )


# -----------------------------------------------------------------------------
# NOTICE TABLE
# Stores announcements posted by the admin on the notice board
# -----------------------------------------------------------------------------
class Notice(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    content    = db.Column(db.Text,        nullable=False)
    is_pinned  = db.Column(db.Boolean,     default=False)   # Pinned notices appear first
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)


# -----------------------------------------------------------------------------
# MESSAGE TABLE
# Stores messages sent by alumni to the admin via the contact form
# -----------------------------------------------------------------------------
class Message(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    sender_id   = db.Column(db.Integer, db.ForeignKey('student.id'))  # Who sent it
    sender_name = db.Column(db.String(100))
    subject     = db.Column(db.String(200), nullable=False)
    content     = db.Column(db.Text,        nullable=False)
    is_read     = db.Column(db.Boolean,     default=False)  # Admin marks as read
    created_at  = db.Column(db.DateTime,    default=datetime.utcnow)


# -----------------------------------------------------------------------------
# EVENT TABLE
# Stores alumni events, reunions and gatherings scheduled by the admin
# -----------------------------------------------------------------------------
class Event(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_date  = db.Column(db.String(50),  nullable=False)
    location    = db.Column(db.String(200))
    event_type  = db.Column(db.String(50),  default='General')  # Reunion, Seminar, Workshop etc.
    created_at  = db.Column(db.DateTime,    default=datetime.utcnow)



# -----------------------------------------------------------------------------
# RSVP TABLE
# Stores alumni responses to events (Going, Maybe, Not Going)
# -----------------------------------------------------------------------------
class RSVP(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    event_id   = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    status     = db.Column(db.String(20), nullable=False)  # 'going', 'maybe', 'not_going'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



# -----------------------------------------------------------------------------
# FOLLOW TABLE
# Stores follow relationships between alumni
# -----------------------------------------------------------------------------
class Follow(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    following_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)    

# -----------------------------------------------------------------------------
# JOB TABLE
# Stores job postings by alumni
# -----------------------------------------------------------------------------
class Job(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    posted_by    = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    title        = db.Column(db.String(200), nullable=False)
    company      = db.Column(db.String(200), nullable=False)
    location     = db.Column(db.String(200))
    job_type     = db.Column(db.String(50), default='Full Time')  # Full Time, Part Time, Remote, Internship
    sector       = db.Column(db.String(100))
    description  = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    salary       = db.Column(db.String(100))
    deadline     = db.Column(db.String(50))
    is_active    = db.Column(db.Boolean, default=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

# -----------------------------------------------------------------------------
# JOB APPLICATION TABLE
# Stores applications submitted by alumni for jobs
# -----------------------------------------------------------------------------
class JobApplication(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    job_id       = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    applicant_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    cover_letter = db.Column(db.Text)
    status       = db.Column(db.String(20), default='pending')  # pending, reviewed, accepted, rejected
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)


# -----------------------------------------------------------------------------
# POST TABLE
# Stores alumni posts/updates for the community feed
# -----------------------------------------------------------------------------
class Post(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    author_id  = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    content    = db.Column(db.Text, nullable=False)
    post_type  = db.Column(db.String(50), default='update')  # update, achievement, job, question
    likes      = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    image = db.Column(db.String(200))  # Optional image filename

# -----------------------------------------------------------------------------
# REVIEW TABLE
# Stores alumni reviews and ratings of their college
# -----------------------------------------------------------------------------
class Review(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    author_id  = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    rating     = db.Column(db.Integer, nullable=False)   # 1-5 stars
    title      = db.Column(db.String(200), nullable=False)
    content    = db.Column(db.Text, nullable=False)
    teaching   = db.Column(db.Integer, default=3)  # Teaching quality rating
    facilities = db.Column(db.Integer, default=3)  # Facilities rating
    placement  = db.Column(db.Integer, default=3)  # Placement rating
    created_at = db.Column(db.DateTime, default=datetime.utcnow)




# -----------------------------------------------------------------------------
# COMMENT TABLE
# Stores comments on alumni feed posts
# -----------------------------------------------------------------------------
class Comment(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    post_id    = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    author_id  = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    content    = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



# -----------------------------------------------------------------------------
# NOTIFICATION TABLE
# Stores notifications for alumni (likes, comments, follows, etc.)
# -----------------------------------------------------------------------------
class Notification(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    actor_id   = db.Column(db.Integer, db.ForeignKey('student.id'))  # Who triggered it
    notif_type = db.Column(db.String(50), nullable=False)  # like, comment, follow, job, event
    message    = db.Column(db.String(300), nullable=False)
    link       = db.Column(db.String(200))  # Where to go when clicked
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# -----------------------------------------------------------------------------
# BOOKMARK TABLE
# Stores jobs bookmarked/saved by alumni
# -----------------------------------------------------------------------------
class Bookmark(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    job_id     = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# -----------------------------------------------------------------------------
# POLL TABLE
# Stores polls created by admin
# -----------------------------------------------------------------------------
class Poll(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    question   = db.Column(db.String(300), nullable=False)
    is_active  = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# -----------------------------------------------------------------------------
# POLL OPTION TABLE
# Stores options for each poll
# -----------------------------------------------------------------------------
class PollOption(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    poll_id  = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)
    text     = db.Column(db.String(200), nullable=False)
    votes    = db.Column(db.Integer, default=0)

# -----------------------------------------------------------------------------
# POLL VOTE TABLE
# Stores votes cast by alumni
# -----------------------------------------------------------------------------
class PollVote(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    poll_id    = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    option_id  = db.Column(db.Integer, db.ForeignKey('poll_option.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)