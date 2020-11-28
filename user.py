from flask_login import UserMixin
from utils import rds
import pandas as pd


class OAuthUser(UserMixin):
    def __init__(self, id_, username, email, image_file):
        self.id = id_
        self.username = username
        self.email = email
        self.image_file = image_file


    @staticmethod
    def get(user_id):
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
        em = pd.read_sql(
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
            id_=userid, username=name, email=em, image_file=image
        )
        return user


    @staticmethod
    def create(id_, username, email, image_file):
        conn = rds.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO backtest.OAuth_user (id, username, email, image_file)"
            "VALUES (%s, %s, %s, %s)",
            (id_, username, email, image_file)
        )
        conn.commit()

