"""
application.py
"""

import collections
import datetime
import importlib
import json
import logging
import os
import secrets
import shutil
import time

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
import flask
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from PIL import Image
from dash import Dash
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
from flask import Flask, flash, redirect, url_for
from flask import render_template
from flask import request
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, current_user, login_required, \
    login_user, logout_user
from flask_mail import Message, Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from oauthlib.oauth2 import WebApplicationClient
from pylint import epylint as lint
from pylint.lint import Run
from tqdm import trange
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, \
    ValidationError
from flask_moment import Moment
from errors.handlers import errors
from user import OAuthUser
from utils import s3_util, rds

logging.getLogger('botocore').setLevel(logging.CRITICAL)
logging.getLogger('boto3').setLevel(logging.CRITICAL)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

application = Flask(__name__)

moment = Moment(application)
application.config.from_object("config")

db = SQLAlchemy(application)
bcrypt = Bcrypt(application)
login_manager = LoginManager(application)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# create an s3 client
s3_client = s3_util.init_s3_client()

# email for send reset password token
mail = Mail(application)

# error handler
application.register_blueprint(errors)

# Google OAuth login client
client = WebApplicationClient(application.config["GOOGLE_CLIENT_ID"])
migrate = Migrate(application, db)

# dash object
dash_app = Dash(__name__, server=application, external_stylesheets=[dbc.themes.BOOTSTRAP],
                url_base_pathname='/dash_plots/')
dash_app.validation_layout = True
dash_app._layout = html.Div()
# global variables for update dash dynamically depending on different user
OptionList = []
pnl_paths = []
TOTAL_CAPITAL = 10 ** 6


# endpoint routes


@application.route("/OAuth_login")
def oauth_login():
    """
    OAuth login route
    :return:
    """
    google_provider_cfg = requests.get(application.config["GOOGLE_DISCOVERY_URL"]).json()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"]
    )
    logger.info(request_uri)
    return redirect(request_uri)


@application.route("/OAuth_login/callback")
def callback():
    """
    OAuth login callback function from google auth page
    :return:
    """
    code = request.args.get("code")
    google_provider_cfg = requests.get(application.config["GOOGLE_DISCOVERY_URL"]).json()
    token_endpoint = google_provider_cfg["token_endpoint"]
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(application.config["GOOGLE_CLIENT_ID"], application.config["GOOGLE_CLIENT_SECRET"])
    )
    client.parse_request_body_response(json.dumps(token_response.json()))
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    url, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(url, headers=headers, data=body)
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        user_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        user_name = userinfo_response.json()["given_name"]
        current_user.id = int(unique_id)
    else:
        return "User email not available or not verified by Google", 400
    user = OAuthUser(
        id_=unique_id, username=user_name, email=user_email, image_file=picture
    )
    if not OAuthUser.get(unique_id):
        OAuthUser.create(unique_id, user_name, user_email, picture)
    login_user(user)
    return redirect(url_for("home"))


@login_manager.user_loader
def load_user(user_id):
    """
    load user from OAuth user table if id is found otherwise load user from user table
    :param user_id:
    :return:
    """
    if not OAuthUser.get(user_id):
        return User.query.get(int(user_id))
    return OAuthUser.get(user_id)


@application.route("/home")
@login_required
def home():
    """
    home page after user login

    :return: redirect user to upload page
    """
    if current_user.is_authenticated:
        conn = rds.get_connection()
        if isinstance(current_user.email, str):
            userid = pd.read_sql(
                f"select id from backtest.user where email = '{current_user.email}';",
                conn
            )
            current_user.id = int(userid['id'].iloc[0])
        else:
            current_user.email = str(current_user.email['email'].iloc[0])
            userid = pd.read_sql(
                f"select id from backtest.OAuth_user where email = '{current_user.email}';",
                conn
            )
            current_user.id = int(userid['id'].iloc[0])
        return redirect('upload')
    return render_template('welcome.html', title='About')


@application.route("/")
@application.route("/welcome")
def about():
    """Welcome page of Backtesting platform, introduce features and functionalities of the platform

    Returns:
        function: render welcome.html page with title About
    """
    return render_template('welcome.html', title='About')


@application.route("/login", methods=['GET', 'POST'])
def login():
    """authenticate current user to access the platform with valid email and
       password registered in user table

    Returns:
        function: render login.html page with title Login, redirect user to home page
        when successfully authenticate
    """
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password,
                                               form.password.data) and user.is_approved == "Yes":
            login_user(user, remember=form.remember.data)
            current_user.email = form.email.data
            current_user.user_type = user.user_type
            current_user.id = user.id
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            else:
                if user.user_type == "user":
                    return redirect(url_for('home'))
                elif user.user_type == "admin":
                    return redirect(url_for('admin'))
        else:
            flash('Login Unsuccessful. Please check email and password. Waiting for admin approval',
                  'danger')
    return render_template('login.html', title='Login', form=form)


@application.route("/logout")
def logout():
    """
    logout current user
    :return:
    """
    logout_user()
    return redirect(url_for('about'))


