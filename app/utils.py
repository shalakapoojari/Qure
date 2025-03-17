import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
import logging
from flask import Flask
from flask_pymongo import PyMongo
from flask_socketio import SocketIO
import os
import logging
from logging.handlers import RotatingFileHandler

# Initialize extensions
mongo = PyMongo()
socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object('app.config.Config')
    
    # Configure logging
    configure_logging(app)
    
    # Initialize extensions
    mongo.init_app(app)
    socketio.init_app(app)
    
    # Ensure static directories exist
    os.makedirs(os.path.join(app.static_folder, 'qrcodes'), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'images'), exist_ok=True)
    
    # Register blueprints
    from app.routes.user_routes import user_bp
    from app.routes.admin_routes import admin_bp
    
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

def configure_logging(app):
    """Configure application logging."""
    if not app.debug:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.mkdir('logs')
            
        # Set up file handler
        file_handler = RotatingFileHandler('logs/qure.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        
        # Add handlers
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Qure Queue Management System startup')

def register_error_handlers(app):
    """Register error handlers for the application."""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500
    
    # Import render_template here to avoid circular imports
    from flask import render_template



def send_token_accepted_email(to_email, user_name):
    """Send email notification when a user's token is accepted."""
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Your Turn Has Arrived - Qure Queue System"
        msg['From'] = current_app.config['MAIL_DEFAULT_SENDER']
        msg['To'] = to_email
        
        # Create HTML version of the message
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4361ee; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f8f9fa; padding: 20px; border-radius: 0 0 5px 5px; }}
                .button {{ display: inline-block; background-color: #4361ee; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Your Turn Has Arrived!</h1>
                </div>
                <div class="content">
                    <p>Hello {user_name},</p>
                    <p>Great news! It's now your turn in the queue.</p>
                    <p>Please proceed to the counter as soon as possible.</p>
                    <p>Thank you for your patience!</p>
                    <p>Best regards,<br>Qure Queue Management System</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create plain text version of the message
        text = f"""
        Hello {user_name},
        
        Great news! It's now your turn in the queue.
        
        Please proceed to the counter as soon as possible.
        
        Thank you for your patience!
        
        Best regards,
        Qure Queue Management System
        """
        
        # Attach parts
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        with smtplib.SMTP_SSL(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT']) as server:
            server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
            server.sendmail(current_app.config['MAIL_DEFAULT_SENDER'], to_email, msg.as_string())
            
        current_app.logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to send email: {str(e)}")
        raise

