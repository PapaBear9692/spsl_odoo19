# Copyright 2026 SPSL - Smart Printing Service Limited
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class NotificationLog(models.Model):
    _name = 'spsl.notification.log'
    _description = 'SPSL Notification Log'
    _order = 'id desc'

    event_code = fields.Char(
        string='Event Code',
        required=True,
        index=True,
    )
    template_id = fields.Many2one(
        'spsl.notification.template',
        string='Template',
        index=True,
    )
    channel = fields.Selection(
        selection=[
            ('in_app', 'In-App'),
            ('email', 'Email'),
            ('sms', 'SMS'),
            ('push', 'Push'),
        ],
        string='Channel',
        required=True,
    )
    recipient_id = fields.Many2one(
        'res.users',
        string='Recipient User',
        index=True,
    )
    recipient_email = fields.Char(
        string='Recipient Email',
    )
    recipient_phone = fields.Char(
        string='Recipient Phone',
    )
    sent_date = fields.Datetime(
        string='Sent Date',
        default=fields.Datetime.now,
        index=True,
    )
    status = fields.Selection(
        selection=[
            ('queued', 'Queued'),
            ('sent', 'Sent'),
            ('delivered', 'Delivered'),
            ('failed', 'Failed'),
            ('bounced', 'Bounced'),
        ],
        string='Status',
        required=True,
        default='queued',
    )
    error_message = fields.Text(
        string='Error Message',
    )
    document_ref = fields.Reference(
        string='Document Reference',
        selection='_get_document_models',
    )
    retry_count = fields.Integer(
        string='Retry Count',
        default=0,
    )
    next_retry_date = fields.Datetime(
        string='Next Retry Date',
    )

    @api.model
    def _get_document_models(self):
        models = self.env['ir.model'].search([('is_mail_thread', '=', True)])
        return [(m.model, m.name) for m in models]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'sent_date' not in vals:
                vals['sent_date'] = fields.Datetime.now()
        return super().create(vals_list)

    def write(self, vals):
        # Only allow updating status-related fields (immutability for the rest)
        immutable_fields = {
            'event_code', 'template_id', 'channel', 'recipient_id',
            'recipient_email', 'recipient_phone', 'sent_date', 'document_ref',
        }
        for record in self:
            blocked = immutable_fields & set(vals.keys())
            if blocked:
                raise ValidationError(_(
                    'Notification log fields %(fields)s are immutable and cannot be modified.',
                    fields=', '.join(sorted(blocked)),
                ))
        return super().write(vals)

    @api.model
    def _auto_init(self):
        result = super()._auto_init()
        self.env.cr.execute("""
            CREATE INDEX IF NOT EXISTS spsl_notification_log_event_status_date_idx
            ON spsl_notification_log (event_code, status, sent_date)
        """)
        return result