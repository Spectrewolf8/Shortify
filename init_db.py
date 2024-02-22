# import sqlite3

# connection = sqlite3.connect('database.db')

# with open('schema.sql') as f:
#     connection.executescript(f.read())

# connection.commit()
# connection.close()
import bson

from flask import current_app, g
from werkzeug.local import LocalProxy
from flask_pymongo import PyMongo

from pymongo.errors import DuplicateKeyError, OperationFailure
from bson.objectid import ObjectId
from bson.errors import InvalidId


def get_db():
    """
    Configuration method to return db instance
    """
    db = getattr(g, "_urls", None)

    if db is None:

        db = g._database = PyMongo(current_app).db
    print(current_app)
    return db


# Use LocalProxy to read the global db instance with just `db`
db = LocalProxy(get_db)
