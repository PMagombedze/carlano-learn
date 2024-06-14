from flask import Blueprint, render_template, request, flash, redirect, url_for
from models import db, User
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

auth = Blueprint("auth", __name__)


@auth.route("/", strict_slashes=False)
def login():
    return render_template("auth/login.html")


@auth.route("/auth/teacher/login", strict_slashes=False)
def teacher_login():
    return render_template("auth/teacher_login.html")


@auth.route("/auth/teacher/signup", strict_slashes=False)
def teacher_signup():
    return render_template("auth/teacher_signup.html")


@auth.route("/auth/create_account", strict_slashes=False)
def register():
    return render_template("auth/signup.html")


@auth.route("/auth/forgot_password", strict_slashes=False)
def forgot_password():
    return render_template("auth/forgot_password.html")


@auth.route("/auth/reset_password")
def reset_password():
    return render_template("auth/reset_password.html")
