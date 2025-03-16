from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from app import mongo
import uuid
from datetime import datetime
import os

user_bp = Blueprint('user', __name__)

@user_bp.route('/join_queue/<queue_id>', methods=['GET', 'POST'])
def join_queue(queue_id):
    try:
        queue = mongo.db.queues.find_one({"queue_id": queue_id})

        if not queue:
            flash("Queue not found.", "danger")
            return render_template('join_queue.html', queue_closed=True)

        if queue.get('status') == 'closed':
            return render_template('join_queue.html', queue_closed=True)

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()

            if not name or not email:
                flash("Name and Email are required.", "warning")
                return render_template('join_queue.html', queue_id=queue_id, queue_closed=False)

            user_id = str(uuid.uuid4())[:8]

            mongo.db.queues.update_one(
                {"queue_id": queue_id},
                {"$push": {
                    "users": {
                        "user_id": user_id,
                        "name": name,
                        "email": email,
                        "joined_at": datetime.now()
                    }
                }}
            )

            updated_queue = mongo.db.queues.find_one({"queue_id": queue_id})
            position = len(updated_queue.get("users", [])) - 1

            return render_template("waiting_page.html", name=name, position=position)

    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        return render_template('join_queue.html', queue_id=queue_id, queue_closed=False)

    return render_template('join_queue.html', queue_id=queue_id, queue_closed=False)
