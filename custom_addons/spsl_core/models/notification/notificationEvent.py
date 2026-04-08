from odoo import models, fields, api


class NotificationEvent(models.Model):
    _name = 'spsl.notification.event'
    _description = 'SPSL Notification Event'
    _order = 'category, sequence'

    name = fields.Char(
        string='Event Name',
        required=True,
    )
    code = fields.Char(
        string='Event Code',
        required=True,
        # unique=True removed - not supported in Odoo 19
        index=True,
    )
    category = fields.Selection(
        selection=[
            ('approval', 'Approval'),
            ('document', 'Document'),
            ('alert', 'Alert'),
            ('reminder', 'Reminder'),
            ('system', 'System'),
        ],
        string='Category',
        required=True,
        index=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    description = fields.Text(
        string='Description',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )