# svblog - entry.py
# Author: James Gray
# June 2013
#
# This file contains the Entry class, which
# flask-demo uses to create instances of entry 
# objects to be added to the entry database.

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite://///home/edesign/svblog/data/entries.db'

# Create SQLAlchemy object for file database
edb = SQLAlchemy(app)

class Entry(edb.Model):
    """
    Creates an entry object.
    """

    # Initialize columns
    id = edb.Column(edb.Integer, primary_key=True)
    userid = edb.Column(edb.String(80))
    title = edb.Column(edb.String(32))
    text = edb.Column(edb.String(32))

    def __init__(self, userid, title, text):
        self.userid = userid
        self.title = title
        self.text = text

    def __repr__(self):
        return '<Entry %r>' % self.title
