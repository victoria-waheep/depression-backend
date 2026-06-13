from datetime import datetime, timezone
from app.extensions import db


class Prediction(db.Model):
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    prediction_label = db.Column(db.String(50), nullable=False)   # Responder / Non-Responder
    response_probability = db.Column(db.Float, nullable=False)
    severity_status = db.Column(db.String(50), nullable=True)      # Mild / Moderate / Severe
    status = db.Column(db.String(50), default="Active")            # Active / Pending / Completed
    prediction_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "prediction_label": self.prediction_label,
            "response_probability": round(self.response_probability, 4),
            "severity_status": self.severity_status,
            "status": self.status,
            "prediction_date": self.prediction_date.isoformat(),
        }
