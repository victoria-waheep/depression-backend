from app.extensions import db


class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Demographics
    full_name = db.Column(db.String(150), nullable=True)
    patient_code = db.Column(db.String(50), nullable=True, unique=True, index=True)
    age = db.Column(db.Float, nullable=True)
    gender = db.Column(db.Integer, nullable=True)  # 0=Female, 1=Male

    # ML Features
    neoFFI_q31 = db.Column(db.Float, nullable=True)
    neoFFI_q33 = db.Column(db.Float, nullable=True)
    neoFFI_q37 = db.Column(db.Float, nullable=True)
    neoFFI_q43 = db.Column(db.Float, nullable=True)
    neoFFI_q46 = db.Column(db.Float, nullable=True)
    neoFFI_q51 = db.Column(db.Float, nullable=True)
    n_oddb_CN = db.Column(db.Float, nullable=True)
    BDI_pre = db.Column(db.Float, nullable=True)
    rTMS_PROTOCOL = db.Column(db.Float, nullable=True)

    # Cascade: deleting a patient removes their predictions too
    predictions = db.relationship(
        "Prediction",
        backref="patient",
        lazy=True,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "doctor_id": self.doctor_id,
            "full_name": self.full_name,
            "patient_code": self.patient_code,
            "age": self.age,
            "gender": self.gender,
            "neoFFI_q31": self.neoFFI_q31,
            "neoFFI_q33": self.neoFFI_q33,
            "neoFFI_q37": self.neoFFI_q37,
            "neoFFI_q43": self.neoFFI_q43,
            "neoFFI_q46": self.neoFFI_q46,
            "neoFFI_q51": self.neoFFI_q51,
            "n_oddb_CN": self.n_oddb_CN,
            "BDI_pre": self.BDI_pre,
            "rTMS_PROTOCOL": self.rTMS_PROTOCOL,
        }
