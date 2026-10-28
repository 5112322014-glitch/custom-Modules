from odoo import fields, models


class OfficeVisitorToken(models.Model):
    _name = 'office.visitor.token'
    _description = 'Office Visitor API Token'

    token = fields.Char(required=True, index=True, readonly=True)
    user_id = fields.Many2one(
        'res.users', required=True, ondelete='cascade', readonly=True)
    expires_at = fields.Datetime(required=True, readonly=True)
