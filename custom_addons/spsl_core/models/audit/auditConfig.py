from odoo import models, fields, api


class AuditConfig(models.Model):
    _name = 'spsl.audit.config'
    _description = 'SPSL Audit Configuration'
    _rec_name = 'model_id'

    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        required=True,
        ondelete='cascade',
    )
    model_name = fields.Char(
        string='Model Name',
        related='model_id.model',
        store=True,
    )
    audit_enabled = fields.Boolean(
        string='Enable Audit',
        default=True,
    )
    retention_years = fields.Integer(
        string='Retention (Years)',
        default=7,
    )
    track_create = fields.Boolean(
        string='Track Creation',
        default=True,
    )
    track_write = fields.Boolean(
        string='Track Updates',
        default=True,
    )
    track_delete = fields.Boolean(
        string='Track Deletion',
        default=True,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )