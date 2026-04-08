from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SPSLBaseMixin(models.AbstractModel):
    _name = 'spsl.base.mixin'
    _description = 'SPSL Base Mixin'

    @api.model
    def _get_company(self):
        return self.env.company

    @api.model
    def _get_user(self):
        return self.env.user