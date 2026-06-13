import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.chat_message import ChatMessage
from app.services.chat_service import send_message, get_conversation, mark_as_read

logger = logging.getLogger(__name__)
chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")


@chat_bp.post("/send")
@jwt_required()
def send():
    sender_id = int(get_jwt_identity())
    body = request.get_json(force=True) or {}
    receiver_id = body.get("receiver_id")
    text = body.get("message_text", "").strip()

    if not receiver_id:
        return jsonify({"success": False, "message": "receiver_id is required."}), 400
    if not text:
        return jsonify({"success": False, "message": "message_text is required."}), 400
    if receiver_id == sender_id:
        return jsonify({"success": False, "message": "Cannot send a message to yourself."}), 400

    msg = send_message(sender_id, receiver_id, text)
    return jsonify({"success": True, "message": msg.to_dict()}), 201


@chat_bp.get("/conversation/<int:user1_id>/<int:user2_id>")
@jwt_required()
def conversation(user1_id, user2_id):
    current_user_id = int(get_jwt_identity())

    if current_user_id not in (user1_id, user2_id):
        return jsonify({"success": False, "message": "Forbidden."}), 403

    messages = get_conversation(user1_id, user2_id)
    return jsonify({"success": True, "messages": [m.to_dict() for m in messages]}), 200


@chat_bp.patch("/read/<int:message_id>")
@jwt_required()
def read_message(message_id):
    current_user_id = int(get_jwt_identity())

    msg = ChatMessage.query.get_or_404(message_id)

    if msg.receiver_id != current_user_id:
        return jsonify({"success": False, "message": "Forbidden."}), 403

    # Idempotent — safe to call even if already read
    if not msg.is_read:
        msg = mark_as_read(message_id)

    return jsonify({"success": True, "message": msg.to_dict()}), 200
