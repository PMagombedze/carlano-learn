from flask import Flask, request, jsonify
from auth import auth
import os
from config import Config
from models import db, User, Course, Submission
from datetime import datetime

from api import api, jwt, recaptcha

app = Flask(__name__)
app.config.from_object(Config)
app.config.update(dict(
    GOOGLE_RECAPTCHA_ENABLED=True,
    GOOGLE_RECAPTCHA_SITE_KEY="6LdsZ5opAAAAAHQUPPtHtrjHl_TCe9acD5VLI6O6",
    GOOGLE_RECAPTCHA_SECRET_KEY="6LdsZ5opAAAAAOr4Rf2gI8yqtQE6TbPtu6ykwUDs",
    GOOGLE_RECAPTCHA_THEME = "light",
    GOOGLE_RECAPTCHA_TYPE = "image",
    GOOGLE_RECAPTCHA_SIZE = "normal",
    GOOGLE_RECAPTCHA_LANGUAGE = "en",
    GOOGLE_RECAPTCHA_RTABINDEX = 10,
))
app.register_blueprint(auth, url_prefix="/")


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


with app.app_context():

    api.init_app(app)
    jwt.init_app(app)
    recaptcha.init_app(app)
    db.init_app(app)
    db.create_all()

if __name__ == "__main__":
    app.run(port=5000, debug=True)
