import base64
import io
import uuid
from datetime import datetime
import os
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
import qrcode
from app.extensions import socketio
from app import mongo
from app.utils import send_token_accepted_email

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
def admin_dashboard():
    """Render Admin Dashboard with all queues."""
    # Get the most recent queue
    queue = mongo.db.queues.find_one(sort=[('created_at', -1)])
    queue_id = queue.get('queue_id') if queue else None
    
    user_id_from_server = "admin_user"  # Should ideally come from session
    return render_template("admin_dashboard.html", queue_id=queue_id, user_id_from_server=user_id_from_server)

@admin_bp.route('/create_queue', methods=['POST'])
def create_queue():
    """Create a new queue and generate QR code."""
    try:
        # Generate unique queue ID
        queue_id = str(uuid.uuid4())[:8]

        # Create queue in database
        mongo.db.queues.insert_one({
            'queue_id': queue_id,
            'users': [],
            'status': 'open',
            'created_at': datetime.utcnow()
        })

        # Generate join URL
        base_url = current_app.config.get('BASE_URL', request.host_url.rstrip('/'))
        join_url = f"{base_url}/user/join_queue/{queue_id}"

        # Generate QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(join_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code to static folder
        qr_dir = os.path.join(current_app.static_folder, 'qrcodes')
        os.makedirs(qr_dir, exist_ok=True)
        
        qr_path = os.path.join(qr_dir, f"{queue_id}.png")
        img.save(qr_path)
        
        # Generate URL for QR code
        qr_code_url = url_for('static', filename=f'qrcodes/{queue_id}.png', _external=True)
        
        return jsonify({
            'status': 'success',
            'queue_id': queue_id,
            'qr_code_url': qr_code_url
        })
        
    except Exception as e:
        current_app.logger.error(f"Error creating queue: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to create queue: {str(e)}"
        }), 500

@admin_bp.route('/accept_user/<queue_id>', methods=['POST'])
def accept_user(queue_id):
    """Accept the first user in the queue and send them a confirmation email."""
    try:
        # Find the queue
        queue = mongo.db.queues.find_one({"queue_id": queue_id})

        if not queue or not queue.get("users"):
            flash("Queue not found or empty.", "warning")
            socketio.emit('queue_empty')
            return redirect(url_for('admin.admin_dashboard'))

        # Get the first user in the queue
        current_user = queue["users"][0]
        user_id = current_user["user_id"]

        # Remove user from queue
        mongo.db.queues.update_one(
            {"queue_id": queue_id},
            {"$pull": {"users": {"user_id": user_id}}}
        )

        # Get user details
        user_name = current_user.get("name", "User")
        user_email = current_user.get("email")

        # Send email notification
        if user_email:
            try:
                send_token_accepted_email(user_email, user_name)
            except Exception as e:
                current_app.logger.error(f"Failed to send email: {str(e)}")
                flash(f"User accepted but email notification failed: {str(e)}", "warning")

        # Emit socket event to notify user
        socketio.emit('token_accepted', {
            'user_id': user_id,
            'message': f"Your turn has arrived! Please proceed to the counter."
        })

        # Get updated queue
        updated_queue = mongo.db.queues.find_one({"queue_id": queue_id})
        users = updated_queue.get("users", [])
        
        # Notify next user if there is one
        if users:
            next_user = users[0]
            socketio.emit('you_are_next', {
                'user_id': next_user.get('user_id'),
                'message': "You're next in line! Please get ready."
            })
        else:
            # Queue is empty, notify admin
            socketio.emit('queue_empty')
        
        # Emit queue update event
        socketio.emit('queue_update', {
            'queue_id': queue_id,
            'total_users': len(users),
            'users': [
                {
                    'position': idx + 1,
                    'name': user.get('name', 'Unknown'),
                    'email': user.get('email', 'Not Provided')
                }
                for idx, user in enumerate(users)
            ]
        })

        flash(f"{user_name}'s token has been accepted!", "success")
        return redirect(url_for('admin.admin_dashboard'))
        
    except Exception as e:
        current_app.logger.error(f"Error accepting user: {str(e)}")
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/queue_status/<queue_id>', methods=['GET'])
def queue_status(queue_id):
    """Return JSON with queue status and user positions."""
    try:
        # Find the queue
        queue = mongo.db.queues.find_one({"queue_id": queue_id})

        if not queue:
            return jsonify({"status": "error", "message": "Queue not found"}), 404

        # Get users and their positions
        users = queue.get("users", [])
        user_list = [
            {
                "position": index + 1,
                "name": user.get("name", "Unknown"),
                "email": user.get("email", "Not Provided")
            }
            for index, user in enumerate(users)
        ]

        return jsonify({
            "status": "success",
            "queue_id": queue_id,
            "total_users": len(users),
            "users": user_list
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting queue status: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@admin_bp.route('/close_queue/<queue_id>', methods=['POST'])
def close_queue(queue_id):
    """Close the specified queue."""
    try:
        # Update queue status to closed
        result = mongo.db.queues.update_one(
            {"queue_id": queue_id},
            {"$set": {"status": "closed"}}
        )

        if result.modified_count:
            flash("Queue closed successfully.", "success")
        else:
            flash("Queue was already closed or not found.", "warning")

        return redirect(url_for('admin.admin_dashboard'))
        
    except Exception as e:
        current_app.logger.error(f"Error closing queue: {str(e)}")
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/reopen_queue/<queue_id>', methods=['POST'])
def reopen_queue(queue_id):
    """Reopen a previously closed queue."""
    try:
        # Update queue status to open
        result = mongo.db.queues.update_one(
            {"queue_id": queue_id},
            {"$set": {"status": "open"}}
        )

        if result.modified_count:
            flash("Queue reopened successfully.", "success")
        else:
            flash("Queue was already open or not found.", "warning")

        return redirect(url_for('admin.admin_dashboard'))
        
    except Exception as e:
        current_app.logger.error(f"Error reopening queue: {str(e)}")
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('admin.admin_dashboard'))

