from flask_restful import Resource, Api, reqparse
from flask import request, jsonify
from models import User, db, Course, Submission
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


class Signup(Resource):
    def post(self):
        data = request.get_json()
        try:
            user_data = UserCreate(**data)
            email = user_data.email
            password = user_data.password
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
        new_user = User(email=email, password=password)
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
            {"id": str(user.id), "email": user.email, "password": user.password}
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
            return {"message": "Logged in successfully", "token": access_token}, 200
        else:
            return {"message": "Invalid password"}, 200


class ProtectedResource(Resource):
    @jwt_required()
    def get(self):
        return {"message": "Token is valid"}


class SubmissionResource(Resource):
    def post(self, course_id):
        course = Course.query.get(course_id)
        if course is None:
            return {"error": "Course not found"}, 404

        parser = reqparse.RequestParser()
        parser.add_argument("user_id")
        parser.add_argument(
            "assignment"
        )
        parser.add_argument("due_date")
        parser.add_argument(
            "file",
            type=werkzeug.datastructures.FileStorage,
            required=True,
        )

        data = parser.parse_args(strict=False)
        user = User.query.get(data["user_id"])
        if user is None:
            return {"error": "User not found"}, 404

        submission_date = datetime.now()
        due_date = datetime.strptime(data["due_date"], "%Y-%m-%dT%H:%M:%S.%fZ")

        file = data["file"]
        file.save("static/uploads/" + file.filename)

        submission = Submission(
            course, user, data["assignment"], submission_date, due_date, file.filename
        )
        db.session.add(submission)
        db.session.commit()

        return {"message": "Assignment submitted successfully!"}, 201


class CourseResource(Resource):
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("title", required=True, help="Title cannot be blank!")
        parser.add_argument(
            "teacher_name", required=True, help="Teacher name cannot be blank!"
        )
        parser.add_argument("description", required=False)
        data = parser.parse_args()

        current_user = get_jwt_identity()
        user = User.query.filter_by(email=current_user).first()
        if not user or not user.is_admin:
            return {"error": "Unauthorized access"}, 403

        new_course = Course(
            title=data["title"],
            teacher_name=data["teacher_name"],
            description=data.get("description", ""),
        )
        db.session.add(new_course)
        db.session.commit()

        return jsonify({"message": "Course created successfully"})

    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        user = User.query.filter_by(email=current_user).first()
        if not user or not user.is_admin:
            return {"error": "Unauthorized access"}, 403

        courses = Course.query.all()
        return jsonify(
            [
                {
                    "id": str(course.id),
                    "title": course.title,
                    "teacher_name": course.teacher_name,
                    "description": course.description,
                }
                for course in courses
            ]
        )


api.add_resource(CourseResource, "/api/courses")
api.add_resource(SubmissionResource, "/api/courses/<string:course_id>/submissions")
api.add_resource(ProtectedResource, "/api/protected")
api.add_resource(Signup, "/api/signup")
api.add_resource(Users, "/api/signup/users", "/api/signup/users/<string:id>")
api.add_resource(Login, "/api/login")
