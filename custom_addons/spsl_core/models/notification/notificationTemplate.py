# Copyright 2026 SPSL - Smart Printing Service Limited
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class NotificationTemplate(models.Model):
    _name = 'spsl.notification.template'
    _description = 'SPSL Notification Template'
    _order = 'event_code'
    _sql_constraints = [
        ('event_code_unique', 'UNIQUE(event_code)', 'Event code must be unique!'),
    ]

    event_code = fields.Char(
        string='Event Code',
        required=True,
        index=True,
        help='Unique code for the notification event (e.g., "NE-001").',
    )
    name = fields.Char(
        string='Event Name',
        required=True,
        help='Human-readable name (e.g., "Invoice Generated").',
    )
    description = fields.Text(
        string='Description',
        help='Description of what triggers this notification event.',
    )
    channels = fields.Many2many(
        'spsl.notification.channel',
        'spsl_notification_template_channel_rel',
        'template_id',
        'channel_id',
        string='Notification Channels',
        help='Select channels through which notifications are sent.',
    )
    recipient_type = fields.Selection(
        selection=[
            ('specific_user', 'Specific User'),
            ('role_group', 'Role/Group'),
            ('document_follower', 'Document Follower'),
            ('manager', 'Manager'),
            ('custom', 'Custom'),
        ],
        string='Recipient Type',
        required=True,
        default='specific_user',
        help='Determines who receives the notification.',
    )
    recipient_group_id = fields.Many2one(
        'res.groups',
        string='Recipient Group',
        help='Group to notify when recipient_type is "role_group".',
    )
    recipient_user_ids = fields.Many2many(
        'res.users',
        'spsl_notification_template_user_rel',
        'template_id',
        'user_id',
        string='Recipient Users',
        help='Specific users to notify when recipient_type is "specific_user".',
    )
    subject_template = fields.Char(
        string='Subject Template',
        help='Jinja2/QWeb template for notification subject (e.g., "Invoice {{object.name}} Generated").',
    )
    body_template = fields.Text(
        string='Body Template',
        help='Jinja2/QWeb template for notification body with HTML support.',
    )
    is_mandatory = fields.Boolean(
        string='Mandatory',
        default=False,
        help='If True, users cannot opt out of this notification.',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    escalation_delay_hours = fields.Integer(
        string='Escalation Delay (Hours)',
        default=0,
        help='Hours before escalation notification is sent. 0 = no escalation.',
    )
    escalation_template_id = fields.Many2one(
        'spsl.notification.template',
        string='Escalation Template',
        help='The escalation notification template to trigger after the delay.',
    )
    model_ids = fields.Many2many(
        'ir.model',
        'spsl_notification_template_model_rel',
        'template_id',
        'model_id',
        string='Applicable Models',
        help='Models that can use this notification template.',
    )

    @api.constrains('event_code')
    def _check_event_code_format(self):
        for record in self.event_code:
            if record and not record.startswith('NE-'):
                raise ValidationError(_('Event code must start with "NE-".'))

    @api.constrains('escalation_delay_hours')
    def _check_escalation_delay(self):
        for record in self:
            if record.escalation_delay_hours < 0:
                raise ValidationError(_('Escalation delay hours cannot be negative.'))

    def get_recipients(self, record):
        self.ensure_one()
        if self.recipient_type == 'specific_user':
            return self.recipient_user_ids
        elif self.recipient_type == 'role_group':
            return self.recipient_group_id.users if self.recipient_group_id else self.env['res.users']
        elif self.recipient_type == 'document_follower':
            return record.message_partner_ids if hasattr(record, 'message_partner_ids') else self.env['res.users']
        elif self.recipient_type == 'manager':
            if hasattr(record, 'user_id') and record.user_id:
                return record.user_id
            return self.env['res.users']
        elif self.recipient_type == 'custom':
            return self.recipient_user_ids
        return self.env['res.users']

    def render_template(self, record, template_type='body'):
        self.ensure_one()
        if template_type == 'subject':
            template = self.subject_template or ''
        else:
            template = self.body_template or ''
        try:
            return self.env['mail.template']._render_template(template, record._name, [record.id])
        except Exception:
            return template