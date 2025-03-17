from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app
from app.extensions import mongo, socketio
import uuid
from datetime import datetime
import os

user_bp = Blueprint('user', __name__)

@user_bp.route('/join_queue/<queue_id>', methods=['GET', 'POST'])
def join_queue(queue_id):
    try:
        # Find the queue in the database
        queue = mongo.db.queues.find_one({"queue_id": queue_id})

        # Check if queue exists
        if not queue:
            flash("Queue not found.", "danger")
            return render_template('join_queue.html', queue_closed=True)

        # Check if queue is closed
        if queue.get('status') == 'closed':
            return render_template('join_queue.html', queue_closed=True)

        # Handle form submission
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()

            # Validate form data
            if not name or not email:
                flash("Name and Email are required.", "warning")
                return render_template('join_queue.html', queue_id=queue_id, queue_closed=False)

            # Generate unique user ID
            user_id = str(uuid.uuid4())[:8]

            # Add user to queue
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

            # Get updated queue to determine position
            updated_queue = mongo.db.queues.find_one({"queue_id": queue_id})
            position = len(updated_queue.get("users", [])) - 1

            # Emit queue update event
            socketio.emit('queue_update', {
                'queue_id': queue_id,
                'total_users': position + 1,
                'users': [
                    {
                        'position': idx + 1,
                        'name': user.get('name', 'Unknown'),
                        'email': user.get('email', 'Not Provided')
                    }
                    for idx, user in enumerate(updated_queue.get('users', []))
                ]
            })

            # Render waiting page
            return render_template("waiting_page.html", 
                                  name=name, 
                                  position=position, 
                                  user_id=user_id,
                                  people_ahead=position)

    except Exception as e:
        current_app.logger.error(f"Error in join_queue: {str(e)}")
        flash(f"An error occurred: {str(e)}", "danger")
        return render_template('join_queue.html', queue_id=queue_id, queue_closed=False)

    # Render join form
    return render_template('join_queue.html', queue_id=queue_id, queue_closed=False)

@user_bp.route('/check_position/<queue_id>/<user_id>', methods=['GET'])
def check_position(queue_id, user_id):
    try:
        # Find the queue
        queue = mongo.db.queues.find_one({"queue_id": queue_id})
        
        if not queue:
            return jsonify({"status": "error", "message": "Queue not found"}), 404
        
        # Find user's position
        users = queue.get("users", [])
        position = -1
        
        for idx, user in enumerate(users):
            if user.get("user_id") == user_id:
                position = idx
                break
        
        if position == -1:
            return jsonify({"status": "error", "message": "User not found in queue"}), 404
        
        return jsonify({
            "status": "success",
            "position": position,
            "total_users": len(users),
            "is_next": position == 0
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in check_position: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

