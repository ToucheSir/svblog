# MicroBlog - app.py
# Author: James Gray
# June 2013
#
# This file contains the main Flask
# application logic for the project.

import os
from flask import Flask, request, session, redirect, \
    url_for, render_template, flash, send_from_directory
from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug import secure_filename
from tools import get_user, has_file_access, valid_file, valid_user, display
from user import User, udb
from upload import Upload, fdb

app = Flask(__name__)
app.config.from_pyfile('settings.cfg')

def init_db():
	"""
	Create the initial user and file database tables.
	"""
	udb.create_all()
	fdb.create_all()

@app.after_request
def after_request(response):
	"""
	Add header to prevent browser from caching pages.
	This will prevent a user from accessing their files
	after logging out, or after logging in as another user.
	"""
	response.headers['Cache-Control'] = 'private, max-age=0'
	return response

@app.route('/login/', methods=['GET', 'POST'])
def login():
	"""
	Allows a user to log in to their account.
	Note that the index page redirects here by default.
	"""
	error = None
	if request.method == 'POST':
		username = request.form['username']

		# Check to see if the user exists.
		user_instance = get_user(username)
		if user_instance is None:
			error = 'Invalid username.'
		elif not user_instance.check_pw(request.form['password']):
			error = 'Invalid password.'
		else:
			session['logged_in'] = username
			flash('Successfully logged in.')
			return redirect(url_for('files', name=username))

	display(error)
	return render_template('login.html')

@app.route('/')
def index():
	return redirect(url_for('login'))

@app.route('/logout/')
def logout():
	"""
	Logs a user out before returning to the login screen.
	"""
	session.pop('logged_in', None)
	flash('Successfully logged out.')
	return redirect(url_for('login'))

@app.route('/create/', methods=['GET', 'POST'])
def create():
	"""
	Allows a user to create a new account.
	"""
	error = None
	if request.method == 'POST':
		# Get submitted values from fields.
		username = request.form['username']
		password = request.form['password-a']

		# Check if there is a user by the same username in the database.
		user_instance = get_user(username)
		if user_instance is not None:
			error = 'Username is already taken.'
		elif password != request.form['password-b']:
			error = 'Passwords do not match.'
		else:
			# Add user to the database and log user in.
			user_instance = User(username, password)
			udb.session.add(user_instance)
			udb.session.commit()

			flash('Account created!')
			session['logged_in'] = username
			return redirect(url_for('files', name=username))

	display(error)
	return render_template('create.html')

@app.route('/user/<name>/files/')
@app.route('/user/<name>/', alias=True)
def files(name):
	"""
	This page presents a user's uploaded files, and allows
	the user to download them individually.
	"""
	error = valid_user(name)
	if error is None:
		uploads = [dict(userid=f.userid, filename=f.filename) \
			for f in Upload.query.all()]
		return render_template('files.html', username=name, uploads=uploads)

	# If an error occurs, display the error and
	# redirect to the appropriate page.
	display(error)
	if 'logged_in' in session:
		return redirect(url_for('files', name=session['logged_in']))
	else:
		return redirect(url_for('login'))

@app.route('/user/<name>/upload/', methods=['GET', 'POST'])
def upload(name):
	"""
	This page allows a user to upload a text or image file.
	"""
	error = valid_user(name)
	if error is None:
		if request.method == 'POST':
			file = request.files['file']
			if file and valid_file(file.filename):
				# Sanitize the filename, save the file to the uploads
				# folder, and add the file and owner info to the file database.
				filename = secure_filename(file.filename)
				file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
				file_instance = Upload(name, filename)
				
				# Insert the upload object into the database.
				fdb.session.add(file_instance)
				fdb.session.commit()

				flash('File was uploaded successfully.')
				return redirect(url_for('files', name=name))
			else:
				flash("Invalid filename or file type.")
		return render_template('upload.html')

	# If an error occurs, display the error and
	# redirect to the appropriate page.
	display(error)
	if 'logged_in' in session:
		return redirect(url_for('upload', name=session['logged_in']))
	else:
		return redirect(url_for('login'))

@app.route('/user/<name>/files/<filename>')
def uploaded_file(name, filename):
	"""
	This page will fetch a given file from the uploads folder,
	provided the user has privileges to access the file.
	"""
	error = valid_user(name)
	if error is None:
		if has_file_access(session['logged_in'], filename):
			return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
		else:
			error = "Access denied."

	# If an error occurs, display the error and
	# redirect to the appropriate page.
	display(error)
	if 'logged_in' in session:
		return redirect(url_for('files', name=session['logged_in']))
	else:
		return redirect(url_for('login'))

if __name__ == "__main__":
	init_db()
	app.run()
