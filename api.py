from flask_restful import Resource, Api, reqparse
from flask import request, jsonify
from models import User, db, Course, Submissions, CourseEnrollment, Assignments
from dotenv import load_dotenv
import pydantic, werkzeug
from datetime import datetime, timedelta
from flask_mail import Mail, Message
import os
import re


from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    create_access_token,
    get_jwt_identity,
)

api = Api()
jwt = JWTManager()
mail = Mail()

from pydantic import BaseModel, EmailStr

load_dotenv()


commonPasswords = [
    "123456",
    "password",
    "123456789",
    "12345678",
    "12345",
    "1234567",
    "admin",
    "123123",
    "qwerty",
    "abc123",
    "letmein",
    "monkey",
    "111111",
    "password1",
    "qwerty123",
    "dragon",
    "1234",
    "baseball",
    "iloveyou",
    "trustno1",
    "sunshine",
    "princess",
    "football",
    "welcome",
    "shadow",
    "superman",
    "michael",
    "ninja",
    "mustang",
    "jessica",
    "charlie",
    "ashley",
    "bailey",
    "passw0rd",
    "master",
    "love",
    "hello",
    "freedom",
    "whatever",
    "nicole",
    "jordan",
    "cameron",
    "secret",
    "summer",
    "1q2w3e4r",
    "zxcvbnm",
    "starwars",
    "computer",
    "taylor",
    "startrek",
    "123456",
    "123456789",
    "qwerty",
    "password",
    "12345",
    "qwerty123",
    "1q2w3e",
    "12345678",
    "111111",
    "1234567890",
]


def is_secure_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if password in commonPasswords:
        return False
    return True


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    surname: str
    is_admin: bool


class Signup(Resource):
    def post(self):
        data = request.get_json()
        try:
            user_data = UserCreate(**data)
            email = user_data.email
            password = user_data.password
            surname = user_data.surname
            name = user_data.name
            is_admin = user_data.is_admin

        except pydantic.ValidationError as e:
            error_msg = "Invalid email address"
            if e.errors():
                error_msg += ": " + e.errors()[0]["msg"]
            return {"error": error_msg}, 400

        # Check if user with the given email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return {"error": "Email already exists"}, 400

        if is_secure_password(password) == False:
            return {
                "error": "Password should contain at least 8 characters, an uppercase and a lowercase character"
            }, 400

        new_user = User(
            email=email,
            password=password,
            name=name,
            surname=surname,
            is_admin=is_admin,
        )
        db.session.add(new_user)
        db.session.commit()

        # Generate a JWT token for the new user
        access_token = create_access_token(identity=email)
        return {
            "message": "User created successfully",
            "token": access_token,
            "is_admin": is_admin,
        }, 201


class Users(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        user = User.query.filter_by(email=current_user).first()
        if not user or not user.is_admin:
            return {"error": "Unauthorized access"}, 403
        users = User.query.all()
        return [
            {
                "id": str(user.id),
                "email": user.email,
                "password": user.password,
                "name": user.name,
                "surname": user.surname,
            }
            for user in users
        ], 200

    @jwt_required()
    def delete(self, id):
        current_user = get_jwt_identity()
        user = User.query.filter_by(email=current_user).first()
        if not user or not user.is_admin:
            return {"error": "Unauthorized access"}, 403
        user_to_delete = User.query.filter_by(id=id).first()
        if not user_to_delete:
            return {"error": "User not found"}, 404
        db.session.delete(user_to_delete)
        db.session.commit()
        return {"message": "User deleted successfully"}, 200


class Login(Resource):
    def post(self):
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        user = User.query.filter_by(email=email).first()
        if not user:
            return {"message": "User not found"}, 200
        if user.check_password(password):
            # Generate a JWT token for the user
            access_token = create_access_token(identity=email)
            return {
                "message": "Logged in successfully",
                "token": access_token,
                "id": str(user.id),
                "is_admin": user.is_admin,
                "surname": user.surname,
                "name": user.name,
            }, 200
        else:
            return {"message": "Invalid password"}, 200


class ProtectedResource(Resource):
    @jwt_required()
    def get(self):
        return {"message": "Token is valid"}


class SubmissionsResource(Resource):
    def post(self, course_id):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "file", type=werkzeug.datastructures.FileStorage, location="files"
        )
        parser.add_argument(
            "submissions_date", required=True, help="Submissions date cannot be blank!"
        )
        parser.add_argument("due_date", required=True, help="Due date cannot be blank!")
        data = parser.parse_args()

        course = Course.query.filter_by(id=course_id).first()
        if not course:
            return {"error": "Course not found"}, 404

        submissions = Submissions(
            course_id=course_id,
            assignment=data["file"].read(),  # Read the uploaded PDF file
            submissions_date=datetime.strptime(data["submissions_date"], "%Y-%m-%d"),
            due_date=datetime.strptime(data["due_date"], "%Y-%m-%d"),
        )
        db.session.add(submissions)
        db.session.commit()

        return {"message": "Submissions created successfully"}, 201


