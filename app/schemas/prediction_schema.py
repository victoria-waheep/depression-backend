from marshmallow import Schema, fields


class PredictionInputSchema(Schema):
    # Only patient_id is needed — features are read from the stored Patient record.
    patient_id = fields.Integer(required=True)