@application.route("/upload")
@login_required
def upload():
    """home page of the backtesting platform, login is required to access this page

    Returns:
        function: render home.html page with context of login user's username
    """
    current_user_init()
    context = {"username": current_user.username,
               "report": "",
               "message": "Your upload check detail will be shown here"}
    return render_template('upload.html', **context)


@application.route("/upload", methods=["POST"])
@login_required
def upload_strategy():
    """upload user strategy to alchemist database
    
    Returns:
        string: return message of upload status with corresponding pylint score
    test_id = num -> it is for testing
    need to avoid local and cloud storage difference
    cloud path: e.g. s3://com34156-strategies/{user_id}/strategy_num/{strategy_name}.py

    local has its own count
    and cloud has its own count
    """
    current_user_init()
    if "user_file" not in request.files:
        return "No user_file is specified"
    if "strategy_name" not in request.form:
        return "No strategy name specified"
    file = request.files["user_file"]
    name = request.form["strategy_name"]
    if name == "":
        return "Strategy name may not be empty"

    if len(name) >= 50:
        return "Strategy name should not be greater than 50 characters"

    message = check_upload_file(file)
    if message != "OK":
        return message

    # get the number of folders
    bucket_name = application.config["S3_BUCKET"]

    userid = str(current_user.id)
    response = check_py_validity(file, userid)

    if '/' not in response:
        # move coverage to same page
        # this will be checked by frontend
        return response

    local_path = response.split(':')[1]
    status = response.split(':')[0]
    # Run pylint again to get the message
    # to pylint_stdout, which is an IO.byte
    (pylint_stdout, _) = lint.py_run(local_path, return_std=True)
    pylint_message = pylint_stdout.read()
    pylint_message = clean_pylint_output(pylint_message)

    # if the file is invalid, need to stop here
    local_prefix = '/'.join(local_path.split('/')[:-1])
    if "error" in status:
        shutil.rmtree(local_prefix)
        logger.info("pytest does not pass for a valid .py file")
        report = (
            "Your strategy has error or is not able to run! "
            "Correct your file and upload again\n\n"
            "*************Backend Check Information**************\n\n"
        )
        # append information
        report = report + pylint_message
        context = {
            "username": current_user.username,
            "report": report,
            "message": "Your upload check detail will be shown here"
        }
        return render_template('upload.html', **context)

    test_id = request.args.get('test_id')

    conn = rds.get_connection()
    cursor = conn.cursor()
    if test_id is not None:
        test_id = int(test_id)
        logger.info("uploading testing file...")
        cnt_loc = test_id
    else:
        logger.info("uploading user file...")
        cursor.execute(
            "SELECT MAX(strategy_id) as max_strategy FROM backtest.strategies"
        )
        first = cursor.fetchone()
        cnt_loc = first['max_strategy']
        cnt_loc += 1
        logger.info("max + 1 is - %s", cnt_loc)

    cloud_new_folder = "strategy" + str(cnt_loc)
    strategy_folder = os.path.join(userid, cloud_new_folder)
    # upload to s3 bucket
    filepath = upload_strategy_to_s3(
        local_path, bucket_name, strategy_folder
    )

    logger.info(f"file uploads to path {filepath}")

    # store in database
    cursor = conn.cursor()
    timestamp = str(datetime.datetime.utcnow())

    query = "INSERT INTO backtest.strategies (user_id, strategy_location, \
        last_modified_date, last_modified_user, strategy_name) \
                VALUES (%s,%s,%s,%s,%s)"
    username = current_user.username
    cursor.execute(
        query, (current_user.id, filepath, timestamp, username, name)
    )

    conn.commit()

    # remove the local file
    shutil.rmtree(local_prefix)

    logger.info(f"affected rows = {cursor.rowcount}")
    message = "Your strategy " + name + \
              " is uploaded successfully!"

    context = {"username": current_user.username,
               "report": pylint_message,
               "message": message}
    return render_template('upload.html', **context)


