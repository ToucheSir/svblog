# svblog - app.py
# Author: James Gray
# June 2013
#
# This file contains the main Flask
# application logic for the project.

import os, re
from datetime import datetime, timedelta
from flask import Flask, request, session, redirect, \
    url_for, render_template, flash, send_from_directory
from werkzeug import secure_filename
from tools import urlify, get_user, valid_file, valid_user, display
from user import User, udb
from upload import Upload, fdb
from entry import Entry, edb

app = Flask(__name__)
app.config.from_pyfile('settings.cfg')

def init_db():
    """
    Create the initial user, file and entry database tables.
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
    if 'logged_in' not in session:
        session['theme'] = app.config['DEFAULT_THEME']

    if request.method == 'POST':
        username = request.form['username']

        # Check to see if the user exists.
        user_instance = get_user(username)
        if user_instance is None:
            error = 'Invalid username.'
        elif not user_instance.check_pw(request.form['password']):
            error = 'Invalid password.'
        else:
            session['logged_in'], session['posting_enabled'], session['theme'] = \
                username, user_instance.posting_enabled, user_instance.theme
            flash('Successfully logged in.')
            return redirect(url_for('entries', name=username))
    else:
        return render_template('login.html', theme=session['theme'])

    display(error)
    return render_template('login.html', theme=session['theme'])

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/logout/')
def logout():
    """
    Logs a user out before returning to the login screen.`
    """
    session.pop('logged_in', None)
    session.pop('posting_enabled', None)
    session['theme'] = app.config['DEFAULT_THEME']
    flash('Successfully logged out.')
    return redirect(url_for('login'))

@app.route('/create/', methods=['GET', 'POST'])
def create():
    """
    Allows a user to create a new account.
    """
    error = None
    if 'logged_in' not in session:
        session['theme'] = app.config['DEFAULT_THEME']

    if request.method == 'POST':
        # Get submitted values from fields.
        username, password  = request.form['username'], request.form['password-a']

        # Check if there is a user by the same username in the database.
        user_instance = get_user(username)
        if user_instance is not None:
            error = 'Username is already taken.'
        elif re.search(r'[^_a-zA-Z0-9]', username):
            error = 'Username must only contain letters, numbers, and underscores.'
        elif password == '':
            error = 'Please enter a password.'
        elif password != request.form['password-b']:
            error = 'Passwords do not match.'
        else:
            # Add user to the database and log user in.
            user_instance = User(username, password)
            user_instance.theme = app.config['DEFAULT_THEME']
            udb.session.add(user_instance)
            udb.session.commit()

            flash('Account created!')
            session['logged_in'], session['posting_enabled'], session['theme'] = \
                username, user_instance.posting_enabled, user_instance.theme
            return redirect(url_for('entries', name=username))

    display(error)
    return render_template('create.html', theme=session['theme'])

@app.route('/<name>/', methods=['GET', 'POST'])
def entries(name):
    """
    This page presents a user's blog posts and file uploads,
    allowing visitors to download the files individually.
    """

    if get_user(name) is not None:
        session['theme'] = get_user(name).theme
        entries = [e for e in Entry.query.all()]
        entries.reverse()
        uploads = [dict(userid=f.userid, filename=f.filename, filetype=f.filetype) \
            for f in Upload.query.all()]

        if request.method == "POST":
            title, text = request.form['title'], request.form['text']
            text = urlify(text)

            entry_instance = Entry(name, title, text)
            edb.session.add(entry_instance)
            edb.session.commit()

            flash('Post successful!')
            return redirect(url_for('entries', name=name))
        else:
            return render_template('entries.html', username=name, \
                uploads=uploads, entries=entries, theme=session['theme'])
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
                old_filename = filename = secure_filename(file.filename)
                filetype = filename.rsplit('.', 1)[1].lower()

                # Prevents duplicate filenames by appending (1), (2), etc.
                # e.g. if two "images.jpg" are uploaded, the second one would
                # become "images(1).jpg".
                x = 0
                while os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
                    x += 1
                    filename = ("%s(%s).%s" % (old_filename.rsplit('.', 1)[0], x, filetype))

                # Save the file to the uploads folder.
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                file_instance = Upload(name, filename, filetype)

                # Insert the upload object into the database.
                fdb.session.add(file_instance)
                fdb.session.commit()

                flash('File was uploaded successfully.')
                return redirect(url_for('entries', name=name))
            else:
                flash("Invalid filename or file type.")
        return render_template('upload.html', username=name, theme=session['theme'])

    # If an error occurs, display the error and
    # redirect to the appropriate page.
    display(error)
    if 'logged_in' in session:
        return redirect(url_for('upload', name=session['logged_in']))
    else:
        return redirect(url_for('login'))

@app.route('/<name>/delete/post_<id>')
def delete_entry(name, id):
    """
    This page will delete an entry from the database.
    """

    # Check if the user is logged in before allowing to delete files.
    error = valid_user(name)
    if error is None:
        entry_instance = Entry.query.filter_by(id=id, userid=name).first()
        if entry_instance and entry_instance.userid == name:
            # Delete the entry from the database if it exists.
            edb.session.delete(entry_instance)
            edb.session.commit()

            flash('Entry was deleted successfully.')
            return redirect(url_for('entries', name=name))
        else:
            error = "Specified entry does not exist."

    # If an error occurs, display the error and
    # redirect to the appropriate page.
    display(error)
    if 'logged_in' in session:
        return redirect(url_for('entries', name=session['logged_in']))
    else:
        return redirect(url_for('login'))


@app.route('/<name>/delete/<filename>', methods=['GET', 'POST'])
def delete_file(name, filename):
    """
    This page will delete a file from the database and uploads folder.
    """

    # Check if the user is logged in before allowing to delete files.
    error = valid_user(name)
    if error is None:
        file = Upload.query.filter_by(filename=filename).first()
        if file and file.userid == name:
            # Delete the file from the upload folder if it exists.
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.isfile(filepath):
                os.remove(filepath)

            # Delete the upload object from the database.
            fdb.session.delete(file)
            fdb.session.commit()

            flash('File was deleted successfully.')
            return redirect(url_for('entries', name=name))
        else:
            error = "Specified file does not exist."

    # If an error occurs, display the error and
    # redirect to the appropriate page.
    display(error)
    if 'logged_in' in session:
        return redirect(url_for('entries', name=session['logged_in']))
    else:
        return redirect(url_for('login'))

@app.route('/<name>/<filename>')
def uploaded_file(name, filename):
    """
    This page will fetch a given file from the uploads folder.
    """
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/<name>/theme/', methods=['GET', 'POST'])
def change_theme(name):
    """
    This page will allow the user to change the appearance of their blog.
    """

    # Check if the user is logged in before allowing to change theme.
    error = valid_user(name)
    if error is None:
        if request.method == 'POST':
            new_theme = request.form['theme']
            user_instance = get_user(name)

            # Change the user's theme, change the theme in browser and
            # store the changed theme in the user database.
            user_instance.theme = session['theme'] = new_theme
            udb.session.commit()

            flash('Theme changed to %s.' % new_theme.lower())
            return redirect(url_for('change_theme', name=name))

        return render_template('theme.html', username=name, theme=session['theme'])

    # If an error occurs, display the error and
    # redirect to the appropriate page.
    display(error)
    if 'logged_in' in session:
        return redirect(url_for('upload', name=session['logged_in']))
    else:
        return redirect(url_for('login'))

@app.route('/<name>/all/')
def view_users(name):
    """
    This page will allow the administrator to view the blogs of all registered users.
    """

    # Check if the logged in user is the administrator.
    if 'logged_in' in session and session['logged_in'] == "admin":
        users = [u for u in User.query.all()]
        return render_template('all.html', username=name, users=users, theme=session['theme'])
    else:
        error = "Must be logged in as the administrator to access this page."
        display(error)
        return redirect(url_for('login'))

if __name__ == "__main__":
    init_db()
    app.run()
