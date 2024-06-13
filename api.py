from flask_restful import Resource, Api, reqparse
from flask import request, jsonify
from models import User, db, Course, Submission, CourseEnrollment
from dotenv import load_dotenv
import pydantic, werkzeug
from datetime import datetime

from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    create_access_token,
    get_jwt_identity,
)

api = Api()
jwt = JWTManager()

from pydantic import BaseModel, EmailStr

load_dotenv()


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    surname: str


class Signup(Resource):
    def post(self):
        data = request.get_json()
        try:
            user_data = UserCreate(**data)
            email = user_data.email
            password = user_data.password
            surname = user_data.surname
            name = user_data.name
        except pydantic.ValidationError as e:
            error_msg = "Invalid email address"
            if e.errors():
                error_msg += ": " + e.errors()[0]["msg"]
            return {"error": error_msg}, 400

        # Check if user with the given email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return {"error": "Email already exists"}, 400

        # Create a new user
        new_user = User(email=email, password=password, name=name, surname=surname)
        db.session.add(new_user)
        db.session.commit()

        # Generate a JWT token for the new user
        access_token = create_access_token(identity=email)
        return {"message": "User created successfully", "token": access_token}, 201


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
            }, 200
        else:
            return {"message": "Invalid password"}, 200


class ProtectedResource(Resource):
    @jwt_required()
    def get(self):
        return {"message": "Token is valid"}


class SubmissionResource(Resource):
    def post(self, course_id):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "file", type=werkzeug.datastructures.FileStorage, location="files"
        )
        parser.add_argument(
            "submission_date", required=True, help="Submission date cannot be blank!"
        )
        parser.add_argument("due_date", required=True, help="Due date cannot be blank!")
        data = parser.parse_args()

        course = Course.query.filter_by(id=course_id).first()
        if not course:
            return {"error": "Course not found"}, 404

        submission = Submission(
            course_id=course_id,
            assignment=data["file"].read(),  # Read the uploaded PDF file
            submission_date=datetime.strptime(data["submission_date"], "%Y-%m-%d"),
            due_date=datetime.strptime(data["due_date"], "%Y-%m-%d"),
        )
        db.session.add(submission)
        db.session.commit()

        return {"message": "Submission created successfully"}, 201


class CourseResource(Resource):
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("title", required=True, help="Title cannot be blank!")
        parser.add_argument(
            "teacher_name", required=True, help="Teacher name cannot be blank!"
        )
        data = parser.parse_args()

        current_user = get_jwt_identity()
        user = User.query.filter_by(email=current_user).first()
        if not user or not user.is_admin:
            return {"error": "Unauthorized access"}, 403

        new_course = Course(
            title=data["title"],
            teacher_name=data["teacher_name"],
        )
        db.session.add(new_course)
        db.session.commit()

        return jsonify({"message": "Course created successfully"})

    # @jwt_required()
    def get(self):
        # current_user = get_jwt_identity()
        # user = User.query.filter_by(email=current_user).first()
        # if not user or not user.is_admin:
        #     return {"error": "Unauthorized access"}, 403

        courses = Course.query.all()
        return jsonify(
            [
                {
                    "id": str(course.id),
                    "title": course.title,
                    "teacher_name": course.teacher_name,
                }
                for course in courses
            ]
        )


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


api.add_resource(
    UnenrollCourse, "/api/students/<string:student_id>/<string:course_id>/courses"
)
api.add_resource(EnrollStudent, "/api/students/enroll")
api.add_resource(StudentCourses, "/api/students/<string:student_id>/courses")
api.add_resource(CourseResource, "/api/courses")
api.add_resource(SubmissionResource, "/api/courses/<string:course_id>/submissions")
api.add_resource(ProtectedResource, "/api/protected")
api.add_resource(Signup, "/api/signup")
api.add_resource(Users, "/api/signup/users", "/api/signup/users/<string:id>")
api.add_resource(Login, "/api/login")
