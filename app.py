from flask import Flask, request, jsonify
from auth import auth
from config import Config
from models import db, User, Course, Submission
from datetime import datetime

from api import api, jwt

app = Flask(__name__)
app.config.from_object(Config)
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

    # Removed the file type check, allowing any type of file
    file.save("uploads/" + file.filename)

    submission = Submission(
        course, user, assignment, submission_date, due_date, file.filename
    )
    db.session.add(submission)
    db.session.commit()

    return jsonify({"message": "Assignment submitted successfully!"}), 201


with app.app_context():

    api.init_app(app)
    jwt.init_app(app)
    db.init_app(app)
    db.create_all()

if __name__ == "__main__":
    app.run(port=5000, debug=True)
