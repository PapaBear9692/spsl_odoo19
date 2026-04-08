from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import hashlib
import json


class AuditLog(models.Model):
    _name = 'spsl.audit.log'
    _description = 'SPSL Audit Log'
    _order = 'id desc'
    _rec_name = 'id'

    name = fields.Char(
        string='Log Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self._generate_name(),
    )
    model = fields.Char(
        string='Model',
        required=True,
        index=True,
    )
    res_id = fields.Integer(
        string='Resource ID',
        required=True,
        index=True,
    )
    res_name = fields.Char(
        string='Resource Name',
        compute='_compute_res_name',
        store=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        default=lambda self: self.env.user.id,
        index=True,
    )
    action = fields.Char(
        string='Action',
        required=True,
        index=True,
    )
    old_values = fields.Text(
        string='Old Values',
        copy=False,
    )
    new_values = fields.Text(
        string='New Values',
        copy=False,
    )
    changes = fields.Text(
        string='Changes',
        copy=False,
    )
    hash = fields.Char(
        string='Hash',
        required=True,
        copy=False,
        readonly=True,
        index=True,
    )
    previous_hash = fields.Char(
        string='Previous Hash',
        required=True,
        copy=False,
        readonly=True,
        index=True,
    )
    timestamp = fields.Datetime(
        string='Timestamp',
        required=True,
        default=fields.Datetime.now,
        index=True,
    )
    ip_address = fields.Char(
        string='IP Address',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        copy=False,
    )

    @api.depends('model', 'res_id')
    def _compute_res_name(self):
        for record in self:
            if record.model and record.res_id:
                res = self.env[record.model].browse(record.res_id)
                record.res_name = res.display_name if res.exists() else False
            else:
                record.res_name = False

    def _generate_name(self):
        sequence = self.env['ir.sequence'].next_by_code('spsl.audit.log')
        return sequence or f'AUD/{fields.Date.today().year}/0000'

    def _compute_hash(self, prev_hash, data):
        content = f"{prev_hash}|{data}"
        return hashlib.sha256(content.encode()).hexdigest()

    @api.model
    def _get_last_hash(self):
        last_log = self.search([], order='id desc', limit=1)
        return last_log.hash if last_log else '0' * 64

    def write(self, vals):
        res = super().write(vals)
        return res


class AuditConfig(models.Model):
    _name = 'spsl.audit.config'
    _description = 'SPSL Audit Configuration'
    _rec_name = 'model_id'

    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        required=True,
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