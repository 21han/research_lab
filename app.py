"""
app.py
"""
import logging
import os
import secrets
import shutil
from datetime import datetime

import pandas as pd
from PIL import Image

from flask import Flask, flash, redirect, url_for
from flask import render_template
from flask import request
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, current_user, login_required, \
    login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
# pylint
from pylint.lint import Run
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, \
    ValidationError
from db_utils import rds

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

app = Flask(__name__)
app.config.from_object("config")

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


# endpoint routes


@login_manager.user_loader
def load_user(user_id):
    """[summary]

    Args:
        user_id ([type]): [description]

    Returns:
        [type]: [description]
    """
    return User.query.get(int(user_id))


@app.route("/")
@app.route("/welcome")
def about():
    """[summary]

    Returns:
        [type]: [description]
    """
    return render_template('welcome.html', title='About')


@app.route("/home")
@login_required
# current page is login required, which means not logging will be redirected
def home():
    """[summary]

    Returns:
        [type]: [description]
    """
    context = {"username": current_user.username}
    return render_template('home.html', **context)


@app.route("/home", methods=["POST"])
@login_required
def upload_strategy():
    """[summary]

    Returns:
        [type]: [description]
    """
    if "user_file" not in request.files:
        return "No user_file is specified"
    if "strategy_name" not in request.form:
        return "Strategy name may not be empty"
    file = request.files["user_file"]
    name = request.form["strategy_name"]
    '''
        These attributes are also available

        file.filename               # The actual name of the file
        file.content_type
        file.content_length
        file.mimetype

    '''
    if file.filename == "":
        return "Please select a file"

    if not allowed_file(file.filename):
        return "Your file extension type is not allowed"

    if not file:
        return "File not found. Please upload it again"

    username = current_user.username
    folder = 'strategies/' + username
    if not os.path.exists(folder):
        os.makedirs(folder)

    # get the number of folders

    cnt = len([_ for _ in os.listdir(folder)])
    new_folder = "strategy" + str(cnt + 1)

    strategy_folder = os.path.join(folder, new_folder)
    os.makedirs(strategy_folder)  # it must be new file

    # name file to be main.py
    filepath = os.path.join(strategy_folder, "main.py")
    file.save(filepath)
    result = Run([filepath], do_exit=False)

    # may be need threshold
    logger.info(result.linter.stats)
    if "global_note" not in result.linter.stats or \
            result.linter.stats['global_note'] <= 0:
        logger.info("wrong file, remove")
        shutil.rmtree(strategy_folder)
        return "Your strategy has error or is not able to run! \
            correct your file and upload again"

    # store in database

    score = result.linter.stats['global_note']
    conn = rds.get_connection()
    cursor = conn.cursor()
    timestamp = str(datetime.now())

    query = "INSERT INTO backtest.strategies (user_id, strategy_location, \
            last_modified_date, last_modified_user, strategy_name) \
                    VALUES (%s,%s,%s,%s,%s)"
    cursor.execute(
        query, (current_user.id, filepath, timestamp, username, name)
    )

    conn.commit()
    logger.info(f"affected rows = {cursor.rowcount}")

    message = "Your strategy " + name + \
              " is uploaded successfully with pylint score " + \
              str(score) + "/10.00"

    return message


@app.route("/login", methods=['GET', 'POST'])
def login():
    """[summary]

    Returns:
        [type]: [description]
    """

    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        # admin
        if form.email.data == 'admin@backtesting.com' and form.password.data \
                == 'admin':
            flash('Welcome boss!', 'success')
            return redirect(url_for('admin'))
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password,
                                               form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(
                url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password',
                  'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/register", methods=['GET', 'POST'])
def register():
    """[summary]

    Returns:
        [type]: [description]
    """
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user = User(username=form.username.data,
                    email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Your account has been created! You are now able to log in',
              'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/admin", methods=['GET', 'POST'])
# @login_required
def admin():
    """[summary]

    Returns:
        [type]: [description]
    """
    return render_template('admin.html')


@app.route("/logout")
def logout():
    """[summary]

    Returns:
        [type]: [description]
    """
    logout_user()
    return redirect(url_for('home'))


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    """[summary]

    Returns:
        [type]: [description]
    """
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
    image_file = url_for('static',
                         filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


@app.route('/strategies')
def all_strategy():
    """[summary]

    Returns:
        [type]: [description]
    """
    current_user_id = 0
    all_user_strategies = get_user_strategies(current_user_id)
    # display all user strategy as a table on the U.I.
    return render_template('strategies.html', df=all_user_strategies)


@app.route('/strategy')
def display_strategy():
    """[summary]

    Returns:
        [type]: [description]
    """
    strategy_id = request.args.get('id')
    strategy_location = get_strategy_location(strategy_id)
    with open(f"strategies/{strategy_location}/src/main.py") as f:
        code_snippet = f.read()
    return render_template('strategy.html', code=code_snippet)


# helper functions


def save_picture(form_picture):
    """[summary]

    Args:
        form_picture ([type]): [description]

    Returns:
        [type]: [description]
    """
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics',
                                picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn


def get_user_strategies(user_id):
    """[summary]

    Args:
        user_id ([type]): [description]

    Returns:
        [type]: [description]
    """
    strategies = rds.get_all_strategies(user_id)
    return strategies


def get_strategy_location(strategy_id):
    """[summary]

    Args:
        strategy_id ([type]): [description]

    Returns:
        [type]: [description]
    """
    conn = rds.get_connection()
    strategies = pd.read_sql(
        f"select * from strategies where strategy_id = {strategy_id};",
        conn
    )
    s_loc = strategies['strategy_location'].iloc[0]
    logger.info(f"[db] - {s_loc}")
    return s_loc


def allowed_file(filename):
    """[summary]

    Args:
        filename ([type]): [description]

    Returns:
        [type]: [description]
    """

    # allowed file extenstion
    # see config.py
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config[
               "ALLOWED_EXTENSIONS"]


# Forms: registration, login, account


class RegistrationForm(FlaskForm):
    """[summary]

    Args:
        FlaskForm ([type]): [description]

    Raises:
        ValidationError: [description]
        ValidationError: [description]
    """
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(),
                                                 EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        """[summary]

        Args:
            username ([type]): [description]

        Raises:
            ValidationError: [description]
        """
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                'That username is taken. Please choose a different one.')

    def validate_email(self, email):
        """[summary]

        Args:
            email ([type]): [description]

        Raises:
            ValidationError: [description]
        """
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(
                'That email is taken. Please choose a different one.')


class LoginForm(FlaskForm):
    """[summary]

    Args:
        FlaskForm ([type]): [description]
    """
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class UpdateAccountForm(FlaskForm):
    """[summary]

    Args:
        FlaskForm ([type]): [description]

    Raises:
        ValidationError: [description]
        ValidationError: [description]
    """
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture',
                        validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError(
                    'That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError(
                    'That email is taken. Please choose a different one.')


# User object

class User(db.Model, UserMixin):
    """[summary]

    Args:
        db ([type]): [description]
        UserMixin ([type]): [description]

    Returns:
        [type]: [description]
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)

    # strategy = db.relationship('Strategy', backref='location', lazy=True)
    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


def main():
    app.run(debug=True, threaded=True, host='0.0.0.0', port='5000')


if __name__ == "__main__":
    main()
