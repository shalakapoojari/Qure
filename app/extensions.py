# extensions.py
from flask_socketio import SocketIO
from flask_pymongo import PyMongo

mongo = PyMongo()
socketio = SocketIO(cors_allowed_origins="*")


