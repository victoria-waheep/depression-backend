import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from marshmallow import ValidationError

from app.schemas.auth_schema import RegisterSchema, LoginSchema
from app.services.auth_service import register_user, authenticate_user

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

register_schema = RegisterSchema()
login_schema = LoginSchema()


@auth_bp.post("/register")
def register():
    try:
        data = register_schema.load(request.get_json(force=True) or {})
    except ValidationError as err:
        return jsonify({"success": False, "errors": err.messages}), 400

    try:
        user = register_user(
            full_name=data["full_name"],
            email=data["email"],
            password=data["password"],
            role=data.get("role", "Patient"),
        )
    except ValueError as err:
        return jsonify({"success": False, "message": str(err)}), 409

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify({"success": True, "token": token, "user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    try:
        data = login_schema.load(request.get_json(force=True) or {})
    except ValidationError as err:
        return jsonify({"success": False, "errors": err.messages}), 400

    try:
        user = authenticate_user(data["email"], data["password"])
    except ValueError as err:
        return jsonify({"success": False, "message": str(err)}), 401

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify({"success": True, "token": token, "user": user.to_dict()}), 200
