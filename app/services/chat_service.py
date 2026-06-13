from app.extensions import db
from app.models.chat_message import ChatMessage


def send_message(sender_id: int, receiver_id: int, text: str) -> ChatMessage:
    msg = ChatMessage(sender_id=sender_id, receiver_id=receiver_id, message_text=text)
    db.session.add(msg)
    db.session.commit()
    return msg


def get_conversation(user1_id: int, user2_id: int) -> list:
    messages = (
        ChatMessage.query
        .filter(
            ((ChatMessage.sender_id == user1_id) & (ChatMessage.receiver_id == user2_id))
            | ((ChatMessage.sender_id == user2_id) & (ChatMessage.receiver_id == user1_id))
        )
        .order_by(ChatMessage.timestamp.asc())
        .all()
    )
    return messages


def mark_as_read(message_id: int) -> ChatMessage:
    msg = ChatMessage.query.get_or_404(message_id)
    msg.is_read = True
    db.session.commit()
    return msg
