# MicroBlog - user.py
# Author: James Gray
# June 2013
#
# This file contains the User class, which
# flask-demo uses to add and fetch user instances
# to and from a user database.

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite://///Users/jamesgray/Desktop/Science Venture/microblog/data/users.db'

# Create SQLAlchemy object for user database
udb = SQLAlchemy(app)

class User(udb.Model):
	"""Creates a user object and stores in an SQLAlchemy database."""

	# Initialize columns
	id = udb.Column(udb.Integer, primary_key=True)
	name = udb.Column(udb.String(80), unique=True)
	pw_hash = udb.Column(udb.String(160))

	def __init__(self, username, password):
		self.name = username

		# Get an instance of the user object from the
		# database if it exists.
		db_instance = User.query.filter_by(name=username).first()

		if db_instance is None:
			# Generate a hash for the given password.
			self.__set_pw(password)

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
