# SQLAlchemy models

from flask_sqlalchemy import SQLAlchemy
import bcrypt
import uuid
from pydantic import EmailStr

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    is_admin = db.Column(db.Boolean, default=False)
    email = db.Column(db.Text, unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    name = db.Column(db.Text)
    surname = db.Column(db.Text)

    def __init__(self, email: EmailStr, password, name, surname):
        self.email = email
        self.password = self._hash_password(password)
        self.name = name
        self.surname = surname

    def _hash_password(self, password):
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hashed_password.decode("utf-8")

    def check_password(self, password):
        return bcrypt.checkpw(password.encode("utf-8"), self.password.encode("utf-8"))


class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.Text, nullable=False)
    teacher_name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Many-to-Many relationship with User model (students)
    students = db.relationship(
        "User", secondary="course_enrollments", backref="courses"
    )

    # One-to-Many relationship with Submission model
    submissions = db.relationship("Submission", backref="course", lazy=True)

    def __init__(self, title: str, teacher_name: str, description: str = ""):
        self.title = title
        self.teacher_name = teacher_name
        self.description = description


class CourseEnrollment(db.Model):
    __tablename__ = "course_enrollments"
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("courses.id"))
    user_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"))


class Submission(db.Model):
    __tablename__ = "submissions"
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("courses.id"))
    user_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"))
    assignment = db.Column(db.Text, nullable=False)
    submission_date = db.Column(db.DateTime, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)

    def __init__(
        self,
        course: Course,
        user: User,
        assignment,
        submission_date,
        due_date,
    ):
        self.course = course
        self.user = user
        self.assignment = assignment
        self.submission_date = submission_date
        self.due_date = due_date
