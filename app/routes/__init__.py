from flask import Blueprint, redirect, url_for,render_template
from app import mongo

main = Blueprint('main', __name__)


@main.route('/dashboard')
def dashboard():
    return render_template("admin_dashboard.html")