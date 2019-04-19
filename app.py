import hashlib
import logging
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, jsonify, make_response, render_template, flash, redirect
from sqlalchemy import func
from flask_cors import CORS
from werkzeug.security import safe_str_cmp
from flask_jwt import JWT, jwt_required, current_identity
from logging.handlers import RotatingFileHandler


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///asg3.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = False  # use false for production
db = SQLAlchemy(app)

# Setting up Logging Functionality (using file-based logging)
logHandler = RotatingFileHandler('info.log', maxBytes=1000, backupCount=1)
logHandler.setLevel(logging.INFO)
app.logger.setLevel(logging.INFO)
app.logger.addHandler(logHandler)
log = app.logger

# enable CORS on all the routes that start with /api
CORS(app, resources={r"/api/*": {"origins": "*"}})

# configure the database to use Flask Sessions
db = SQLAlchemy(app)
session = db.session

# Import the models after initialising the database-
from models.anime import Anime
from models.users import User


def authenticate(username, password):
    """
    The Authenticate function is used primarily by the JWT library to determine if submitted credentials match
    :param username: Unique username for the user
    :param password: Password used to verify user account
    :return: returns an instance of the user model
    """
    try:
        # Fetch user using the username (case insensitive search)
        user = User.query.filter(func.lower(User.username) == func.lower(username)).one_or_none()
        if user:  # If we found a record, then hash password and compare to determine validity
            hashed_password = hashlib.sha1(password.encode('utf-8')).hexdigest()
            if safe_str_cmp(hashed_password, user.password):
                return user  # return the instance of the user
    except Exception as e:
        log.error("Authenticate: {0}".format(e))
    # We failed authentication either due to incorrect credentials or server error
    return False


def identity(payload):
    """
    The identify function will provide a way to retrieve the user details based on the identity in the JWT
    :param payload: the data payload within the JWT request
    :return: returns the serializable (dictionary-based) representation of the user or None if no user found
    """
    try:
        user_id = payload['identity']
        user = User.query.get(user_id)
        if user:
            return user.toDict()
    except Exception as e:
        print(e)
    return None


jwt = JWT(app, authenticate, identity)


@app.before_first_request
def setup():
    print("Running flask for the First Time. Installing database.")
    db.Model.metadata.drop_all(bind=db.engine)
    db.Model.metadata.create_all(bind=db.engine)


@app.route('/')
def home():
    """
    Displays the landing page for the application
    """
    records = []
    start = 1
    num_records = 10
    try:
        query = Anime.query.order_by(Anime.anime_id.asc())
        # retrieve query parameters for controlling amount of records retrieved
        start = request.args.get('offset', default=1, type=int)
        num_records = request.args.get('limit', default=10, type=int)
        # retrieve the data as pages
        records = query.paginate(start, num_records).items
    except Exception as e:
        log.error("Get Index: {0}".format(e))

    return render_template('index.html', Anime=records, start=start, num_records=num_records )


@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity


@app.route('/protected')
@app.route('/api/users', methods=['GET'])
def get_users():
    """
    Retrieve the users from the database
    :return:
    """
    try:
        query = User.query.order_by(User.username.asc())
        # retrieve query parameters for controlling amount of records retrieved
        start = request.args.get('offset', default=1, type=int)
        num_records = request.args.get('limit', default=10, type=int)
        # retrieve the data as pages
        records = query.paginate(start, num_records).items
        # convert records into its dictionary-based representation for serialization
        records = [rec.toDict() for rec in records]
        
        return jsonify(records)  # convert the dictionary-base representation as a JSON response
    except Exception as e:
        log.error("Get Users: {0}".format(e))
        return make_response(jsonify({'error': 'Server encountered an error.'
                                               ' Contact the administrator if problem persists.'}), 500)


@app.route('/protected')
@app.route('/api/users', methods=['POST'])
def store_users():
    try:
        if request.form:  # Check if the user info is submitted by an HTML form
            request_data = request.form
        else:  # Information is submitted via an API request using JSON
            request_data = request.get_json()
        # retrieve the data from the request from the client
        username = request_data.get('username')
        password = request_data.get('password')
        # print("Username: {0}, Password: {1}, Role: {2}".format(username, password, role))
        # If all the information supplied
        if username and password:  # (TODO Should provide more extensive data validation before saving)
            # hash the password using the same method used before (TODO put into a function to modularize and DRY method)
            hashed_password = hashlib.sha1(username.encode('utf-8')).hexdigest()
            # Add the data to the model, save and then commit to the database
            user = User(username, hashed_password)
            session.add(user)
            session.commit()
            # Once the save operation is completed, then send response with record to the client
            return make_response(jsonify(user.toDict()), 201) # set the HTTP status code to created
        else:
            # At this point, the details submitted by user is incorrect, therefore we sent appropriate HTTP Status code
            return make_response(jsonify({'error': 'Invalid information received.'}), 400)
    except Exception as e:
        log.error("Store Users: {0}".format(e))
        return make_response(jsonify({'error': 'Server encountered an error.'
                                               ' Contact the administrator if problem persists.'}), 500)


