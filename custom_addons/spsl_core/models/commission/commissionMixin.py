# Copyright 2026 SPSL - Smart Printing Service Limited
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import models, fields, api


class CommissionMixin(models.AbstractModel):
    """Abstract model providing commission calculation functionality.

    Inherit from this mixin to add commission eligibility and calculation
    to any model that inherits from this mixin.
    """

    _name = 'spsl.commission.mixin'
    _description = 'SPSL Commission Mixin'

    commission_eligible = fields.Boolean(
        string='Eligible for Commission',
        default=False,
        copy=False,
    )
    commission_amount = fields.Monetary(
        string='Commission Amount',
        currency_field='currency_id',
        default=0.0,
        copy=False,
    )

    # TODO: Uncomment when spsl_commission_entry model is created
    # commission_entry_id = fields.Many2one(
    #     'spsl.commission.entry',
    #     string='Commission Entry',
    #     copy=False,
    #     index=True,
    # )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )

    def _calculate_commission(self, rule):
        self.ensure_one()
        return 0.0
