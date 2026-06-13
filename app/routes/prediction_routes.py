import logging
import io
from datetime import datetime, timezone

import pandas as pd
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from app.extensions import db
from app.models.patient import Patient
from app.models.prediction import Prediction
from app.services import ml_service

logger = logging.getLogger(__name__)
prediction_bp = Blueprint("predictions", __name__, url_prefix="/api")

# Features pulled from the Patient record — must match pipeline's feature_names exactly.
PATIENT_FEATURE_KEYS = [
    "age",
    "neoFFI_q31", "neoFFI_q33", "neoFFI_q37",
    "neoFFI_q43", "neoFFI_q46", "neoFFI_q51",
    "n_oddb_CN", "BDI_pre", "rTMS_PROTOCOL",
]

# Max CSV upload size (rows) to prevent abuse
BATCH_ROW_LIMIT = 500


@prediction_bp.post("/predict")
@jwt_required()
def predict():
    claims = get_jwt()
    if claims.get("role") != "Doctor":
        return jsonify({"success": False, "message": "Doctor access required."}), 403

    body = request.get_json(force=True) or {}
    patient_id = body.get("patient_id")
    if not patient_id:
        return jsonify({"success": False, "message": "patient_id is required."}), 400

    doctor_id = int(get_jwt_identity())
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"success": False, "message": f"Patient {patient_id} not found."}), 404

    if patient.doctor_id != doctor_id:
        return jsonify({"success": False, "message": "Forbidden."}), 403

    # Build feature dict from stored patient record — not from request body
    feature_dict = {key: getattr(patient, key, None) for key in PATIENT_FEATURE_KEYS}

    missing = [k for k, v in feature_dict.items() if v is None]
    if missing:
        return jsonify({
            "success": False,
            "message": f"Patient record is missing required features: {missing}",
        }), 422

    try:
        result = ml_service.predict_single(feature_dict)
    except Exception as exc:
        logger.error(f"[predict] ML inference failed: {exc}")
        return jsonify({"success": False, "message": "Prediction failed. Check server logs."}), 500

    pred = Prediction(
        patient_id=patient_id,
        prediction_label=result["prediction_label"],
        response_probability=result["probability"],
        severity_status=result["severity_status"],
        status="Active",
    )
    db.session.add(pred)
    db.session.commit()

    return jsonify({
        "success": True,
        "prediction": result["prediction_label"],
        "probability": result["probability"],
        "severity_status": result["severity_status"],
        "threshold_used": result["threshold_used"],
        "prediction_id": pred.id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }), 201


@prediction_bp.post("/predict/batch")
@jwt_required()
def predict_batch():
    claims = get_jwt()
    if claims.get("role") != "Doctor":
        return jsonify({"success": False, "message": "Doctor access required."}), 403

    if "file" not in request.files:
        return jsonify({"success": False, "message": "No CSV file provided (key='file')."}), 400

    csv_file = request.files["file"]
    try:
        df = pd.read_csv(io.BytesIO(csv_file.read()))
    except Exception:
        return jsonify({"success": False, "message": "Failed to read CSV file."}), 400

    if df.empty:
        return jsonify({"success": False, "message": "CSV file is empty."}), 400

    if len(df) > BATCH_ROW_LIMIT:
        return jsonify({
            "success": False,
            "message": f"CSV exceeds maximum row limit of {BATCH_ROW_LIMIT}.",
        }), 400

    try:
        results = ml_service.predict_batch(df)
    except Exception as exc:
        logger.error(f"[predict_batch] Batch inference failed: {exc}")
        return jsonify({"success": False, "message": "Batch prediction failed."}), 500

    doctor_id = int(get_jwt_identity())
    saved = 0
    for row in results:
        patient_id = None
        if "patient_id" in df.columns:
            try:
                patient_id = int(df.iloc[row["row_index"]]["patient_id"])
            except Exception:
                pass

        if patient_id:
            patient = Patient.query.get(patient_id)
            if patient and patient.doctor_id == doctor_id:
                pred = Prediction(
                    patient_id=patient_id,
                    prediction_label=row["prediction_label"],
                    response_probability=row["probability"],
                    severity_status=row["severity_status"],
                    status="Active",
                )
                db.session.add(pred)
                saved += 1

    db.session.commit()

    return jsonify({
        "success": True,
        "processed_rows": len(results),
        "successful_predictions": len(results),
        "saved_to_db": saved,
        "results": results,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }), 200


@prediction_bp.get("/predictions/patient/<int:patient_id>")
@jwt_required()
def get_patient_predictions(patient_id):
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())

    patient = Patient.query.get_or_404(patient_id)

    if claims.get("role") == "Doctor" and patient.doctor_id != current_user_id:
        return jsonify({"success": False, "message": "Forbidden."}), 403

    if claims.get("role") != "Doctor" and patient.id != current_user_id:
        return jsonify({"success": False, "message": "Forbidden."}), 403

    predictions = (
        Prediction.query
        .filter_by(patient_id=patient_id)
        .order_by(Prediction.prediction_date.desc())
        .all()
    )
    return jsonify({"success": True, "predictions": [p.to_dict() for p in predictions]}), 200
