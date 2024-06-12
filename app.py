from flask import Flask, request, jsonify, render_template
from auth import auth
from views import views
import os
from config import Config
from models import db, User, Course, Submission
from datetime import datetime
from dotenv import load_dotenv

from api import api, jwt

app = Flask(__name__)
app.config.from_object(Config)

load_dotenv()

app.register_blueprint(auth, url_prefix="/")
app.register_blueprint(views, url_prefix="/")


@app.route("/api/courses/submissions/<string:course_id>", methods=["POST"])
def create_submission(course_id):
    course = Course.query.get(course_id)
    if course is None:
        return jsonify({"error": "Course not found"}), 404

    user_id = request.form["user_id"]
    assignment = request.form["assignment"]
    due_date = request.form["due_date"]
    file = request.files["file"]

    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404

    submission_date = datetime.now()
    due_date = datetime.strptime(due_date, "%Y-%m-%dT%H:%M:%S.%fZ")

    # Create the directory for the user if it doesn't exist
    user_dir = f"uploads/{user.name} {user.surname}"
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)

    # Save the file with the assignment name as the filename
    filename = f"{assignment}.pdf"
    file_path = os.path.join(user_dir, filename)
    file.save(file_path)

    submission = Submission(
        course, user, assignment, submission_date, due_date, file_path
    )
    db.session.add(submission)
    db.session.commit()

    return jsonify({"message": "Assignment submitted successfully!"}), 201


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
    db.create_all()

if __name__ == "__main__":
    app.run(port=5000, debug=True)