@app.route('/api/users/<username>', methods=['GET'])
def get_user_by_username(username):
    """
    A function to retrieve the specific details of a user by the username submitted via the URL
    :param username:
    :return:
    """
    try:
        user = User.query.filter(func.lower(User.username) == func.lower(username)).one_or_none()
        if user:
            return jsonify(user.toDict())
        else:
            return make_response(jsonify(None), 404)
    except Exception as e:
        log.error("Get By Username: {0}".format(e))
        return make_response(jsonify({'error': 'Server encountered an error.'
                                               ' Contact the administrator if problem persists.'}), 500)


@app.route('/api/anime', methods=['GET','POST'])
def show_all_anime():
    try:
        query = Anime.query.order_by(Anime.anime_id.asc())
        # retrieve query parameters for controlling amount of records retrieved
        start = request.args.get('offset', default=1, type=int)
        num_records = request.args.get('limit', default=10, type=int)
        # retrieve the data as pages
        records = query.paginate(start, num_records).items
        
        return render_template('index.html', Anime=records, start=start, num_records=num_records )

    except Exception as e:
        log.error("Show all Anime: {0}".format(e))
        return make_response(jsonify({'error': 'Server encountered an error.'
                                               ' Contact the administrator if problem persists.'}), 500)


@app.route('/anime/<anime_id>', methods=['GET'])
def get_anime_by_id(anime_id):
    try:
        anime = Anime.query.get(anime_id)
        if anime:
            show = Anime.query.get(anime_id)
            return render_template('details.html', anime=show)
        else:
            results = None
            return make_response(jsonify(results), 404)
    except Exception as e:
        log.error("Get Anime by Id: {0}".format(e))
        return make_response(jsonify({'error': 'Server encountered an error.'
                                               ' Contact the administrator if problem persists.'}), 500)

@app.route('/api/login', methods=['GET'])
def go_to_login_page():
    try:
        return render_template('login.html')
    except Exception as e:
        log.error("Failed to login: {0}".format(e))
        return make_response(jsonify({'error': 'Server encountered an error.'
                                               ' Contact the administrator if problem persists.'}), 500)

@app.route('/api/login', methods=['POST'])
def login():
    try:
        import hashlib
        query = Anime.query.order_by(Anime.anime_id.asc())
        # retrieve query parameters for controlling amount of records retrieved
        start = request.args.get('offset', default=1, type=int)
        num_records = request.args.get('limit', default=10, type=int)
        # retrieve the data as pages
        records = query.paginate(start, num_records).items

        username = request.form.get('username')
        password = request.form.get('password')
        
        isAuthenticated = False
        if username and password:
            user = User.query.filter(func.lower(User.username) == func.lower(username)).one_or_none()
            if user:
                isAuthenticated = True
                return render_template('index.html', isAuthenticated=isAuthenticated, Anime=records, start=start, num_records=num_records )
            else:
                return render_template('login.html')
        else:
            # At this point, the details submitted by user is incorrect, therefore we sent appropriate HTTP Status code
            return make_response(jsonify({'error': 'Invalid information received.'}), 400)
    except Exception as e:
        log.error("Failed to login: {0}".format(e))
        return make_response(jsonify({'error': 'Server encountered an error.'
                                               ' Contact the administrator if problem persists.'}), 500)


@app.route('/logout')
def logout():
    query = Anime.query.order_by(Anime.anime_id.asc())
    # retrieve query parameters for controlling amount of records retrieved
    start = request.args.get('offset', default=1, type=int)
    num_records = request.args.get('limit', default=10, type=int)
    # retrieve the data as pages
    records = query.paginate(start, num_records).items

    isAuthenticated = False
    return render_template('index.html', isAuthenticated=isAuthenticated, Anime=records, start=start, num_records=num_records )

@app.route('/form')
def form():
    return render_template('AnimeData.html')

@app.route('/add_by_form',methods=['POST'])
def add_by_form():
    anime=Anime(request.form['anime_id'],request.form['name'],request.form['genre'],request.form['anime_type'],request.form['episodes'],request.form['rating'],request.form['members'])
    db.session.add(anime)
    db.session.commit()
    return redirect(url_for("form"))

@app.route('/upload')
def upload():
   return render_template('upload.html')
	
@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file():
   if request.method == 'POST':
      f = request.files['file']
      f.save(secure_filename(f.filename))
      f=loadAnimeFromFile(f)
      return 'file uploaded successfully'   #just need to upload contents

if __name__ == "__main__":
    print("Running From the Command line")