@application.route("/register", methods=['GET', 'POST'])
def register():
    """register a new user to the platform database

    Returns:
        function: render register.html page with title Register
    """
    form = RegistrationForm()
    if form.validate_on_submit():
        if len(set(form.password.data)) < 5:
            raise ValidationError('password should contain 5 or more unique characters')
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')

        if len(form.username.data) < 2 or len(form.username.data) > 20:
            raise ValidationError

        user = User(username=form.username.data,
                    email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(
            f'Your account has been created! An admin is reviewing your registration request, please check-in again '
            f'in 24 hours',
            'success')
        return redirect(url_for('login'))
    return render_template(
        'register.html', title='Register', form=form)


@application.route("/admin", methods=['GET', 'POST'])
@login_required
def admin():
    """render admin user page

    Returns:
        function: render falsk admin page
    """
    return redirect('/admin/')


@application.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    """display current user's account information and allows the current user to
       update their username, email and upload profile image

    Returns:
        function : render account.html page with title account
    """
    current_user_init()
    form = UpdateAccountForm()
    if hasattr(current_user, "password") and form.validate_on_submit():
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
    else:
        flash('Google account info cannot be updated', 'warning')
    if hasattr(current_user, "password"):
        image_file = url_for('static',
                             filename='profile_pics/' + current_user.image_file)
    else:
        image_file = current_user.image_file
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


@application.route('/strategies/<int:page_num>')
@login_required
def all_strategy(page_num):
    """display all user strategy as a table on the U.I.

    Returns:
        function: render strategies.html page
    """
    if not isinstance(current_user.id, int):
        conn = rds.get_connection()
        current_user.email = str(current_user.email['email'].iloc[0])
        userid = pd.read_sql(
            f"select id from backtest.OAuth_user where email = '{current_user.email}';",
            conn
        )
        current_user.id = int(userid['id'].iloc[0])
        user_name = pd.read_sql(
            f"select username from backtest.OAuth_user where email = '{current_user.email}';",
            conn
        )
        current_user.username = str(user_name['username'].iloc[0])
    current_user_id = current_user.id
    username = current_user.username

    strategies = Strategies.query.filter_by(
        user_id=current_user_id).order_by(
        Strategies.last_modified_date.desc()
    ).paginate(per_page=5, page=page_num, error_out=True)

    return render_template(
        'strategies.html',
        df=strategies,
        username=username
    )


def get_strategy_to_local(strategy_location):
    """
    get strategy from s3_resource to local
    :param strategy_location: s3_resource loction
    :return: local strategy file path
    """
    current_user_init()
    s3_resource = s3_util.init_s3()

    if "/" not in strategy_location:
        raise ValueError("Invalid Strategy Location.")

    s3_url_obj = s3_util.S3Url(strategy_location)
    user_folder = f"strategies/user_id_{current_user.id}"
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
        open(f"{user_folder}/__init__.py", 'a').close()

    local_strategy_path = f"{user_folder}/current_strategy.py"
    logger.info(
        f"-- s3_resource bucket: {s3_url_obj.bucket} -- s3_resource key: {s3_url_obj.key}")

    s3_resource.Bucket(s3_url_obj.bucket).download_file(
        s3_url_obj.key,
        local_strategy_path
    )

    return local_strategy_path


@application.route('/strategy')
def display_strategy():
    """display select strategy with id

    Returns:
        function: strategy.html
    """
    strategy_id = request.args.get('id')
    strategy_location = get_strategy_location(strategy_id)

    # step 1: aws cp file to local
    local_strategy_path = get_strategy_to_local(strategy_location)

    # step 2: display content
    with open(local_strategy_path) as file:
        code_snippet = file.read()

    return render_template(
        'strategy.html', strategy_id=strategy_id, code=code_snippet, num_bars=1)


@application.route('/strategy', methods=["POST"])
@login_required
def delete_strategy():
    """
    delete strategy
    :return: strategy html
    """
    strategy_id = request.args.get('id')
    strategy_location = get_strategy_location(strategy_id)

    delete_strategy_by_user(strategy_location, strategy_id)
    return redirect('strategies/1')


@application.route('/log_strategy')
def backtest_strategy():
    """
    to help debugging and log strategy before entering into backtest loop
    :return:
    """
    strategy_id = request.args.get('id')
    logger.info("**strategy id %s", str(strategy_id))
    return "nothing"


@application.route('/backtest_progress')
def backtest_progress():
    """
    backtest progress
    :return:
    """
    current_user_init()
    strategy_id = request.args.get('id')
    current_usr_id = current_user.id

    n_days_back = 365  # we backtest using past 1 year's data
    past_n_days = [
        datetime.datetime.utcnow() -
        datetime.timedelta(
            days=i) for i in range(n_days_back)]
    past_n_days = sorted(past_n_days)

    s_module = importlib.import_module(
        f"strategies.user_id_{current_usr_id}.current_strategy")

    current_strategy = s_module.Strategy()

    try:
        strategy_cap = current_strategy.INIT_CAPITAL
    except Exception as e_message:
        logger.error(e_message)

    def backtest():
        """
        to backtest by iterating through each day
        :return:
        """
        pnl_df = {
            'pnl': []
        }
        trades = collections.deque(maxlen=2)  # note: we only keep track of today and last day
        trades.append({'price': None, 'position': None})
        for day_x in trange(n_days_back):
            one_tenth = n_days_back // 10
            if day_x % one_tenth == 0:
                time.sleep(1)
            progress = {0: min(100 * day_x // n_days_back, 100)}
            trades.append({'price': current_strategy.get_price(), 'position': current_strategy.get_position()})
            total_value_x = compute_pnl(trades[0].get('position'), trades[0].get('price'),
                                        trades[1].get('price'), strategy_cap)
            pnl_df['pnl'].append(total_value_x)
            ret_string = f"data:{json.dumps(progress)}\n\n"
            yield ret_string

        yield f"data:{json.dumps({0: 100})}\n\n"
        pnl_df['date'] = past_n_days
        key = persist_to_s3(pnl_df, current_usr_id, strategy_id)
        update_backtest_db(strategy_id, application.config["S3_BUCKET"], key)

    return flask.Response(backtest(), mimetype='text/event-stream')


def persist_to_s3(pnl_df, current_usr, strategy_id):
    """
    persist pnl dataframe to s3 under user and strategy path
    :param pnl_df:
    :param current_usr:
    :param strategy_id:
    :return: the key we persist to
    """
    pnl_df = pd.DataFrame(pnl_df)
    file_name = f'strategies/user_id_{current_usr}/backtest.csv'
    try:
        pnl_df.to_csv(file_name, index=True)
    except Exception as e_msg:
        logger.info(e_msg)
    key = f"{current_usr}/backtest_{strategy_id}.csv"
    _s3_client = s3_util.init_s3_client()
    _s3_client.upload_file(file_name, application.config["S3_BUCKET"], key)
    return key


def update_backtest_db(strategy_id, bucket, key):
    """
    update backtest result to database
    :param strategy_id:
    :param bucket:
    :param key:
    :return:
    """
    conn = rds.get_connection()
    cursor = conn.cursor()
    timestamp = datetime.datetime.utcnow()

    query = "REPLACE INTO backtest.backtests (strategy_id, backtest_id," \
            "pnl_location, last_modified_date) \
                    VALUES (%s,%s,%s,%s)"
    cursor.execute(
        query, (strategy_id, strategy_id,
                f"s3://{bucket}/{key}", timestamp)
    )
    conn.commit()


def compute_pnl(previous_day_position, prev_day_price, current_day_price, init_cap):
    """
    compute total values on a given day
    :param previous_day_position: previous day position
    :param prev_day_price: previous day price
    :param current_day_price: current day price
    :param init_cap initial capital
    :return:
    """
    pnl = 0
    total_positions_usd = 0
    if previous_day_position is None or prev_day_price is None:
        return pnl
    for ticker, percent in previous_day_position.items():
        ticker_quantity = init_cap * percent / prev_day_price[ticker]
        total_positions_usd += current_day_price[ticker] * ticker_quantity
    pnl = total_positions_usd - init_cap
    return pnl


@application.route('/results/', methods=['GET'])
@login_required
def user_results():
    """
    Redirect to dosh route for visualization.
    :return:
    """
    current_user_init()
    user_id = current_user.id
    if type(user_id) == pd.DataFrame:
        user_id = int(user_id['id'].iloc[0])
    update_layout(user_id)
    return redirect('/dash_plots')


@application.route('/dash_plots/', methods=['GET'])
@login_required
def render_reports():
    """
    Redirect flask endpoint to dash server endpoint.
    :return:
    """
    return flask.redirect('/dash_plot')


@application.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    """
    send reset password request
    :return:
    """
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@application.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    """
    reset secret token
    :param token:
    :return:
    """
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)


def send_reset_email(user):
    """
    send reset password request to the registered email
    :param user:
    :return:

    """
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


# helper functions
def current_user_init():
    """
    current_user.field for oauth is pandas.Dataframe
    we need to refactor current_user object
    
    current_user is a global object
    """
    conn = rds.get_connection()
    if isinstance(current_user.email, str):
        userid = pd.read_sql(
            f"select id from backtest.user "
            f"where email = '{current_user.email}';",
            conn
        )
        current_user.id = int(userid['id'].iloc[0])
    else:
        current_user.email = str(current_user.email['email'].iloc[0])
        userid = pd.read_sql(
            f"select * from backtest.OAuth_user "
            f"where email = '{current_user.email}';",
            conn
        )
        current_user.id = int(userid['id'].iloc[0])
        current_user.username = str(userid['username'].iloc[0])
        current_user.image_file = str(userid['image_file'].iloc[0])


def save_picture(form_picture):
    """ save user uploaded profile picture with formatted size in database

    Args:
        form_picture (picture in jpg format): user upload picture

    Returns:
        string: formatted picture string
    """
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(application.root_path, 'static/profile_pics',
                                picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn


def get_user_strategies(user_id):
    """get user strategies according to user id

    Args:
        user_id (int): user identifier

    Returns:
        [type]: [description]
    """
    strategies = rds.get_all_strategies(user_id)
    return strategies


def get_strategy_location(strategy_id):
    """obtain the location of the strategy

    Args:
        strategy_id (int): strategy id

    Returns:
        location: location of the strategy
    """
    conn = rds.get_connection()
    strategies = pd.read_sql(
        f"select * from backtest.strategies where strategy_id = {strategy_id};",
        conn
    )
    s_loc = strategies['strategy_location'].iloc[0]
    logger.info("[db] - %s}", s_loc)
    return s_loc


def allowed_file(filename):
    """allowed file extension
    Args:
        filename ([string]): the file name including the extension

    Returns:
        [bool]: yes for allowed, no for not allowed
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in application.config[
               "ALLOWED_EXTENSIONS"]


def check_upload_file(file):
    """check flask uploaded file
    These attributes are also available
    file.filename          # The actual name of the file
    file.content_type
    file.content_length
    file.mimetype
    Args:
        file ([request]): in flask.request["file"], io.byte type
    """
    if file.filename == "":
        return "Please select a file"

    if not allowed_file(file.filename):
        return "Your file extension type is not allowed"
    if not file:
        return "File not found. Please upload it again"
    return "OK"


def check_py_validity(file, userid):
    """run pylint on file to check if correct
    store file in local
    Args:
        file (str): flask file
        userid(int)
        new_foler: new_folder to save
    """
    # keep a local copy of the file to run pylint
    local_folder = os.path.join('strategies/', userid)
    if not os.path.exists(local_folder):
        os.makedirs(local_folder)
    local_cnt = sum([1 for _ in os.listdir(local_folder)])
    new_folder = "strategy" + str(local_cnt + 1)

    local_strategy_folder = os.path.join(local_folder, new_folder)
    os.makedirs(local_strategy_folder)
    local_path = os.path.join(local_strategy_folder, file.filename)
    logger.info("local testing path is %s", local_path)
    file.save(local_path)
    result = Run([local_path], do_exit=False)
    # may be need threshold
    logger.info(result.linter.stats)

    if "global_note" not in result.linter.stats or \
            result.linter.stats['global_note'] <= 0:
        logger.info("wrong file, remove")

        prefix = "has error:"
    else:
        prefix = "successful:"

    logger.info(prefix)
    if "successful" in prefix:
        logger.info("uploaded: file has pylint score %s",
                    result.linter.stats['global_note'])
    else:
        logger.info("check does not pass")
    response = prefix + local_path
    return response


def upload_strategy_to_s3(
        file, bucket_name, file_prefix):
    """
    Notice that, in addition to ACL we set the ContentType key
    in ExtraArgs to the file's content type. This is because by
    default, all files uploaded to an S3 bucket have their
    content type set to binary/octet-stream, forcing the
    browser to prompt users to download the files instead of
    just reading them when accessed via a public URL (which can
    become quite annoying and frustrating for images and pdfs
    for example)

    Args:
        file ([str]): local file path
        bucket_name (str): bucket name
        file_prefix (str): file prefix, like linxiao/strategy1

    Returns:
        [str]: upload file path
    """
    filename = file.split('/')[-1]
    upload_path = os.path.join(file_prefix, filename)
    try:
        logger.info("uploading file: to path %s", upload_path)

        s3_client.upload_file(
            file,
            bucket_name,
            upload_path,
        )

    except Exception as exp_msg:
        logger.info("Something Happened: %s", exp_msg)
        raise

    return "{}{}".format(application.config["S3_LOCATION"], upload_path)


def delete_strategy_by_user(filepath, strategy_id=None):
    """delete a strategy

    Args:
        filepath (s3): real strategy path in s3, which is
        the same as database

    ASSUME THE FILEPATH is always valid
    NOTE: Need to delete both s3 and database
    :param strategy_id: default None
    """
    logger.info(f"*****{filepath}\n\n")

    bucket_name = application.config["S3_BUCKET"]
    split_path = filepath.split('/')
    prefix = "/".join(split_path[3:])

    response = s3_client.list_objects_v2(
        Bucket=bucket_name, Prefix=prefix
    )
    object_cnt = response["KeyCount"]
    conn = rds.get_connection()
    cursor = conn.cursor()
    delete_strategy_qry = "DELETE FROM backtest.strategies \
                 WHERE strategy_location = %s"
    delete_backtest_qry = f"DELETE FROM backtest.backtests \
                 WHERE strategy_id = {int(strategy_id)}" if strategy_id else "SELECT @@VERSION;"
    if object_cnt == 0:
        cursor.execute(delete_backtest_qry)
        cursor.execute(delete_strategy_qry, (filepath,))
        conn.commit()
        logger.info("affected rows = %d", cursor.rowcount)
        logger.info("Delete file from Database")
    else:
        s3_object = response['Contents'][0]  # assume only one match
        logger.info("affected objects = %d", object_cnt)
        logger.info("Delete file from AWS")
        s3_client.delete_object(Bucket=bucket_name, Key=s3_object['Key'])
        logger.info("Delete file from AWS")
        cursor.execute(delete_backtest_qry)
        cursor.execute(delete_strategy_qry, (filepath,))
        conn.commit()
        logger.info("affected rows = %d", cursor.rowcount)
        logger.info("Delete file from Database")


def clean_pylint_output(pylint_message):
    """clean pylint message

    Args:
        pylint_message (pylint_message): 
        we need to clean pylint output to give
        a cleaner output
    """
    break_lines = pylint_message.split('\n')
    clean_output = []
    for line in break_lines:
        clean_line = line
        if ".py:" in line:
            # target line
            components = line.split(':')
            file = components[0].split('/')[-1]
            components[0] = file
            clean_line = ':'.join(components)
        clean_output.append(clean_line)

    clean_message = '\n'.join(clean_output)
    return clean_message


# Forms: registration, login, account

class RegistrationForm(FlaskForm):
    """Form contains registered user information

    Args:
        FlaskForm (form): a flask form object

    Raises:
        ValidationError: user name exists in the current user table
        ValidationError: email address exists in the current user table
    """
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=10, max=100)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(),
                                                                     EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_password(self, password):
        """
        check if password is in valid format
        :param password:
        :return:
        """
        if len(set(password.data)) < 5:
            raise ValidationError('Password should contain at least 5 unique characters')

    def validate_username(self, username):
        """check if username exists in the current user table

        Args:
            username (string): input username of current user

        Raises:
            ValidationError: the input username exists in the user table
        """
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        """check if input email address exists in the current user table

        Args:
            email (string): email address with valid email format

        Raises:
            ValidationError: current email exists in user table
        """
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')


class LoginForm(FlaskForm):
    """create a flask form object for login user

    Args:
        FlaskForm (flaskform): FlaskForm object
    """
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class UpdateAccountForm(FlaskForm):
    """create a flask form contains users' updated information of their account

    Args:
        FlaskForm (flaskform): Flaskform object

    Raises:
        ValidationError: updated user name exists in user table
        ValidationError: updated email exists in user table
    """
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture',
                        validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        """
        check if updated username is duplicate
        :param username: new user name
        :return: None
        """
        if username.data != current_user.username:
            user = User.query.filter_by(
                username=username.data).first()
            if user:
                raise ValidationError(
                    'That username is taken. Please choose a different one.')

    def validate_email(self, email):
        """
        check update email is empty
        :param email: new email
        :return: None
        """
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError(
                    'That email is taken. Please choose a different one.')


class RequestResetForm(FlaskForm):
    """
    Request reset form
    """
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        """

        :param email:
        :return:
        """
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')


class ResetPasswordForm(FlaskForm):
    """
    Reset Password form
    """
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')


# Database Related Objects

class Strategies(db.Model):
    user_id = db.Column(db.DECIMAL(25))
    strategy_location = db.Column(db.VARCHAR(1024))
    strategy_id = db.Column(db.Integer, primary_key=True)
    last_modified_date = db.Column(db.DATETIME)
    last_modified_user = db.Column(db.VARCHAR(32))
    strategy_name = db.Column(db.VARCHAR(64))


class StrategiesModelView(ModelView):
    """
    Strategies view
    """

    def is_accessible(self):
        """
        check if user can access admin page
        :return: admin user redirect to admin page
        """
        return current_user.is_authenticated and current_user.user_type == "admin"

    def inaccessible_callback(self, name, **kwargs):
        """
        return 403 page if not access admin page
        :param name:
        :param kwargs:
        :return: 403 error page
        """
        return self.render('errors/308.html')


class User(db.Model, UserMixin):
    """User object

    Args:
        db (SQLAlchemy database): SQLAlchemy database
        UserMixin (userMixin): inherit userMixin object
        provide default implementations of User object.

    Returns:
        None: none
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(
        db.String(20),
        nullable=False,
        default='default.jpg')
    password = db.Column(db.String(60), nullable=False)

    is_approved = db.Column(db.String(10), nullable=False, default='No')
    user_type = db.Column(db.String(10), nullable=False, default='user')

    def get_reset_token(self, expires_sec=1800):
        """ get a reset token (expire in 1800 seconds)
        :param expires_sec: set the token expire period to 1800 seconds
        :return:
        """
        serialized = Serializer(application.config['SECRET_KEY'], expires_sec)
        return serialized.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        """ verify reset token

        :param token: secret token
        :return:
        """
        serialized = Serializer(application.config['SECRET_KEY'])
        try:
            user_id = serialized.loads(token)['user_id']
        except Exception as e_msg:
            logger.error(e_msg)
            return None
        return User.query.get(user_id)

    def __repr__(self):
        """
        :return: stirng contains userid, username, user email of user object
        """
        return f"User('{self.id}', '{self.username}', '{self.email}')"


class UserModelView(ModelView):
    """
    User view
    """

    def is_accessible(self):
        """
        check if user can access admin page
        :return: admin user redirect to admin page
        """
        return current_user.is_authenticated and current_user.user_type == "admin"

    def inaccessible_callback(self, name, **kwargs):
        """
        return 403 page if not access admin page
        :param name:
        :param kwargs:
        :return: 403 error page
        """
        return self.render('errors/308.html')


class HomePageView(BaseView):
    """
    Home page view
    """

    @expose('/')
    def index(self):
        """
        return to backtesting home page
        :return:
        """
        return self.render('welcome.html')

    def is_accessible(self):
        """
        admin user access
        :return:
        """
        return current_user.is_authenticated and current_user.user_type == "admin"

    def inaccessible_callback(self, name, **kwargs):
        """
        Non admin user cannot access this page
        :param name:
        :param kwargs:
        :return: redirect to login
        """
        return redirect(url_for('login'))


# admin
admin = Admin(application)
admin.add_view(HomePageView(name='Backtesting Platform', endpoint='home'))
admin.add_view(UserModelView(User, db.session))
admin.add_view(StrategiesModelView(Strategies, db.session))


# dash part
def fig_update(file_path):
    """
    Given the file path, return an updated fig graph to display.
    :param file_path: string, to get csv file.
    :return: figs, the styled graph.
    """

    cr_fig, sr_rolling, pnl_hist, pnl_df, fig_3d = None, None, None, None, None
    logger.info(file_path)
    if file_path is not None:
        split_path = file_path.split('/')
        prefix = "/".join(split_path[3:])

        bucket_name = application.config["S3_BUCKET"]
        csv_obj = s3_client.get_object(Bucket=bucket_name, Key=prefix)
        pnl_df = pd.read_csv(csv_obj['Body'])

        pnl_df['cusum'] = pnl_df['pnl'].cumsum()
        cr_fig = px.line(pnl_df, x='date', y='cusum')

        cr_fig.update_xaxes(
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            )
        )
        # 3d plot
        another_df = pd.DataFrame()
        another_df['normalized_pnl'] = pnl_df['pnl'].div(TOTAL_CAPITAL)
        another_df['date'] = pnl_df['date']
        another_df['rolling_risk'] = pnl_df['pnl'].iloc[1:].div(TOTAL_CAPITAL).rolling(3).std()
        another_df = another_df[another_df['rolling_risk'] < 30]
        risk_list = another_df['rolling_risk'].tolist()

        another_df['color'] = np.asarray([int(num) for num in risk_list])
        fig_3d = px.scatter_3d(another_df, x='date', y='rolling_risk', z='normalized_pnl',
                               color = 'color', width=800, height=800, opacity=0.7)

        # Rolling sharpe ratio plot
        pnl_df['rolling_SR'] = pnl_df.pnl.rolling(180).apply(lambda x: (x.mean() - 0.02) / x.std(), raw=True)

        pnl_df.fillna(0, inplace=True)
        sr_df = pnl_df[pnl_df['rolling_SR'] > 0]
        sr_rolling = go.Figure([go.Scatter(x=sr_df['date'], y=sr_df['rolling_SR'],
                                           line=dict(color="DarkOrange"), mode='lines+markers')])

        sr_rolling.update_xaxes(
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            )
        )
        mean = np.mean(sr_df['rolling_SR'])
        avg_title = "Average value={:.3f}".format(mean)
        sr_rolling.add_hline(y=mean, line_width=3, line_dash="dash", line_color="green",
                             annotation_text=avg_title,
                             annotation_position="bottom right")

        # pnl histogram plot
        pnl_hist = go.Figure()
        profit = pnl_df[pnl_df['pnl'] > 0]
        loss = pnl_df[pnl_df['pnl'] < 0]

        pnl_hist.add_trace(go.Bar(x=profit['date'], y=loss['pnl'],
                                  marker_color='crimson',
                                  name='loss'))
        pnl_hist.add_trace(go.Bar(x=loss['date'], y=profit['pnl'],
                                  marker_color='lightslategrey',
                                  name='profit'))

    return cr_fig, sr_rolling, pnl_hist, pnl_df, fig_3d

def new_plot():

    content_style = {
        "margin-left": "32rem",
        "margin-right": "2rem",
        "padding": "2rem 1rem",
    }
    global OptionList
    navbar = dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Home", href="https://localhost:5000/upload"),
                        style=dict(width='200%'), className="ml-2"),
            dbc.NavItem(dbc.NavLink("Strategies", href="https://localhost:5000/strategies/1"),
                        style=dict(width='200%'), className="ml-2"),
            html.Div(dcc.Dropdown(
                id='backtest_result',
                options=OptionList,
                placeholder="Select Backtest Result",
                style=dict(
                    width='200%',
                    verticalAlign="left"),
                className="dash-bootstrap"
            ), style={"width": "200%"}, )
        ],
        brand="Backtesting Platform",
        brand_href="https://localhost:5000/welcome",
        color="primary",
        dark=True,

    )

    contents = html.Div([
        navbar,
        html.Div(
            [
                html.H2('Cumulative Return',
                        style={'textAlign': 'center', 'font-family': 'Georgia'}),
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(dcc.Graph(id='pnl_fig'),
                                width={"size": 10, "offset": 2}),
                    ]
                )

            ],
            style=content_style
        ),

        html.Div(
            [
                html.H2('3D View of Daily Change',
                        style={'textAlign': 'center', 'font-family': 'Georgia'}),
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(dcc.Graph(id='fig_3d'),
                                width={"size": 10, "offset": 2}),
                    ] )

            ],
            style=content_style
        ),

        html.Div(
            [
                html.H2('Rolling Sharpe Ratio (6-months)',
                        style={'textAlign': 'center', 'font-family': 'Georgia'}),
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(dcc.Graph(id='sr_rolling'),
                                width={"size": 10, "offset": 2}),
                    ]
                )
            ],
            style=content_style
        ),

        html.Div(
            [
                html.H2('Profit and Loss histogram',
                        style={'textAlign': 'center', 'font-family': 'Georgia'}),
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(dcc.Graph(id='pnl_hist'),
                                width={"size": 10, "offset": 2}),
                    ]
                )

            ],
            style=content_style
        ),
        html.Div(id='table')
    ])
    return contents


