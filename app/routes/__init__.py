from flask import Blueprint
from app.extensions import mongo

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return "Hello from Smart Queue!"

@main.route('/health')
def health_check():
    try:
        mongo.db.queues.find_one()
        return "MongoDB Connected", 200
    except Exception as e:
        return str(e), 500
