# svblog - tools.py
# Author: James Gray
# June 2013
#
# This file contains several functions used by app.py.

from flask import session, flash
from user import User

VALID_EXTENSIONS = ['pdf', 'png', 'jpg', 'jpeg', 'gif', 'html', 'css']

def get_user(username):
	"""Query the user database for an instance of a given username."""
	return User.query.filter_by(name=username).first()

def valid_file(filename):
	"""Determines if a file contains an allowed extension."""
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in VALID_EXTENSIONS

def valid_user(name):
	"""Redirects a user to the login page if they attempt to
	load a page to which they do not have access."""

	if 'logged_in' in session and session['logged_in'] == name:
		error = None
	elif get_user(name) is None:
		error = "User does not exist."
	else:
		error = "Must be logged in as %s to access this page." % name

	return error

def display(error):
	"""Displays an error if one has been encountered."""
	if error is not None:
		flash("Error: " + error)