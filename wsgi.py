# wsgi.py
from app import create_app, socketio

app = create_app()

# Only import `socketio` app here, don't run it
# gunicorn will use this file
