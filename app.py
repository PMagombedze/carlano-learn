from flask import Flask, request, jsonify, render_template, send_from_directory, url_for
from auth import auth
from views import views
import os
from flask_migrate import Migrate
from config import Config
from models import *
from datetime import datetime
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

from api import api, jwt, mail

app = Flask(__name__)
app.config.from_object(Config)
migrate = Migrate(app, db)

load_dotenv()

app.register_blueprint(auth, url_prefix="/")
app.register_blueprint(views, url_prefix="/")


@app.route("/api/students/<string:student_id>/assignments", methods=["POST"])
def submit_assignment(student_id):
    return jsonify({"message": "Assignment submitted successfully"}), 201


@app.route("/api/students/assignments", methods=["POST"])
def create_assignment():
    file = request.files["file"]

    # Get the assignment title from the request form
    title = request.form["title"]
    course = request.form["course"]
    teacher = request.form["teacher"]
    description = request.form["description"]
    due_date = request.form["due_date"]


    # Check if the file is present
    if not file:
        return jsonify({"message": "No file provided"}), 400

    # Securely save the file to the uploads folder
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOADS_FOLDER"], filename)
    file.save(file_path)

    # Create a new assignment instance
    assignment = Assignments(
        name=title,
        course=course,
        teacher=teacher,
        description=description,
        due_date=due_date,
        assignment_file=file_path,
    )
    db.session.add(assignment)
    db.session.commit()
    return (
        jsonify({"message": "Assignment created successfully"}),
        201,
    )

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOADS_FOLDER"], filename)

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("error/server.html"), 500


@app.errorhandler(404)
def client_error(e):
    return render_template("error/client.html"), 404


with app.app_context():

    api.init_app(app)
    jwt.init_app(app)
    db.init_app(app)
    mail.init_app(app)
    db.create_all()

if __name__ == "__main__":
    app.run(port=5000, debug=True)
