"""
OAuth user class
"""
import pandas as pd
from flask_login import UserMixin

from utils import rds


class OAuthUser(UserMixin):
    """
    OAuth user
    """
    def __init__(self, id_, username, email, image_file):
        self.id = id_
        self.username = username
        self.email = email
        self.image_file = image_file


    @staticmethod
    def get(user_id):
        """
        get user id
        :param user_id:
        :return:
        """
        conn = rds.get_connection()
        cursor = conn.cursor()
        user = cursor.execute(
            f"SELECT * FROM backtest.OAuth_user WHERE id = {user_id};"
        )

        userid = pd.read_sql(
            f"select id from backtest.OAuth_user where id = '{user_id}';",
            conn
        )
        name = pd.read_sql(
            f"select username from backtest.OAuth_user where id = '{user_id}';",
            conn
        )
        email = pd.read_sql(
            f"select email from backtest.OAuth_user where id = '{user_id}';",
            conn
        )
        image = pd.read_sql(
            f"select image_file from backtest.OAuth_user where id = '{user_id}';",
            conn
        )

        if not user:
            return None

        user = OAuthUser(
            id_=userid, username=name, email=email, image_file=image
        )
        return user


    @staticmethod
    def create(id_, username, email, image_file):
        """
        create OAuth user object and insert into rds oauth user table
        :param id_:
        :param username:
        :param email:
        :param image_file:
        :return:
        """
        conn = rds.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO backtest.OAuth_user (id, username, email, image_file)"
            "VALUES (%s, %s, %s, %s)",
            (id_, username, email, image_file)
        )
        conn.commit()
