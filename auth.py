from flask import Blueprint, render_template

auth = Blueprint('auth', __name__)

@auth.route('/')
def login():
    return render_template('auth/login.html')