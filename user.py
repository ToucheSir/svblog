# svblog - user.py
# Author: James Gray
# June 2013
#
# This file contains the User class, which
# flask-demo uses to create instances of user
# objects to be added to the user database.

from datetime import datetime
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
DATABASE_URI = 'sqlite://///home/brianc/projects/svblog/data/users.db'
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI


# Create SQLAlchemy object for user database
udb = SQLAlchemy(app)


class User(udb.Model):
    """Creates a user object."""

    # Initialize columns
    id = udb.Column(udb.Integer, primary_key=True)
    name = udb.Column(udb.String(80), unique=True)
    pw_hash = udb.Column(udb.String(160))
    creation_date = udb.Column(udb.DateTime)
    posting_enabled = udb.Column(udb.Boolean)
    theme = udb.Column(udb.String(80))

    def __init__(self, username, password):
        self.name = username

        # Get an instance of the user object from the
        # database if it exists.
        db_instance = User.query.filter_by(name=username).first()

        if db_instance is None:
            # Generate a hash for the given password, set posting
            # to be enabled, and set the account creation date.
            self.__set_pw(password)
            self.creation_date = datetime.now()
            self.posting_enabled = True
            self.theme = 'blue'

    def __set_pw(self, password):
        """
        Generates a hash for the given password, to be
        stored in the database.
        """
        self.pw_hash = generate_password_hash(password)

    def check_pw(self, password):
        """
        Checks a password against the stored hash.
        """
        return check_password_hash(self.pw_hash, password)

    def __repr__(self):
        return '<User %r>' % self.name
