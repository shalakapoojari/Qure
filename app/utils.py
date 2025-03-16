import smtplib
from email.mime.text import MIMEText
from flask import current_app

def send_token_accepted_email(to_email, user_name):
    subject = "Your Token Has Been Accepted!"
    body = f"Hi {user_name},\n\nYour token has been accepted. Please proceed to the counter.\n\nThank you!"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = current_app.config['MAIL_DEFAULT_SENDER']
    msg['To'] = to_email

    try:
        with smtplib.SMTP_SSL(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT']) as server:
            server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
            server.sendmail(current_app.config['MAIL_DEFAULT_SENDER'], to_email, msg.as_string())
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email: {e}")
