# Python standard libraries
import json
import os

# Third-party libraries
from flask import request
from oauthlib.oauth2 import WebApplicationClient
import requests

# Internal imports
from user import User


class GoogleLogin():
    '''
    It will interact wit Google oauth to login for a user
    '''
    GOOGLE_CLIENT_ID = None
    GOOGLE_CLIENT_SECRET = None
    GOOGLE_DISCOVERY_URL = None
    client = None
    mongo = None

    def __init__(self, mongo) -> None:
        self.mongo = mongo
        self.GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
        self.GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
        self.GOOGLE_DISCOVERY_URL = os.getenv('GOOGLE_DISCOVERY_URL')
        # OAuth 2 client setup
        self.client = WebApplicationClient(self.GOOGLE_CLIENT_ID)

    def get_google_provider_cfg(self):
        return requests.get(self.GOOGLE_DISCOVERY_URL).json()

    def callback(self):
        # Get authorization code Google sent back to you
        code = request.args.get("code")

        # Find out what URL to hit to get tokens that allow you to ask for
        # things on behalf of a user
        google_provider_cfg = self.get_google_provider_cfg()
        token_endpoint = google_provider_cfg["token_endpoint"]

        # Prepare and send a request to get tokens! Yay tokens!
        token_url, headers, body = self.client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url,
            redirect_url=request.base_url,
            code=code
        )
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(self.GOOGLE_CLIENT_ID, self.GOOGLE_CLIENT_SECRET),
        )

        # Parse the tokens!
        self.client.parse_request_body_response(
            json.dumps(token_response.json()))

        # Now that you have tokens (yay) let's find and hit the URL
        # from Google that gives you the user's profile information,
        # including their Google profile image and email
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = self.client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        # You want to make sure their email is verified.
        # The user authenticated with Google, authorized your
        # app, and now you've verified their email through Google!
        if userinfo_response.json().get("email_verified"):
            unique_id = userinfo_response.json()["sub"]
            users_email = userinfo_response.json()["email"]
            picture = userinfo_response.json()["picture"]
            users_name = userinfo_response.json()["given_name"]
        else:
            return "User email not available or not verified by Google.", 400

        # Create a user in your db with the information provided
        # by Google
        user = User.create(
            self.mongo, unique_id, users_name, users_email, picture
        )
        print(user)
        # Doesn't exist? Add it to the database.
        if not User.get(self.mongo, unique_id):
            User.create(self.mongo, unique_id,
                        users_name, users_email, picture)

        return user

    def login_request_uri(self):
        # Find out what URL to hit for Google login
        google_provider_cfg = self.get_google_provider_cfg()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        # Use library to construct the request for Google login and provide
        # scopes that let you retrieve user's profile from Google
        request_uri = self.client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=request.base_url + "/callback",
            scope=["openid", "email", "profile"],
        )

        return request_uri
