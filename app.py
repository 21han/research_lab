"""

"""
from flask import Flask, redirect, url_for, request, flash, render_template, session
from flask import render_template
import sqlite3
from flask import request
import logging
import pandas as pd

import os
import secrets
from PIL import Image
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

from datetime import datetime, timedelta
# from flask_jwt import JWT, jwt_required, current_identity
# from authlib.integrations.flask_client import OAuth

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

app = Flask(__name__)

app.config['SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alchemist.db'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


# @app.route('/')
# def hello_world():
#     return 'Hello, World!'


def get_user_strategies(user_id):
    conn = sqlite3.connect("alchemist.db")
    strategies = pd.read_sql(f"select * from strategies where user_id = {user_id};", conn)
    return strategies


@app.route('/strategies')
def all_strategy():
    # TODO remove hard code of user after integration with Michael
    current_user_id = 0
    all_user_strategies = get_user_strategies(current_user_id)

    # display all user strategy as a table on the U.I.
    return render_template('strategies.html', df=all_user_strategies)


def get_strategy_location(strategy_id):
    conn = sqlite3.connect("alchemist.db")
    strategies = pd.read_sql(
        f"select * from strategies where strategy_id = {strategy_id};",
        conn
    )
    s_loc = strategies['strategy_location'].iloc[0]
    logger.info(f"[db] - {s_loc}")
    return s_loc


@app.route('/strategy')
def display_strategy():
    strategy_id = request.args.get('id')
    strategy_location = get_strategy_location(strategy_id)
    with open(f"strategies/{strategy_location}/src/main.py") as f:
        code_snippet = f.read()
    return render_template('strategy.html', code=code_snippet)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        # # admin
        # if form.email.data == 'admin@backtesting.com' and form.password.data == 'admin':
        #     flash('Welcome boss!', 'success')
        #     return redirect(url_for('admin'))

        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')

    return render_template('login.html', title='Login', form=form)


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/home")
@login_required
def home():
    return render_template('home.html')


@app.route("/admin", methods=['GET', 'POST'])
# @login_required
def admin():
    return render_template('admin.html')


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/about")
def about():
    return render_template('about.html', title='About')


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)

    # strategy = db.relationship('Strategy', backref='location', lazy=True)
    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class UpdateAccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')


# class Strategy(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     location = db.Column(db.Text, nullable=False)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#
#     # title = db.Column(db.String(100), nullable=False)
#     # date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
#     # content = db.Column(db.Text, nullable=False)
#
#     def __repr__(self):
#         return f"Strategy('{self.id}', '{self.date_posted}' by '{self.user_id}')"


# # Session config
# app.secret_key = os.getenv("APP_SECRET_KEY")
# app.config['SESSION_COOKIE_NAME'] = 'google-login-session'
# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)

# # oAuth Setup
# oauth = OAuth(app)
# google = oauth.register(
#     name='google',
#     client_id=os.getenv("GOOGLE_CLIENT_ID"),
#     client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
#     access_token_url='https://accounts.google.com/o/oauth2/token',
#     access_token_params=None,
#     authorize_url='https://accounts.google.com/o/oauth2/auth',
#     authorize_params=None,
#     api_base_url='https://www.googleapis.com/oauth2/v1/',
#     userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',  # This is only needed if using openId to fetch user info
#     client_kwargs={'scope': 'openid email profile'},
# )
#
# @app.route('/')
# @login_required
# def hello_world():
#     email = dict(session)['profile']['email']
#     return f'Hello, you are logge in as {email}!'
#
# @app.route('/login')
# def login():
#     google = oauth.create_client('google')  # create the google oauth client
#     redirect_uri = url_for('authorize', _external=True)
#     return google.authorize_redirect(redirect_uri)
#
# @app.route('/authorize')
# def authorize():
#     google = oauth.create_client('google')  # create the google oauth client
#     token = google.authorize_access_token()  # Access token from google (needed to get user info)
#     resp = google.get('userinfo')  # userinfo contains stuff u specificed in the scrope
#     user_info = resp.json()
#     user = oauth.google.userinfo()  # uses openid endpoint to fetch user info
#     # Here you use the profile/user data that you got and query your database find/register the user
#     # and set ur own data in the session not the profile from google
#     session['profile'] = user_info
#     session.permanent = True  # make the session permanant so it keeps existing after broweser gets closed
#     return redirect('/')
#
# @app.route('/logout')
# def logout():
#     for key in list(session.keys()):
#         session.pop(key)
#     return redirect('/')


# class Post(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(100), nullable=False)
#     date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
#     content = db.Column(db.Text, nullable=False)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#
#     def __repr__(self):
#         return f"Post('{self.title}', '{self.date_posted}')"
#


def main():
    app.run(debug=True, threaded=True, host='0.0.0.0', port='5000')


if __name__ == "__main__":
    main()
