from marshmallow import Schema, fields, validate, validates, ValidationError


class RegisterSchema(Schema):
    full_name = fields.String(required=True, validate=validate.Length(min=2, max=150))
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=6))
    role = fields.String(load_default="Patient", validate=validate.OneOf(["Doctor", "Patient"]))


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True)
