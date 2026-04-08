from odoo import models, fields, api


class NotificationTemplate(models.Model):
    _name = 'spsl.notification.template'
    _description = 'SPSL Notification Template'
    _order = 'name'

    name = fields.Char(
        string='Template Name',
        required=True,
    )
    code = fields.Char(
        string='Template Code',
        required=True,
        # unique=True removed - not supported in Odoo 19
        index=True,
    )
    event_id = fields.Many2one(
        'spsl.notification.event',
        string='Event',
        required=True,
    )
    subject = fields.Char(
        string='Email Subject',
    )
    body_html = fields.Html(
        string='Email Body',
    )
    sms_body = fields.Text(
        string='SMS Body',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )