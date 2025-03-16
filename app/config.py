class Config:
    MONGO_URI = "mongodb+srv://shalakapoojari677:shalakapoojari@qure.cgdz4.mongodb.net/db?retryWrites=true&w=majority"
    SECRET_KEY = "supersecurekey"
    BASE_URL = "http://localhost:5000"
    
    # ✅ Correct Email Settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465  # Use 465 for SSL (not 587 for TLS if you're using SMTP_SSL)
    MAIL_USERNAME = 'hashdropco@gmail.com'          # Your sender email
    MAIL_PASSWORD = 'hyhc chtl zzzo auvn'           # Gmail App Password
    MAIL_DEFAULT_SENDER = 'hashdropco@gmail.com'    # Sender Name
