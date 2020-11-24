from flask_login import UserMixin
from db import get_db
from utils import rds
import pandas as pd


class OAuth_User(UserMixin):
    def __init__(self, id_, username, email, image_file):
        self.id = id_
        self.username = username
        self.email = email
        self.image_file = image_file

    @staticmethod
    def get(user_id):
        db = get_db()
        user = db.execute(
            "SELECT * FROM OAuth_user WHERE id = ?", (user_id,)
        ).fetchone()

        if not user:
            return None
        user = OAuth_User(
            id_=user[0], username=user[1], email=user[2], image_file=user[3]
        )

        return user

    # @staticmethod
    # def get(user_id):
    #     conn = rds.get_connection()
    #     cursor = conn.cursor()
    #
    #     user = cursor.execute(
    #         f"SELECT * FROM backtest.OAuth_user WHERE id = {user_id};"
    #     )
    #
    #     if not user:
    #         return None
    #
    #     user = OAuth_User(
    #         id_=user[0], username=user[1], email=user[2], image_file=user[3]
    #     )
    #     return user


    @staticmethod
    def create(id_, username, email, image_file):
        db = get_db()
        db.execute(
            "INSERT INTO OAuth_user (id, username, email, image_file)"
            "VALUES (?, ?, ?, ?)",
            (id_, username, email, image_file)
        )
        db.commit()

    # @staticmethod
    # def create(id_, username, email, image_file):
    #     conn = rds.get_connection()
    #     cursor = conn.cursor()
    #     cursor.execute(
    #         "INSERT INTO backtest.OAuth_user (id, username, email, image_file)"
    #         "VALUES (%s, %s, %s, %s)",
    #         (id_, username, email, image_file)
    #     )
    #     conn.commit()
