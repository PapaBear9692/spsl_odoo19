# Copyright 2026 SPSL - Smart Printing Service Limited
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import models, fields, api


class BranchMixin(models.AbstractModel):
    """Abstract model providing multi-branch/operating unit support.

    Inherit from this mixin to add operating unit isolation to any model.
    The mixin provides:
    - operating_unit_id: Link to the operating unit (branch)
    - Automatic default from user's default OU
    - Domain-based data isolation

    NOTE: Requires 'operating_unit' module from OCA to be installed.
    """

    _name = 'spsl.mixin.branch'
    _description = 'Branch/Operating Unit Mixin'

    # Commented out until operating_unit module is installed
    # operating_unit_id = fields.Many2one(
    #     'operating.unit',
    #     string='Operating Unit',
    #     required=True,
    #     readonly=True,
    #     default=lambda self: self._default_operating_unit_id(),
    #     index=True,
    # )

    def _default_operating_unit_id(self):
        """Get the default operating unit for the current user.

        Returns the user's default operating unit if set, otherwise
        returns the first operating unit the user has access to.
        """
        # TODO: Uncomment when operating_unit module is installed
        # user = self.env.user
        # if hasattr(user, 'default_operating_unit_id') and user.default_operating_unit_id:
        #     return user.default_operating_unit_id.id
        # if hasattr(user, 'operating_unit_ids') and user.operating_unit_ids:
        #     return user.operating_unit_ids[0].id
        return False

    # @api.model
    # def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
    #     """Override search to filter by operating unit."""
    #     user = self.env.user
    #     if not user._is_superuser() and hasattr(user, 'operating_unit_ids'):
    #         ou_domain = [('operating_unit_id', 'in', user.operating_unit_ids.ids)]
    #         args = expression.AND([args or [], ou_domain])
    #     return super()._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)

    def _check_operating_unit_access(self):
        """Verify the user has access to the record's operating unit."""
        # TODO: Implement when operating_unit module is installed
        return True