@dash_app.callback(
    Output('pnl_fig', 'figure'),
    Output('fig_3d', 'figure'),
    Output('sr_rolling', 'figure'),
    Output('pnl_hist', 'figure'),
    Output('table', 'children'),
    Input('backtest_result', 'value'))
def update_graph(backtest_fp):
    """
    Dash callback function for update graphs depending on the chosen backtest file from dropdown bar.
    :param backtest_fp:
    :return:
    """
    table_style = {
        "position": "fixed",
        "top": 60,
        "left": 5,
        "bottom": 5,
        "width": "30rem",
        "padding": "2rem 1rem",
        "background-color": "#f8f9fa",
    }
    if backtest_fp is not None:

        pnl_fig, sr_rolling, pnl_hist, pnl_df, fig_3d = fig_update(backtest_fp)
        table_df = pnl_summary(pnl_df)
        table_comp = html.Div(
            [
                html.H2('Statistic Table',
                        style={'textAlign': 'center', 'font-family': 'Georgia',
                               'front_size': '30'}),
                html.Hr(),
                dt.DataTable(
                    data=table_df.to_dict('records'),
                    columns=[{'id': c, 'name': c} for c in table_df.columns],

                    style_cell={'front_size': '30px'},
                    style_cell_conditional=[
                        {
                            'if': {'column_id': 'Backtest'},
                            'textAlign': 'left'
                        },

                        {
                            'if': {'column_id': 'Category'},
                            'textAlign': 'left'
                        },

                    ],
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        },
                        {
                            'if': {'column_id': 'Category'},
                            'fontWeight': 'bold'
                        }
                    ],
                    style_header={
                        'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold'
                    }
                ),
            ], style=table_style
        )
        return pnl_fig, fig_3d, sr_rolling, pnl_hist, table_comp

    else:
        raise PreventUpdate


