"""
application.py
"""

import datetime
import importlib
import json
import logging
import os
import secrets
import shutil
import subprocess
import threading
import time
import collections
import webbrowser
import flask
import pandas as pd
from PIL import Image
from flask import Flask, flash, redirect, url_for
from flask import render_template
from flask import request
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, current_user, login_required, \
    login_user, logout_user
from flask_mail import Message, Mail
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from pylint.lint import Run
from pylint import epylint as lint
from tqdm import trange
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, \
    ValidationError
from utils import s3_util, rds
import threading
import subprocess
import webbrowser
from errors.handlers import errors
from utils import mock_historical_data


logging.getLogger('botocore').setLevel(logging.CRITICAL)
logging.getLogger('boto3').setLevel(logging.CRITICAL)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

application = Flask(__name__)

application.config.from_object("config")

db = SQLAlchemy(application)
bcrypt = Bcrypt(application)
login_manager = LoginManager(application)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# create an s3 client
s3_client = s3_util.init_s3_client()

mail = Mail(application)
application.register_blueprint(errors)

# endpoint routes


@login_manager.user_loader
def load_user(user_id):
    """User object with input user id

    Args:
        user_id (int): primary key of user table

    Returns:
        User: User object with input user id
    """
    return User.query.get(int(user_id))


@application.route("/")
@application.route("/welcome")
def about():
    """Welcome page of Backtesting platform, introduce features and functionalities of the platform

    Returns:
        function: render welcome.html page with title About
    """
    return render_template('welcome.html', title='About')


@application.route("/home")
@login_required
def home():
    """
    home page after user login

    :return: redirect user to upload page
    """
    if current_user.is_authenticated:
        conn = rds.get_connection()
        userid = pd.read_sql(
            f"select id from backtest.user where email = '{current_user.email}';",
            conn
        )
        current_user.id = int(userid['id'].iloc[0])
        return redirect('upload')
    return render_template('welcome.html', title='About')


@application.route("/upload")
@login_required
def upload():
    """home page of the backtesting platform, login is required to access this page

    Returns:
        function: render home.html page with context of login user's username
    """
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
    """
    if "user_file" not in request.files:
        return "No user_file is specified"
    if "strategy_name" not in request.form:
        return "Strategy name may not be empty"
    file = request.files["user_file"]
    name = request.form["strategy_name"]
    
    message = check_upload_file(file)
    if message != "OK":
        return message

    # get the number of folders
    bucket_name = application.config["S3_BUCKET"]

    # path: e.g. s3://com34156-strategies/{user_id}/strategy_num/{strategy_name}.py
    
    conn = rds.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT MAX(strategy_id) as m FROM backtest.strategies"
    )
    for id in cursor.fetchall():
        cnt_loc = id['m']
        break

    logger.info("max + 1 is - %s", cnt_loc+1)
    new_folder = "strategy" + str(cnt_loc+1)

    userid = str(current_user.id)
    response = check_py_validity(file, userid, new_folder)

    if '/' not in response:
        return response
    
    local_path = response
    # Run pylint again to get the message
    # to pylint_stdout, which is an IO.byte
    (pylint_stdout, _) = lint.py_run(local_path, return_std=True)
    pylint_message = pylint_stdout.read()
    
    strategy_folder = os.path.join(userid, new_folder)
    # upload to s3 bucket
    filepath = upload_strategy_to_s3(
        local_path, bucket_name, strategy_folder
    )

    logger.info(f"file uploads to path {filepath}")

    # store in database
    cursor = conn.cursor()
    timestamp = str(datetime.datetime.now())

    query = "INSERT INTO backtest.strategies (user_id, strategy_location, \
            last_modified_date, last_modified_user, strategy_name) \
                    VALUES (%s,%s,%s,%s,%s)"

    username = current_user.username
    cursor.execute(
        query, (current_user.id, filepath, timestamp, username, name)
    )

    conn.commit()
    
    local_folder = os.path.join('strategies/', userid)
    local_strategy_folder = os.path.join(local_folder, new_folder)
    shutil.rmtree(local_strategy_folder)

    logger.info(f"affected rows = {cursor.rowcount}")
    message = "Your strategy " + name + \
              " is uploaded successfully under " + \
              "/".join(filepath.split('/')[-2:]) + " path"
              
    context = {"username": current_user.username,
               "report": pylint_message,
               "message": message}
    return render_template('upload.html', **context)


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
                                               form.password.data):
            login_user(user, remember=form.remember.data)
            current_user.email = form.email.data
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password',
                  'danger')
    logger.info("NOT AUTHENTICATED")
    return render_template('login.html', title='Login', form=form)


@application.route("/register", methods=['GET', 'POST'])
def register():
    """register a new user to the platform database

    Returns:
        function: render register.html page with title Register
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
    return render_template(
        'register.html', title='Register', form=form)


