# Copyright 2026 SPSL - Smart Printing Service Limited
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ApprovalRule(models.Model):
    """Defines which models require approval and what triggers the approval.

    Each rule binds to a specific model (e.g., sale.order) and specifies
    which field determines the approval tier (e.g., amount_total).
    Rule lines define the actual threshold levels.
    """
    _name = 'spsl.approval.rule'
    _description = 'SPSL Approval Rule'
    _order = 'name'

    name = fields.Char(
        string='Rule Name',
        required=True,
    )
    model_name = fields.Selection(
        selection='_selection_model_name',
        string='Document Model',
        required=True,
        help='The model this approval rule applies to (e.g., sale.order)',
    )
    field_trigger = fields.Char(
        string='Trigger Field',
        help='The monetary/numeric field name that determines which approval '
             'tier applies (e.g., amount_total)',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
    )
    line_ids = fields.One2many(
        'spsl.approval.rule.line',
        'rule_id',
        string='Approval Tiers',
    )

    _sql_constraints = [
        (
            'unique_rule_per_model_company',
            'UNIQUE(model_name, company_id)',
            'An approval rule already exists for this model and company.',
        ),
    ]

    @api.model
    def _selection_model_name(self):
        """Dynamically populate model selection from ir.model.

        Returns models that are not abstract, not transient,
        and are custom SPSL models or standard business models.
        """
        models = self.env['ir.model'].search([
            ('transient', '=', False),
        ], order='name')
        return [(m.model, m.name) for m in models]

    @api.constrains('model_name', 'field_trigger')
    def _check_field_trigger_exists(self):
        """Validate that field_trigger exists on the target model."""
        for record in self:
            if not record.field_trigger:
                continue
            if record.model_name not in self.env:
                raise ValidationError(_(
                    'Model "%(model_name)s" does not exist in the system.',
                    model_name=record.model_name,
                ))
            target_model = self.env[record.model_name]
            if record.field_trigger not in target_model._fields:
                raise ValidationError(_(
                    'Field "%(field_name)s" does not exist on model '
                    '"%(model_name)s". Available fields: %(available)s',
                    field_name=record.field_trigger,
                    model_name=record.model_name,
                    available=', '.join(
                        sorted(target_model._fields.keys())[:20]
                    ) + '...',
                ))


class ApprovalRuleLine(models.Model):
    """Defines approval tiers within a rule.

    Each line specifies an amount range and who can approve documents
    falling within that range.
    """
    _name = 'spsl.approval.rule.line'
    _description = 'SPSL Approval Rule Line'
    _order = 'sequence, amount_from'

    rule_id = fields.Many2one(
        'spsl.approval.rule',
        string='Rule',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    amount_from = fields.Float(
        string='Amount From',
        required=True,
        default=0.0,
        help='Lower threshold (inclusive).',
    )
    amount_to = fields.Float(
        string='Amount To',
        default=0.0,
        help='Upper threshold (inclusive). Set to 0 for unlimited.',
    )
    approver_group_id = fields.Many2one(
        'res.groups',
        string='Approver Group',
        required=True,
        help='Security group whose members can approve at this tier.',
    )
    approver_user_id = fields.Many2one(
        'res.users',
        string='Specific Approver',
        help='Override: assign a specific user instead of a group.',
    )
    require_all = fields.Boolean(
        string='Require All Members',
        default=False,
        help='If True, all group members must approve. '
             'If False, any one member suffices.',
    )

    @api.constrains('amount_from', 'amount_to')
    def _check_amount_range(self):
        """Validate that amount_from is less than amount_to (when set)."""
        for record in self:
            if record.amount_to > 0 and record.amount_from >= record.amount_to:
                raise ValidationError(_(
                    'Amount From (%(from_amount)s) must be less than '
                    'Amount To (%(to_amount)s).',
                    from_amount=record.amount_from,
                    to_amount=record.amount_to,
                ))
