from marshmallow import Schema, fields, validate


class PatientSchema(Schema):
    full_name = fields.String(load_default=None)
    patient_code = fields.String(load_default=None)
    age = fields.Float(load_default=None)
    gender = fields.Integer(load_default=None, validate=validate.OneOf([0, 1]))
    neoFFI_q31 = fields.Float(load_default=None)
    neoFFI_q33 = fields.Float(load_default=None)
    neoFFI_q37 = fields.Float(load_default=None)
    neoFFI_q43 = fields.Float(load_default=None)
    neoFFI_q46 = fields.Float(load_default=None)
    neoFFI_q51 = fields.Float(load_default=None)
    n_oddb_CN = fields.Float(load_default=None)
    BDI_pre = fields.Float(load_default=None)
    rTMS_PROTOCOL = fields.Float(load_default=None)
