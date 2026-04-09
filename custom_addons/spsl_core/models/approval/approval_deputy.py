# Copyright 2026 SPSL - Smart Printing Service Limited
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ApprovalDeputy(models.Model):
    """Deputy approver assignment.

    When a designated approver is unavailable (on leave, traveling, etc.),
    a deputy can be assigned to handle approvals on their behalf during
    a specified date range. The deputy must still comply with GB-006
    maker-checker — they cannot approve their own submissions.
    """
    _name = 'spsl.approval.deputy'
    _description = 'Approval Deputy Approver'
    _order = 'date_from desc'

    user_id = fields.Many2one(
        'res.users',
        string='Absent Approver',
        required=True,
        ondelete='cascade',
        help='The approver who is unavailable.',
    )
    deputy_user_id = fields.Many2one(
        'res.users',
        string='Deputy Approver',
        required=True,
        ondelete='cascade',
        help='The user who will approve on behalf of the absent approver.',
    )
    date_from = fields.Date(
        string='From',
        required=True,
        default=fields.Date.today,
        help='Start date of the deputy period (inclusive).',
    )
    date_to = fields.Date(
        string='To',
        required=True,
        help='End date of the deputy period (inclusive).',
    )
    active = fields.Boolean(
        string='Active',
        compute='_compute_active',
        store=True,
        help='Automatically active when today falls within the date range.',
    )

    _sql_constraints = [
        (
            'check_not_self_deputy',
            'CHECK(user_id != deputy_user_id)',
            'A user cannot be their own deputy.',
        ),
    ]

    @api.depends('date_from', 'date_to')
    def _compute_active(self):
        today = fields.Date.today()
        for record in self:
            record.active = (
                record.date_from
                and record.date_to
                and record.date_from <= today <= record.date_to
            )

    @api.constrains('date_from', 'date_to')
    def _check_date_range(self):
        for record in self:
            if record.date_from and record.date_to and record.date_to < record.date_from:
                raise ValidationError(_(
                    'End date (%(to)s) must be on or after start date (%(from)s).',
                    to=record.date_to,
                    from_=record.date_from,
                ))

    @api.constrains('user_id', 'deputy_user_id', 'date_from', 'date_to')
    def _check_no_overlapping_deputies(self):
        """Prevent overlapping deputy assignments for the same approver."""
        for record in self:
            domain = [
                ('id', '!=', record.id),
                ('user_id', '=', record.user_id.id),
                ('date_from', '<=', record.date_to),
                ('date_to', '>=', record.date_from),
            ]
            if self.search_count(domain):
                raise ValidationError(_(
                    'An overlapping deputy assignment already exists for '
                    '%(user)s during this date range.',
                    user=record.user_id.name,
                ))

    @api.model
    def _get_deputy_for_user(self, user_id):
        """Return the deputy user for the given approver, if one is active today.

        Args:
            user_id: The res.users id of the absent approver.

        Returns:
            res.users record of the deputy, or False (empty recordset).
        """
        today = fields.Date.today()
        deputy_record = self.sudo().search([
            ('user_id', '=', user_id),
            ('date_from', '<=', today),
            ('date_to', '>=', today),
        ], limit=1, order='date_from desc')
        return deputy_record.deputy_user_id if deputy_record else self.env['res.users']
