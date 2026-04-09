# Copyright 2026 SPSL - Smart Printing Service Limited
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import models, fields


class NotificationChannel(models.Model):
    _name = 'spsl.notification.channel'
    _description = 'SPSL Notification Channel'
    _order = 'name'

    name = fields.Char(
        string='Channel Name',
        required=True,
    )
    code = fields.Char(
        string='Code',
        required=True,
        index=True,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    description = fields.Text(
        string='Description',
    )