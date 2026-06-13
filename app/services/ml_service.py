"""
ML Service — loads RF_Balanced_calib model once at startup (singleton pattern).
The model .pkl is a dict with keys:
  model, threshold, feature_names, selected_features
"""

import logging
import pandas as pd
import joblib

logger = logging.getLogger(__name__)

_artifact = None  # singleton


def load_model(model_path: str):
    """Load model artifact from disk. Called once at app startup."""
    global _artifact
    try:
        _artifact = joblib.load(model_path)
        required = {"model", "threshold", "feature_names"}
        missing = required - set(_artifact.keys())
        if missing:
            raise ValueError(f"Model artifact missing keys: {missing}")
        logger.info(
            f"[ML] Model loaded successfully. "
            f"Feature count: {len(_artifact['feature_names'])}. "
            f"Threshold: {_artifact['threshold']:.4f}"
        )
    except Exception as exc:
        logger.error(f"[ML] Failed to load model from '{model_path}': {exc}")
        _artifact = None
        raise


def get_artifact():
    """Return the loaded artifact dict or raise if not loaded."""
    if _artifact is None:
        raise RuntimeError("ML model is not loaded. Check startup logs.")
    return _artifact


def _get_severity(probability: float) -> str:
    """Map response probability to clinical severity label."""
    if probability >= 0.75:
        return "Mild"
    elif probability >= 0.45:
        return "Moderate"
    else:
        return "Severe"


def predict_single(feature_dict: dict) -> dict:
    """
    Run prediction for a single patient.

    Parameters
    ----------
    feature_dict : dict
        Keys are the raw feature names the model expects.

    Returns
    -------
    dict with keys: prediction_label, probability, severity_status, threshold_used
    """
    artifact = get_artifact()
    model = artifact["model"]
    threshold = artifact["threshold"]
    feature_names = artifact["feature_names"]

    df = pd.DataFrame([feature_dict], columns=feature_names)

    proba = float(model.predict_proba(df)[:, 1][0])
    label = "Responder" if proba >= threshold else "Non-Responder"
    severity = _get_severity(proba)

    return {
        "prediction_label": label,
        "probability": round(proba, 4),
        "severity_status": severity,
        "threshold_used": round(threshold, 4),
    }


def predict_batch(df: pd.DataFrame) -> list:
    """
    Run predictions on a DataFrame (from a CSV upload).

    Returns a list of dicts, one per row.
    """
    artifact = get_artifact()
    model = artifact["model"]
    threshold = artifact["threshold"]
    feature_names = artifact["feature_names"]

    aligned = df.reindex(columns=feature_names)
    probas = model.predict_proba(aligned)[:, 1]

    results = []
    for i, proba in enumerate(probas):
        proba = float(proba)
        label = "Responder" if proba >= threshold else "Non-Responder"
        results.append({
            "row_index": i,
            "prediction_label": label,
            "probability": round(proba, 4),
            "severity_status": _get_severity(proba),
            "threshold_used": round(threshold, 4),
        })
    return results
