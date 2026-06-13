from app.extensions import db
from app.models.user import User


def register_user(full_name: str, email: str, password: str, role: str) -> User:
    """Create a new user. Raises ValueError if email already exists."""
    if User.query.filter_by(email=email).first():
        raise ValueError("Email already registered.")
    user = User(full_name=full_name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def authenticate_user(email: str, password: str) -> User:
    """Validate credentials. Raises ValueError on failure."""
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        raise ValueError("Invalid email or password.")
    return user
