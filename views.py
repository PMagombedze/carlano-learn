from flask import Blueprint, render_template

views = Blueprint("views", __name__)


@views.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@views.route("/teacher/dashboard")
def teacher():
    return render_template("teacher.html")


@views.route("/dashboard/<topic>")
def dashboard_topic(topic):
    return render_template("submissions.html", topic=topic)