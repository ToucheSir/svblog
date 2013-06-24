# svblog - app.py
# Author: James Gray
# June 2013
#
# This file contains the main Flask
# application logic for the project.

import os
from datetime import datetime, timedelta
from flask import Flask, request, session, redirect, \
    url_for, render_template, flash, send_from_directory
from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug import secure_filename
from tools import get_user, has_file_access, valid_file, valid_user, display
from user import User, udb
from upload import Upload, fdb
from entry import Entry, edb

app = Flask(__name__)
app.config.from_pyfile('settings.cfg')

def init_db():
    """
    Create the initial user and file database tables.
    """
    udb.create_all()
    fdb.create_all()
    edb.create_all()

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
            # After 5 days, disable posting and uploading for the user.
            # This is so that the campers' blogs act as snapshots
            # of their week at camp, and to prevent the posting or
            # uploading of questionable content to their camp-affiliated
            # blog.
            current_date = datetime.now()
            if current_date >= user_instance.creation_date + timedelta(days=5):
                user_instance.posting_enabled = False
                udb.session.commit()

            session['logged_in'] = username
            session['posting_enabled'] = user_instance.posting_enabled
            flash('Successfully logged in.')
            return redirect(url_for('entries', name=username))
    else:
        return render_template('login.html')

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
    session.pop('posting_enabled', None)
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
            session['posting_enabled'] = user_instance.posting_enabled
            return redirect(url_for('entries', name=username))

    display(error)
    return render_template('create.html')

@app.route('/<name>/', methods=['GET', 'POST'])
def entries(name):
    """
    This page presents a user's blog posts and file uploads,
    allowing visitors to download the files individually.
    """

    if get_user(name) is not None:
        entries = [e for e in Entry.query.all()]
        entries.reverse()
        uploads = [dict(userid=f.userid, filename=f.filename) \
            for f in Upload.query.all()]

        if request.method == "POST":
            title = request.form['title']
            text = request.form['text']

            entry_instance = Entry(name, title, text)
            edb.session.add(entry_instance)
            edb.session.commit()

            flash('Post successful!')
            return redirect(url_for('entries', name=name))
        else:
            return render_template('entries.html', username=name, \
                uploads=uploads, entries=entries)
    else:
        display("User does not exist.")
        return redirect(url_for('login'))

@app.route('/<name>/upload/', methods=['GET', 'POST'])
def upload(name):
    """
    This page allows a user to upload a text or image file.
    """

    # Refuse access if posting is disabled for the user.
    if "posting_enabled" in session and session['posting_enabled'] == False:
        error = "Access denied."
        display(error)
        if 'logged_in' in session:
            return redirect(url_for('entries', name=session['logged_in']))
        else:
            return redirect(url_for('login'))

    # Check if the user is logged in before allowing to upload files.
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
                return redirect(url_for('entries', name=name))
            else:
                flash("Invalid filename or file type.")
        return render_template('upload.html', username=name)

    # If an error occurs, display the error and
    # redirect to the appropriate page.
    display(error)
    if 'logged_in' in session:
        return redirect(url_for('upload', name=session['logged_in']))
    else:
        return redirect(url_for('login'))

@app.route('/<name>/<filename>')
def uploaded_file(name, filename):
    """
    This page will fetch a given file from the uploads folder.
    """
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == "__main__":
    init_db()
    app.run()
