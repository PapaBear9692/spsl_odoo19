# Copyright 2026 SPSL - Smart Printing Service Limited
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import models, fields


class ResUsersPush(models.Model):
    _name = 'res.users'
    _inherit = 'res.users'

    push_subscription = fields.Text(
        string='Push Subscription',
        help='JSON-encoded push subscription endpoint and keys (VAPID).',
    )