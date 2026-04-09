# Copyright 2026 SPSL - Smart Printing Service Limited
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ApprovalMixin(models.AbstractModel):
    """Abstract model providing approval workflow functionality.

    Inherit from this mixin to add approval workflow to any model:
        _inherit = ['spsl.mixin.approval']

    The mixin provides:
    - approval_state: Current state of the approval workflow
    - approval_request_id: Link to the approval request record
    - requires_approval: Computed field based on matching approval rules
    - approval_status_display: Human-readable status label
    - _get_approval_rule(): Find matching rule for this model
    - _get_approval_tier(): Find matching tier based on trigger field value
    - _check_requires_approval(): Check if rule and tier exist
    """

    _name = 'spsl.mixin.approval'
    _description = 'Approval Workflow Mixin'

    # Approval States
    APPROVAL_DRAFT = 'draft'
    APPROVAL_PENDING = 'pending'
    APPROVAL_APPROVED = 'approved'
    APPROVAL_REJECTED = 'rejected'

    approval_state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('pending', 'Pending Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        string='Approval Status',
        default='draft',
        required=True,
        readonly=True,
        index=True,
        tracking=True,
    )
    approval_request_id = fields.Many2one(
        'spsl.approval.request',
        string='Approval Request',
        readonly=True,
        ondelete='set null',
    )
    requires_approval = fields.Boolean(
        string='Requires Approval',
        compute='_compute_requires_approval',
        store=False,
    )
    approval_status_display = fields.Char(
        string='Approval Status',
        compute='_compute_approval_status_display',
        store=False,
    )

    # ---------------------------------------------------------------
    # Compute methods
    # ---------------------------------------------------------------
    def _compute_requires_approval(self):
        """Determine if the record requires approval based on rules."""
        for record in self:
            record.requires_approval = record._check_requires_approval()

    def _compute_approval_status_display(self):
        """Return human-readable approval status."""
        state_labels = {
            'draft': _('Draft'),
            'pending': _('Pending Approval'),
            'approved': _('Approved'),
            'rejected': _('Rejected'),
        }
        for record in self:
            label = state_labels.get(record.approval_state, '')
            if record.approval_state == 'pending' and record.approval_request_id:
                label += _(' (Request: %s)', record.approval_request_id.name)
            record.approval_status_display = label

    # ---------------------------------------------------------------
    # CRUD overrides
    # ---------------------------------------------------------------
    # Fields that are always allowed to be written, even on approved records.
    _APPROVAL_IMMUTABLE_SYSTEM_FIELDS = {
        'write_date', 'write_uid', '__last_update',
        'message_ids', 'message_follower_ids', 'message_partner_ids',
        'activity_ids', 'activity_state', 'activity_date_deadline',
        'activity_summary', 'activity_type_id', 'activity_user_id',
    }

    def write(self, vals):
        """Block modifications to approved documents.

        Once approval_state is 'approved', no business field may be
        changed. Only system tracking fields and approval_state itself
        (for state transitions) are exempt. To modify an approved
        document, the approval must first be rejected, reverting the
        document to draft.
        """
        # Collect keys that are actual business fields
        business_fields = set(vals.keys()) - self._APPROVAL_IMMUTABLE_SYSTEM_FIELDS
        if business_fields:
            for record in self:
                if record.approval_state == self.APPROVAL_APPROVED:
                    # If the only business field being written is
                    # approval_state (state transition), allow it.
                    non_state = business_fields - {'approval_state'}
                    if non_state:
                        _logger.warning(
                            'Blocked write on approved %s id=%d by user=%s '
                            'fields=%s',
                            record._name, record.id,
                            self.env.user.login, non_state,
                        )
                        raise UserError(_(
                            'Approved documents cannot be modified. '
                            'To make changes, the approval must be rejected '
                            'and the document re-submitted.'
                        ))
        return super().write(vals)

    # ---------------------------------------------------------------
    # Rule & Tier matching
    # ---------------------------------------------------------------
    def _get_approval_rule(self):
        """Search spsl.approval.rule for a matching rule based on model name.

        Returns the first active rule matching self._name and current company.
        Returns False if no rule found.
        """
        self.ensure_one()
        rule = self.env['spsl.approval.rule'].sudo().search([
            ('model_name', '=', self._name),
            ('active', '=', True),
            '|',
            ('company_id', '=', self.env.company.id),
            ('company_id', '=', False),
        ], limit=1, order='company_id asc')
        return rule

    def _get_approval_tier(self):
        """Match the trigger field value against approval rule line thresholds.

        Reads the trigger field value from the current record and finds
        the matching tier in spsl.approval.rule.line where:
            amount_from <= trigger_value < amount_to (or amount_to == 0 for unlimited)

        Returns the matched spsl.approval.rule.line record or False.
        """
        self.ensure_one()
        rule = self._get_approval_rule()
        if not rule:
            return self.env['spsl.approval.rule.line']

        # Get the trigger field value
        trigger_value = 0.0
        if rule.field_trigger:
            trigger_value = getattr(self, rule.field_trigger, 0.0) or 0.0

        # Find matching tier: amount_from <= value < amount_to (0 = unlimited)
        tier = self.env['spsl.approval.rule.line'].sudo().search([
            ('rule_id', '=', rule.id),
            ('amount_from', '<=', trigger_value),
            '|',
            ('amount_to', '=', 0),
            ('amount_to', '>=', trigger_value),
        ], limit=1, order='sequence asc, amount_from asc')
        return tier

    def _check_requires_approval(self):
        """Return True if a matching rule and tier exist for this record.

        This checks:
        1. An active approval rule exists for this model
        2. The trigger field value falls within a defined tier
        """
        self.ensure_one()
        rule = self._get_approval_rule()
        if not rule:
            return False
        tier = self._get_approval_tier()
        return bool(tier)

    # ---------------------------------------------------------------
    # Actions
    # ---------------------------------------------------------------
    def action_submit_for_approval(self):
        """Submit the record for approval.

        Finds the matching rule and tier, creates an approval request,
        and transitions the state to pending.
        """
        self.ensure_one()
        if self.approval_state != self.APPROVAL_DRAFT:
            raise UserError(_('Only draft records can be submitted for approval.'))

        rule = self._get_approval_rule()
        tier = self._get_approval_tier()

        if not rule:
            raise UserError(_(
                'No approval rule found for model %(model)s.',
                model=self._name,
            ))
        if not tier:
            raise UserError(_(
                'No matching approval tier found for this record. '
                'Check the amount thresholds in the approval rule.'
            ))

        # Create approval request linked to this document
        approval_request = self.env['spsl.approval.request'].create({
            'name': self.env['ir.sequence'].next_by_code('spsl.approval.request')
                    or f'APR/{fields.Date.today().year}/0000',
            'document_ref': f'{self._name},{self.id}',
            'rule_id': rule.id,
            'rule_line_id': tier.id,
            'state': 'pending',
            'requested_by': self.env.user.id,
            'requested_date': fields.Datetime.now(),
        })

        self.write({
            'approval_state': self.APPROVAL_PENDING,
            'approval_request_id': approval_request.id,
        })
        return True

    # ---------------------------------------------------------------
    # Hook methods (override in downstream models)
    # ---------------------------------------------------------------
    def _on_approval_complete(self, approval_request):
        """Hook called when an approval request is approved.

        Override this method in downstream models to implement
        post-approval business logic. For example:

            def _on_approval_complete(self, approval_request):
                super()._on_approval_complete(approval_request)
                self.action_confirm()  # e.g. confirm a sale order

        Args:
            approval_request: The spsl.approval.request record that
                was approved.
        """
        self.ensure_one()

    def _on_approval_rejected(self, approval_request):
        """Hook called when an approval request is rejected.

        Override this method in downstream models to implement
        post-rejection business logic. For example:

            def _on_approval_rejected(self, approval_request):
                super()._on_approval_rejected(approval_request)
                self.write({'state': 'cancel'})

        Args:
            approval_request: The spsl.approval.request record that
                was rejected, containing rejection_reason.
        """
        self.ensure_one()

    def action_approve(self):
        """Approve the record."""
        self.ensure_one()
        if self.approval_state != self.APPROVAL_PENDING:
            raise UserError(_('Only pending records can be approved.'))

        self.write({'approval_state': self.APPROVAL_APPROVED})
        if self.approval_request_id:
            self.approval_request_id.action_approve()
        return True

    def action_reject(self, reason=''):
        """Reject the record."""
        self.ensure_one()
        if self.approval_state != self.APPROVAL_PENDING:
            raise UserError(_('Only pending records can be rejected.'))

        self.write({'approval_state': self.APPROVAL_REJECTED})
        if self.approval_request_id:
            self.approval_request_id.write({'rejection_reason': reason})
            self.approval_request_id.action_reject()
        return True

    def action_reset_to_draft(self):
        """Reset the record to draft state."""
        self.ensure_one()
        if self.approval_state not in (self.APPROVAL_REJECTED, self.APPROVAL_APPROVED):
            raise UserError(_('Only rejected or approved records can be reset to draft.'))

        self.write({
            'approval_state': self.APPROVAL_DRAFT,
            'approval_request_id': False,
        })
        return True
