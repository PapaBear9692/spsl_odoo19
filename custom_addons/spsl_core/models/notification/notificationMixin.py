from odoo import models, fields, api


class NotificationMixin(models.AbstractModel):
    _name = 'spsl.notification.mixin'
    _description = 'SPSL Notification Mixin'

    notification_preference = fields.Selection(
        selection=[
            ('email', 'Email'),
            ('sms', 'SMS'),
            ('both', 'Email and SMS'),
            ('none', 'None'),
        ],
        string='Notification Preference',
        default='email',
        copy=False,
    )

    def _send_notification(self, event_code, template_code, context=None):
        self.ensure_one()
        event = self.env['spsl.notification.event'].search([
            ('code', '=', event_code),
            ('active', '=', True),
        ], limit=1)
        if not event:
            return False
        template = self.env['spsl.notification.template'].search([
            ('code', '=', template_code),
            ('event_id', '=', event.id),
            ('active', '=', True),
        ], limit=1)
        if not template:
            return False
        return self.env['spsl.notification.log']._dispatch_notification(
            self, event, template, context or {}
        )