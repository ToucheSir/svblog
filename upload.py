# svblog - upload.py
# Author: James Gray
# June 2013
#
# This file contains the Upload class, which
# flask-demo uses to create instances of upload
# objects to be added to the upload database.

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
DATABASE_URI = 'sqlite://///home/brianc/projects/svblog/data/users.db'
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI

# Create SQLAlchemy object for file database
fdb = SQLAlchemy(app)


class Upload(fdb.Model):
    """
    Creates an upload object.
    """

    # Initialize columns
    id = fdb.Column(fdb.Integer, primary_key=True)
    userid = fdb.Column(fdb.String(80))
    filename = fdb.Column(fdb.String(160))
    filetype = fdb.Column(fdb.String(80))

    def __init__(self, username, filename, filetype):
        self.userid = username
        self.filename = filename
        self.filetype = filetype

    def __repr__(self):
        return '<File %r>' % self.filename
