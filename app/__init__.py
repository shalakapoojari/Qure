from flask import Flask
from flask_pymongo import PyMongo  
from flask_socketio import SocketIO
from app.config import Config
from flask_cors import CORS
from app.extensions import mongo

mongo = PyMongo()
socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    CORS(app)
    mongo.init_app(app)
    socketio.init_app(app)

    # Register routes
    from app.routes.user_routes import user_bp
    from app.routes.admin_routes import admin_bp
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    return app
