from flask import Flask
from auth import auth
from config import Config
from models import db

from api import api, jwt

app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(auth, url_prefix="/")

with app.app_context():

    api.init_app(app)
    jwt.init_app(app)
    db.init_app(app)
    db.create_all()

if __name__ == "__main__":
    app.run(port=5000, debug=True)
