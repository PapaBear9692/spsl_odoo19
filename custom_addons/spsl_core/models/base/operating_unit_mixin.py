from odoo import models, fields, api


class OperatingUnitMixin(models.AbstractModel):
    _name = 'spsl.operating.unit.mixin'
    _description = 'SPSL Operating Unit Mixin'

    operating_unit_id = fields.Many2one(
        'operating.unit',
        string='Branch',
        required=True,
        default=lambda self: self._default_operating_unit(),
        index=True,
    )

    @api.model
    def _default_operating_unit(self):
        # Get user's default operating unit
        user = self.env.user
        if user.default_operating_unit_id:
            return user.default_operating_unit_id.id
        # Fallback to company's default
        return self.env.company.default_operating_unit_id.id
