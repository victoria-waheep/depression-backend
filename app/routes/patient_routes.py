import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from marshmallow import ValidationError

from app.extensions import db
from app.models.patient import Patient
from app.schemas.patient_schema import PatientSchema

logger = logging.getLogger(__name__)
patient_bp = Blueprint("patients", __name__, url_prefix="/api/patients")

patient_schema = PatientSchema()


def _require_doctor():
    claims = get_jwt()
    if claims.get("role") != "Doctor":
        return jsonify({"success": False, "message": "Doctor access required."}), 403
    return None


@patient_bp.post("")
@jwt_required()
def create_patient():
    err = _require_doctor()
    if err:
        return err

    try:
        data = patient_schema.load(request.get_json(force=True) or {})
    except ValidationError as ve:
        return jsonify({"success": False, "errors": ve.messages}), 400

    doctor_id = int(get_jwt_identity())
    patient = Patient(doctor_id=doctor_id, **data)
    db.session.add(patient)
    db.session.commit()
    return jsonify({"success": True, "patient": patient.to_dict()}), 201


@patient_bp.get("")
@jwt_required()
def list_patients():
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())

    if claims.get("role") == "Doctor":
        # Doctor sees only their own patients
        patients = Patient.query.filter_by(doctor_id=current_user_id).all()
    else:
        # Patient sees only their own record
        patients = Patient.query.filter_by(id=current_user_id).all()

    return jsonify({"success": True, "patients": [p.to_dict() for p in patients]}), 200


@patient_bp.get("/<int:patient_id>")
@jwt_required()
def get_patient(patient_id):
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())

    patient = Patient.query.get_or_404(patient_id)

    if claims.get("role") == "Doctor":
        if patient.doctor_id != current_user_id:
            return jsonify({"success": False, "message": "Forbidden."}), 403
    else:
        if patient.id != current_user_id:
            return jsonify({"success": False, "message": "Forbidden."}), 403

    return jsonify({"success": True, "patient": patient.to_dict()}), 200


@patient_bp.put("/<int:patient_id>")
@jwt_required()
def update_patient(patient_id):
    err = _require_doctor()
    if err:
        return err

    doctor_id = int(get_jwt_identity())
    patient = Patient.query.get_or_404(patient_id)

    if patient.doctor_id != doctor_id:
        return jsonify({"success": False, "message": "Forbidden."}), 403

    try:
        data = patient_schema.load(request.get_json(force=True) or {}, partial=True)
    except ValidationError as ve:
        return jsonify({"success": False, "errors": ve.messages}), 400

    for key, value in data.items():
        if value is not None:
            setattr(patient, key, value)

    db.session.commit()
    return jsonify({"success": True, "patient": patient.to_dict()}), 200


@patient_bp.delete("/<int:patient_id>")
@jwt_required()
def delete_patient(patient_id):
    err = _require_doctor()
    if err:
        return err

    doctor_id = int(get_jwt_identity())
    patient = Patient.query.get_or_404(patient_id)

    if patient.doctor_id != doctor_id:
        return jsonify({"success": False, "message": "Forbidden."}), 403

    db.session.delete(patient)
    db.session.commit()
    return jsonify({"success": True, "message": "Patient deleted."}), 200
