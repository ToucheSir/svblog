# MicroBlog - tools.py
# Author: James Gray
# June 2013
#
# This file contains several functions used by app.py.

from flask import session, flash
from user import User
from upload import Upload

VALID_EXTENSIONS = ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif']

def get_user(username):
	"""Query the user database for an instance of a given username."""
	return User.query.filter_by(name=username).first()

def has_file_access(username, filename):
	"""Query the file database for an instance of a given filename to
	determine access privileges."""
	if Upload.query.filter_by(userid=username, filename=filename).first() is not None:
		return True
	return False

def valid_file(filename):
	"""Determines if a file contains an allowed extension."""
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in VALID_EXTENSIONS

def valid_user(name):
	"""Redirects a user to the login page if they attempt to
	access a page belonging to another user."""
	if 'logged_in' in session and session['logged_in'] == name:
		error = None
	elif get_user(name) is None:
		error = "User %s does not exist." % name
	else:
		error = "Must be logged in as %s to access this page." % name

	return error

def display(error):
	"""Displays an error if one has been encountered."""
	if error is not None:
		flash("Error: " + error)