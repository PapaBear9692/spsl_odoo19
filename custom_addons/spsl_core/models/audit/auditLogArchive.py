# Copyright 2026 SPSL - Smart Printing Service Limited
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import models, fields


class AuditLogArchive(models.Model):
    """Archive table for long-term storage of audit log payloads.
    
    This model stores the JSON payloads (old_values, new_values, field_changes)
    of archived audit log records. The original audit log record remains
    in spsl.audit.log with preserved hash chain integrity, but the detailed
    payloads are moved here for cold storage to reduce database size.
    """
    _name = 'spsl.audit.log.archive'
    _description = 'SPSL Audit Log Archive'
    _order = 'timestamp desc'
    _rec_name = 'name'

    audit_log_id = fields.Many2one(
        'spsl.audit.log',
        string='Original Audit Log',
        required=True,
        ondelete='restrict',
    )
    name = fields.Char(
        string='Log Reference',
        required=True,
        readonly=True,
    )
    model_name = fields.Char(
        string='Model',
        required=True,
        readonly=True,
    )
    record_id = fields.Integer(
        string='Record ID',
        required=True,
        readonly=True,
    )
    record_name = fields.Char(
        string='Record Name',
        readonly=True,
    )
    action = fields.Selection(
        selection=[
            ('create', 'Create'),
            ('write', 'Update'),
            ('unlink', 'Delete'),
        ],
        string='Action',
        required=True,
        readonly=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        readonly=True,
    )
    timestamp = fields.Datetime(
        string='Timestamp',
        required=True,
        readonly=True,
    )
    ip_address = fields.Char(
        string='IP Address',
        readonly=True,
    )
    field_changes = fields.Text(
        string='Changed Fields',
        readonly=True,
    )
    old_values = fields.Text(
        string='Old Values',
        readonly=True,
    )
    new_values = fields.Text(
        string='New Values',
        readonly=True,
    )
    hash = fields.Char(
        string='Hash',
        readonly=True,
    )
    previous_hash = fields.Char(
        string='Previous Hash',
        readonly=True,
    )
    archived_date = fields.Datetime(
        string='Archived Date',
        default=lambda self: fields.Datetime.now(),
        readonly=True,
    )