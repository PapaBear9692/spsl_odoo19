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

    def _send_notification(self, event_code, template_code=None, context=None):
        self.ensure_one()
        template = self.env['spsl.notification.template'].search([
            ('event_code', '=', event_code),
            ('active', '=', True),
        ], limit=1)
        if not template:
            return False
        return self.env['spsl.notification.dispatcher'].dispatch(
            event_code, self, context or {}
        )