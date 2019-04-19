from models.anime import Anime
from models.users import User
from flask import Flask, flash, request, render_template, redirect, url_for, request, abort, jsonify, make_response
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_cors import CORS
from werkzeug.security import safe_str_cmp
from flask_jwt import JWT, jwt_required, current_identity
from logging.handlers import RotatingFileHandler
import json
import os
import hashlib
import logging


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///asg3.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = False  # use false for production
db = SQLAlchemy(app)

logHandler = RotatingFileHandler('info.log', maxBytes=1000, backupCount=1)
logHandler.setLevel(logging.INFO)
app.logger.setLevel(logging.INFO)
app.logger.addHandler(logHandler)
log = app.logger


CORS(app, resources={r"/api/*": {"origins": "*"}})


@app.before_first_request
def setup():
    print("Running flask for the First Time. Installing database.")
    db.Model.metadata.drop_all(bind=db.engine)
    db.Model.metadata.create_all(bind=db.engine)

# When the Flask app is shutting down, close the database session
@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()


@app.route('/')
def home():
    return redirect('/anime')


@app.route('/anime', methods=['GET', 'POST'])
def show_all_anime():
    records = Anime.query.order_by(Anime.anime_id.asc())
    return render_template('index.html', Anime=records)


@app.route('/anime/<anime_id>', methods=['GET'])
def get_anime_by_id(anime_id):
    show = Anime.query.get(anime_id)
    return render_template('details.html', anime=show)