@application.route("/admin", methods=['GET', 'POST'])
def admin():
    """render admin user page

    Returns:
        function: render admin.html page
    """
    return render_template('admin.html')


@application.route("/logout")
def logout():
    """logout current user and kill the user's session

    Returns:
        function: redirect user to welcome page
    """
    logout_user()
    return redirect('welcome')


@application.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    """display current user's account information and allows the current user to
       update their username, email and upload profile image

    Returns:
        function : render account.html page with title account
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


@application.route('/strategies')
@login_required
def all_strategy():
    """display all user strategy as a table on the U.I.

    Returns:
        function: render strategies.html page
    """

    current_user_id = current_user.id
    username = current_user.username
    all_user_strategies = get_user_strategies(current_user_id)
    return render_template(
        'strategies.html',
        df=all_user_strategies,
        username=username
    )


def get_strategy_to_local(strategy_location):
    """
    get strategy from s3_resource to local
    :param strategy_location: s3_resource loction
    :return: local strategy file path
    """

    conn = rds.get_connection()
    userid = pd.read_sql(
        f"select id from backtest.user where email = '{current_user.email}';",
        conn
    )
    current_usr = userid

    s3_resource = s3_util.init_s3()

    if "/" not in strategy_location:
        raise ValueError("Invalid Strategy Location.")

    s3_url_obj = s3_util.S3Url(strategy_location)

    user_folder = f"strategies/user_id_{current_usr}"
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
    delete stratege
    :return: strageti html
    """
    strategy_id = request.args.get('id')
    strategy_location = get_strategy_location(strategy_id)

    delete_strategy_by_user(strategy_location)
    return redirect('strategies')


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
    strategy_id = request.args.get('id')
    current_usr = current_user.id

    s_module = importlib.import_module(
        f"strategies.user_id_{current_usr}.current_strategy")

    n_days_back = 365  # we backtest using past 1 year's data
    past_n_days = [
        datetime.datetime.today() -
        datetime.timedelta(
            days=i) for i in range(n_days_back)]
    past_n_days = sorted(past_n_days)

    def backtest():
        pnl_df = {
            'pnl': []
        }
        """ to backtest by iterating through each day"""
        trades = collections.deque(maxlen=2)  # note: we only keep track of today and last day
        for day_x in trange(n_days_back):
            one_tenth = n_days_back // 10
            if day_x % one_tenth == 0:
                time.sleep(1)
            progress = {0: min(100 * day_x // n_days_back, 100)}
            ret_string = f"data:{json.dumps(progress)}\n\n"
            yield ret_string
            day_x_position = s_module.Strategy().get_position()
            day_x = past_n_days[day_x]
            total_value_x = compute_total_value(day_x, day_x_position)
            position_df['value'].append(total_value_x)
            pnl_df['pnl'].append(total_value_x)

        yield f"data:{json.dumps({0: 100})}\n\n"
        pnl_df['date'] = past_n_days
        key = persist_to_s3(pnl_df, current_usr, strategy_id)
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
    pnl_df.to_csv(file_name, index=True)
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
    timestamp = datetime.datetime.now()

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
    if previous_day_position is None:
        return pnl
    for ticker, percent in previous_day_position.items():
        ticker_quantity = init_cap * percent / prev_day_price[ticker]
        total_positions_usd += current_day_price[ticker] * ticker_quantity
    pnl = total_positions_usd - init_cap
    return pnl


@application.route('/results')
@login_required
def display_results():
    """display all the backtest results with selection option
        Returns:
            function: results.html
    """
    # display all user backtest results as a table on the U.I.
    current_user_id = current_user.id
    user_backests = get_user_backtests(current_user_id)
    return render_template("results.html", df=user_backests)


@application.route('/plots', methods=['POST'])
# @login_required
def run_dash():
    """
    Run dash application first in this function
        and then open then dash url in the new window.
        It will go back to /results for other selections.
    :return: redirect to /results
    """
    strategy_ids = request.form.get('ids').split(',')
    cmd = strategy_ids
    cmd.insert(0, 'dash_app.py')
    cmd.insert(0, 'python')

    proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    t = threading.Thread(target=output_reader, args=(proc,))
    t.start()

    try:
        time.sleep(3)
        webbrowser.open('http://localhost:8050')
        # assert b'Directory listing' in resp.read()
        time.sleep(5)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=1)
            logger.info('== subprocess exited with rc =%d', proc.returncode)
        except subprocess.TimeoutExpired:
            logger.info('subprocess did not terminate in time')
    t.join()

    return redirect('/results')



@application.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    """
    send reset passwrod request
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
def output_reader(proc):
    """
    Check if subprocess works correctly.
    :param proc: process
    :return: None
    """
    for line in iter(proc.stdout.readline, b''):
        logger.info('got line: {0}'.format(line.decode('utf-8')), end='')


def get_user_backtests(user_id):
    """
    Get backtest dataframe from rds.
    :param user_id: user id
    :return: dataframe
    """
    backtests = rds.get_all_backtests(user_id)

    return backtests


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


def check_py_validity(file, userid, new_folder):
    """run pylint on file to check if correct

    Args:
        file (str): flask file
        userid(int)
        new_foler: new_folder to save
    """
    # keep a local copy of the file to run pylint
    local_folder = os.path.join('strategies/', userid)
    if not os.path.exists(local_folder):
        os.makedirs(local_folder)

    local_strategy_folder = os.path.join(local_folder, new_folder)
    os.makedirs(local_strategy_folder)
    local_path = os.path.join(local_strategy_folder, file.filename)
    logger.info(f"local testing path is {local_path}")
    file.save(local_path)
    result = Run([local_path], do_exit=False)

    # may be need threshold
    logger.info(result.linter.stats)
    
    if "global_note" not in result.linter.stats or \
            result.linter.stats['global_note'] <= 0:
        logger.info("wrong file, remove")

        shutil.rmtree(local_strategy_folder)
        return "Your strategy has error or is not able to run! \
            correct your file and upload again"

    logger.info("testing file has pylint score %s", 
                result.linter.stats['global_note'])
    return local_path

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
        logger("Something Happened: %s", exp_msg)
        return e

    return "{}{}".format(application.config["S3_LOCATION"], upload_path)


def delete_strategy_by_user(filepath):
    """delete a strategy

    Args:
        filepath (s3): real strategy path in s3, which is
        the same as database

    ASSUME THE FILEPATH is always valid
    NOTE: Need to delete both s3 and database
    """
    conn = rds.get_connection()
    bucket_name = application.config["S3_BUCKET"]
    split_path = filepath.split('/')
    prefix = "/".join(split_path[3:])

    response = s3_client.list_objects_v2(
        Bucket=bucket_name, Prefix=prefix
    )
    object_cnt = response["KeyCount"]
    s3_object = response['Contents'][0]  # assume only one match
    logger.info("affected objects = %d", object_cnt)
    logger.info("Delete file from AWS")
    s3_client.delete_object(Bucket=bucket_name, Key=s3_object['Key'])
    logger.info("Delete file from AWS")
    cursor = conn.cursor()
    query = "DELETE FROM backtest.strategies \
                WHERE strategy_location = %s"
    cursor.execute(query, (filepath,))
    conn.commit()
    logger.info("affected rows = %d", cursor.rowcount)
    logger.info("Delete file from Database")


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
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(),
                                                                     EqualTo('password')])
    submit = SubmitField('Sign Up')

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
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')


# User object

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

    def get_reset_token(self, expires_sec=1800):
        """ get a reset token (expire in 1800 seconds)

        :param expires_sec: set the token expire period to 1800 seconds
        :return:
        """
        s = Serializer(application.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        """ verify reset token

        :param token: secret token
        :return:
        """
        s = Serializer(application.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        """
        :return: stirng contains userid, username, user email of user object
        """
        return f"User('{self.id}', '{self.username}', '{self.email}')"


def main():
    """
    run application
    :return: None
    """
    application.run(debug=False, threaded=True, host='0.0.0.0', port='5000')


if __name__ == "__main__":
    main()
