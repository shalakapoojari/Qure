import base64
import io
import uuid
from datetime import datetime
import os
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
import qrcode
from pymongo.collection import ReturnDocument
from app import mongo, socketio
from app.utils import send_token_accepted_email
from flask import current_app  # Assumed utility function

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
def admin_dashboard():
    """Render Admin Dashboard with the latest queue ID."""
    last_queue = mongo.db.queues.find_one(sort=[('_id', -1)])
    queue_id = last_queue["queue_id"] if last_queue else ""
    user_id_from_server = "admin_user"  # Should ideally come from session
    return render_template("admin_dashboard.html", queue_id=queue_id, user_id_from_server=user_id_from_server)


@admin_bp.route('/create_queue', methods=['POST'])
def create_queue():
    """Create a new queue and return its QR code (base64)."""
    queue_id = str(uuid.uuid4())[:8]

    mongo.db.queues.insert_one({
        'queue_id': queue_id,
        'users': [],
        'status': 'open',
        'created_at': datetime.utcnow()
    })

    # Use BASE_URL from environment variables
    base_url = os.getenv('BASE_URL', 'https://qure.onrender.com/')
    join_url = f"{base_url}/user/join_queue/{queue_id}"

    # Generate QR Code
    qr_img = qrcode.make(join_url)
    buffer = io.BytesIO()
    qr_img.save(buffer)
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')

    return jsonify({
        'queue_id': queue_id,
        'qr_code': img_base64
    })


@admin_bp.route('/accept_user/<queue_id>', methods=['POST'])
def accept_user(queue_id: str):
    """Accept the first user in the queue and send them a confirmation email."""
    queue = mongo.db.queues.find_one({"queue_id": queue_id})

    if not queue or not queue.get("users"):
        flash("Queue not found or empty.", "warning")
        return '', 204

    current_user = queue["users"][0]

    mongo.db.queues.update_one(
        {"queue_id": queue_id},
        {"$pull": {"users": {"user_id": current_user["user_id"]}}}
    )

    user_name = current_user.get("name", "User")
    user_email = current_user.get("email")

    if user_email:
        send_token_accepted_email(user_email, user_name)

    flash(f"{user_name}'s token has been accepted!", "success")
    return '', 204


@admin_bp.route('/queue_status/<queue_id>', methods=['GET'])
def queue_status(queue_id: str):
    """Return JSON with queue status and user positions."""
    queue = mongo.db.queues.find_one({"queue_id": queue_id})

    if not queue:
        return jsonify({"status": "error", "message": "Queue not found"}), 404

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


@admin_bp.route('/close_queue/<queue_id>', methods=['POST'])
def close_queue(queue_id: str):
    """Close the specified queue."""
    result = mongo.db.queues.update_one(
        {"queue_id": queue_id},
        {"$set": {"status": "closed"}}
    )

    if result.modified_count:
        flash("Queue closed successfully.", "success")
    else:
        flash("Queue was already closed or not found.", "warning")

    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/reopen_queue/<queue_id>', methods=['POST'])
def reopen_queue(queue_id: str):
    """Reopen a previously closed queue."""
    result = mongo.db.queues.update_one(
        {"queue_id": queue_id},
        {"$set": {"status": "open"}}
    )

    if result.modified_count:
        flash("Queue reopened successfully.", "success")
    else:
        flash("Queue was already open or not found.", "warning")

    return redirect(url_for('admin.admin_dashboard'))
