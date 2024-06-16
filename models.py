from flask_sqlalchemy import SQLAlchemy
import bcrypt
import uuid
from pydantic import EmailStr
from datetime import datetime
import os
import pytz
from werkzeug.utils import secure_filename

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    is_admin = db.Column(db.Boolean, default=False)
    email = db.Column(db.Text, unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    name = db.Column(db.Text)
    surname = db.Column(db.Text)

    # One-to-Many relationship with Assignments model
    assignments = db.relationship("Assignments", backref="teacher", lazy=True)

    # One-to-Many relationship with Submissions model
    submissions = db.relationship("Submissions", backref="student", lazy=True)

    def __init__(self, email: EmailStr, password, name, surname, is_admin):
        self.email = email
        self.password = self._hash_password(password)
        self.name = name
        self.surname = surname
        self.is_admin = is_admin

    def _hash_password(self, password):
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hashed_password.decode("utf-8")

    def check_password(self, password):
        return bcrypt.checkpw(password.encode("utf-8"), self.password.encode("utf-8"))


class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.Text, nullable=False)
    teacher_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"))
    teacher = db.relationship("User", backref="courses_taught")

    # Many-to-Many relationship with User model (students)
    students = db.relationship(
        "User", secondary="course_enrollments", backref="courses"
    )

    # One-to-Many relationship with Assignments model
    assignments = db.relationship("Assignments", backref="course", lazy=True)

    # One-to-Many relationship with Submissions model
    submissions = db.relationship("Submissions", backref="course", lazy=True)

    def __init__(self, title: str, teacher: User, description: str = ""):
        self.title = title
        self.teacher = teacher
        self.description = description

    @property
    def teacher_name(self):
        return f"{self.teacher.name} {self.teacher.surname}"


class CourseEnrollment(db.Model):
    __tablename__ = "course_enrollments"
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("courses.id"))
    user_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"))


class Assignments(db.Model):
    __tablename__ = "assignments"
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("courses.id"))
    teacher_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"))
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    assignment_file = db.Column(db.Text, nullable=True)

    def __init__(
        self,
        course: Course,
        teacher: User,
        name: str,
        description: str,
        due_date: datetime,
        assignment_file: str = None,
    ):
        self.course = course
        self.teacher = teacher
        self.name = name
        self.description = description
        self.due_date = due_date
        self.assignment_file = assignment_file


import arrow


class Submissions(db.Model):
    __tablename__ = "submissions"
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("courses.id"))
    student_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"))
    assignment_id = db.Column(
        db.UUID(as_uuid=True), db.ForeignKey("assignments.id"), nullable=False
    )
    assignment = db.relationship("Assignments", backref="submissions")
    assignment_text = db.Column(db.Text, nullable=False)
    submission_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    submission_date_str = db.Column(
        db.String,
        nullable=False,
        default=lambda: arrow.utcnow().to("US/Pacific").format("ddd D MMM YYYY h:mm A"),
    )
    submission_file = db.Column(db.Text, nullable=True)

    def __init__(
        self,
        course: Course,
        student: User,
        assignment: Assignments,
        assignment_text: str,
        submission_file: str = None,
    ):
        self.course = course
        self.student = student
        self.assignment = assignment
        self.assignment_text = assignment_text
        self.submission_date = datetime.utcnow()
        self.submission_file = submission_file

    def to_dict(self):
        student = User.query.filter_by(id=self.student_id, is_admin=False).first()
        if student:
            student_name = f"{student.name} {student.surname}"
        else:
            student_name = "Unknown"
        return {
            "id": self.id,
            "course_id": self.course_id,
            "student_id": self.student_id,
            "student_name": student_name,
            "submission_date_str": self.submission_date_str,
            "assignment_id": self.assignment_id,
            "assignment_text": self.assignment_text,
            "submission_date": self.submission_date.isoformat(),
            "submission_file": self.submission_file,
        }