class CourseResource(Resource):
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("title", required=True, help="Title cannot be blank!")
        data = parser.parse_args()

        current_user = get_jwt_identity()
        user = User.query.filter_by(email=current_user).first()
        if not user or not user.is_admin:
            return {"error": "Unauthorized access"}, 403

        if Course.query.filter_by(title=data["title"]).first():
            return {"error": "Course with this title already exists"}, 400

        new_course = Course(
            title=data["title"], teacher=user  # Set the teacher to the current user
        )
        db.session.add(new_course)
        db.session.commit()

        return jsonify({"message": "Course created successfully"})

    def get(self):
        courses = Course.query.all()
        return jsonify(
            [
                {
                    "id": str(course.id),
                    "title": course.title,
                    "teacher_name": course.teacher_name,  # Use the computed property
                }
                for course in courses
            ]
        )

    @jwt_required()
    def delete(self, course_id):
        current_user = get_jwt_identity()
        user = User.query.filter_by(email=current_user).first()
        if not user or not user.is_admin:
            return {"error": "Unauthorized access"}, 403

        course = Course.query.filter_by(id=course_id).first()
        if not course:
            return {"error": "Course not found"}, 404

        db.session.delete(course)
        db.session.commit()

        return {"message": "Course deleted successfully"}, 200


class StudentCourses(Resource):
    def get(self, student_id):
        student = User.query.get(student_id)
        if student is None:
            return jsonify({"error": "Student not found"}), 404

        courses = student.courses
        course_list = [
            {
                "id": course.id,
                "title": course.title,
                "teacher_name": course.teacher_name,
            }
            for course in courses
        ]

        return jsonify({"courses": course_list})


class EnrollStudent(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "student_id", required=True, help="Student ID cannot be blank"
        )
        parser.add_argument(
            "course_id", required=True, help="Course ID cannot be blank"
        )
        args = parser.parse_args()

        student = User.query.get(args["student_id"])
        if student is None:
            return jsonify({"error": "Student not found"}), 404

        course = Course.query.get(args["course_id"])
        if course is None:
            return jsonify({"error": "Course not found"}), 404

        if course in student.courses:
            return jsonify({"error": "Student is already enrolled in this course"}), 400

        enrollment = CourseEnrollment(
            user_id=args["student_id"], course_id=args["course_id"]
        )
        db.session.add(enrollment)
        db.session.commit()

        return jsonify({"message": "Student enrolled in course successfully"})


class UnenrollCourse(Resource):
    def delete(self, student_id, course_id):
        student = User.query.get(student_id)
        if student is None:
            return jsonify({"error": "Student not found"}), 404

        course = Course.query.get(course_id)
        if course is None:
            return jsonify({"error": "Course not found"}), 404

        enrollment = CourseEnrollment.query.filter_by(
            user_id=student_id, course_id=course_id
        ).first()
        if enrollment is None:
            return jsonify({"error": "Student is not enrolled in this course"}), 400

        db.session.delete(enrollment)
        db.session.commit()

        return jsonify({"message": "Student unenrolled from course successfully"})


class ForgotPassword(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("email", required=True, help="Email cannot be blank!")
        data = parser.parse_args()

        user = User.query.filter_by(email=data["email"]).first()
        if not user:
            return {"error": "User not found"}, 404

        # Generate a password reset token that expires after 5 minutes
        reset_token = create_access_token(
            identity=user.email, expires_delta=timedelta(minutes=5)
        )

        # Send the reset token to the user via email
        msg = Message(
            "Password Reset Token",
            sender=("Carlano Team", os.getenv("MAIL_USERNAME")),
            recipients=[user.email],
        )
        msg.body = f"Hello {user.name},\n\nPlease click on the following link to reset your password: http://localhost:5000/auth/reset_password?token={reset_token}\n\nBest regards,\nThe Support Team"
        mail.send(msg)

        return {"message": "Password reset token sent to your email"}, 200

    @jwt_required()
    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "new_password", required=True, help="New password cannot be blank!"
        )
        parser.add_argument(
            "confirm_password", required=True, help="Confirm password cannot be blank!"
        )
        data = parser.parse_args()

        if data["new_password"] != data["confirm_password"]:
            return {"error": "New password and confirm password must match"}, 400

        # Get the user from the JWT token
        user = User.query.filter_by(email=get_jwt_identity()).first()
        if not user:
            return {"error": "User not found"}, 404

        # Update the user's password
        if is_secure_password(data["new_password"]) == False:
            return {
                "error": "Password should contain at least 8 characters, an uppercase and a lowercase character"
            }, 400

        user.password = User._hash_password(self, data["new_password"])
        db.session.commit()

        return {"message": "Password updated successfully"}, 200


class AssignmentListAPI(Resource):
    def get(self):
        assignments = Assignments.query.all()
        return jsonify(
            [
                {
                    "id": str(assignment.id),
                    "course_id": str(assignment.course_id),
                    "name": assignment.name,
                    "description": assignment.description,
                    "due_date": assignment.due_date.isoformat(),
                    "assignment_file": assignment.assignment_file,
                }
                for assignment in assignments
            ]
        )


class AllSubmissions(Resource):
    #use jwt so that only teacher can view submissions
    def get(self):
        submissions = Submissions.query.all()
        return jsonify([submission.to_dict() for submission in submissions])


api.add_resource(AllSubmissions, "/api/submissions")
api.add_resource(AssignmentListAPI, "/api/assignments")
api.add_resource(ForgotPassword, "/api/forgot_password")
api.add_resource(
    UnenrollCourse, "/api/students/<string:student_id>/<string:course_id>/courses"
)
api.add_resource(EnrollStudent, "/api/students/enroll")
api.add_resource(StudentCourses, "/api/students/<string:student_id>/courses")
api.add_resource(CourseResource, "/api/courses", "/api/courses/<string:course_id>")
api.add_resource(SubmissionsResource, "/api/courses/<string:course_id>/submissions")
api.add_resource(ProtectedResource, "/api/protected")
api.add_resource(Signup, "/api/signup")
api.add_resource(Users, "/api/signup/users", "/api/signup/users/<string:id>")
api.add_resource(Login, "/api/login")