def get_plot(strategy_ids):
    """
    Get two dictionaries, one mapping from strategy id to strategy name,
    another is mapping from strategy id to strategy location. Update the global variables for OptionList and pnl_paths.
    :param strategy_ids: a list of strategy ids.
    :return: True if the global variable pnl_paths and OptionList updated, otherwise False
    """
    strategy_names = {}
    id_paths = {}
    global pnl_paths
    if len(strategy_ids) > 0:
        backtests = rds.get_all_locations(strategy_ids)
        for idx, strategy_id in enumerate(strategy_ids):
            strategy_names[strategy_id] = backtests['strategy_name'].iloc[idx]
            id_paths[strategy_id] = backtests['pnl_location'].iloc[idx]

        global OptionList
        OptionList = [{'label': v, 'value': id_paths[k]} for k, v in strategy_names.items()]
        pnl_paths = [id_paths[k] for k in strategy_names.keys()]
        return True

    return False


def pnl_summary(data):
    """
    Statistic analysis of backtest result.
    :param data: A dataframe including the backtest results, contains date and pnl two columns.
    :return: A dataframe for making the table, it contains two columns,
    category name and corresponding values.
    """
    data['cumulative'] = data['pnl'].cumsum()
    result = {'Category': [], 'Value': []}
    total_date = data.shape[0]
    return_value = (data['cumulative'].iloc[-1]) / TOTAL_CAPITAL

    num_format = "{:,}".format

    # Annual return
    annual_return = round(return_value / (total_date / 365) * 100, 2)
    result['Category'].append('Annual Return')
    result['Value'].append(num_format(annual_return) + '%')

    # Cumulative return
    cumulative_return = round(return_value * 100, 2)
    result['Category'].append('Cumulative Return')
    result['Value'].append(num_format(cumulative_return) + '%')

    # Annual volatility
    daily_change = data['pnl'].iloc[1:].div(TOTAL_CAPITAL)
    annual_volatility = round(daily_change.std() * np.sqrt(365), 2)
    result['Category'].append('Annual Volatility')
    result['Value'].append(num_format(annual_volatility))

    # Sharpe ratio
    ratio_value = data['pnl'].div(TOTAL_CAPITAL)
    sharpe_ratio = round(ratio_value.mean() / ratio_value.std() * np.sqrt(365), 2)
    result['Category'].append('Sharpe Ratio')
    result['Value'].append(num_format(sharpe_ratio))

    # Max Dropdown
    max_drop = round((np.max(data['pnl']) - np.min(data['pnl'])) / np.max(data['pnl']), 2)
    result['Category'].append('Max Dropdown')
    result['Value'].append(num_format(max_drop))

    # Skew
    skew = round(data['pnl'].skew(), 2)
    result['Category'].append('Skew')
    result['Value'].append(num_format(skew))

    # Kurtosis
    kurtosis = round(data['pnl'].kurtosis(), 2)
    result['Category'].append('Kurtosis')
    result['Value'].append(num_format(kurtosis))

    return pd.DataFrame(result)


def update_layout(user_id):
    """
    Get all the valid backtes results and given the corresponding stratefy ids to dash.
    :param user_id: current user_id
    :return: True if the user has backtest results, otherwise False.
    """
    all_ids = list(rds.get_all_backtests(user_id)['strategy_id'])
    all_strategy_ids = [str(id) for id in all_ids]
    if len(all_strategy_ids) > 0:
        get_plot(all_strategy_ids)
        return True
    get_plot([])
    return False


if __name__ == "__main__":
    application.debug = True

    dash_app.layout = new_plot
    dash_app.title = 'Visualization'
    app_embeds = DispatcherMiddleware(application, {
        '/dash_plot': dash_app.server
    })

    run_simple('localhost', 5000, app_embeds, use_reloader=True, use_debugger=True, ssl_context="adhoc")
