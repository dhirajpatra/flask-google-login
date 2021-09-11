from flask_login import UserMixin
from pymongo import mongo_client


class User(UserMixin):
    def __init__(self, id_, name, email, profile_pic):
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic

    @staticmethod
    def all(mongo):
        user = mongo.db.users.find()
        if not user:
            return None
        return user

    @staticmethod
    def get(mongo, id):
        user = mongo.db.users.find_one_or_404({"id": id})
        if not user:
            return None

        user = User(
            id_=user['id'], name=user['name'], email=user['email'], profile_pic=user['profile_pic']
        )
        return user

    @staticmethod
    def create(mongo, id_, name, email, profile_pic):
        users = mongo.db.users
        user = {
            "id": id_,
            "name": name,
            "email": email,
            "profile_pic": profile_pic
        }
        id = users.insert_one(user).inserted_id
        # get the new user details
        user = mongo.db.users.find_one_or_404({"_id": id})
        if not user:
            return None

        user = User(
            id_=user['id'], name=user['name'], email=user['email'], profile_pic=user['profile_pic']
        )
        return user
