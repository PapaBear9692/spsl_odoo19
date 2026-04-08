# Copyright 2026 SPSL - Smart Printing Service Limited
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import models, fields, api


class ApprovalMixin(models.AbstractModel):
    """Abstract model providing approval workflow functionality.

    Inherit from this mixin to add approval workflow to any model.
    The mixin provides:
    - approval_state: Current state of the approval workflow
    - approval_request_id: Link to the approval request record
    - requires_approval: Computed field to determine if approval is needed
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

    def _compute_requires_approval(self):
        """Determine if the record requires approval based on approval rules.

        Override this method in inheriting models to implement custom logic.
        """
        for record in self:
            record.requires_approval = bool(record.approval_request_id)

    def action_submit_for_approval(self):
        """Submit the record for approval.

        Creates an approval request and updates the state.
        """
        self.ensure_one()
        if self.approval_state != self.APPROVAL_DRAFT:
            return False

        # Create approval request
        approval_request = self.env['spsl.approval.request'].create({
            'model': self._name,
            'res_id': self.id,
            'state': 'pending',
        })

        self.write({
            'approval_state': self.APPROVAL_PENDING,
            'approval_request_id': approval_request.id,
        })
        return True

    def action_approve(self):
        """Approve the record."""
        self.ensure_one()
        if self.approval_state != self.APPROVAL_PENDING:
            return False

        self.write({'approval_state': self.APPROVAL_APPROVED})
        if self.approval_request_id:
            self.approval_request_id.action_approve()
        return True

    def action_reject(self, reason=''):
        """Reject the record."""
        self.ensure_one()
        if self.approval_state != self.APPROVAL_PENDING:
            return False

        self.write({'approval_state': self.APPROVAL_REJECTED})
        if self.approval_request_id:
            self.approval_request_id.action_reject(reason)
        return True

    def action_reset_to_draft(self):
        """Reset the record to draft state."""
        self.ensure_one()
        if self.approval_state not in (self.APPROVAL_REJECTED, self.APPROVAL_APPROVED):
            return False

        self.write({
            'approval_state': self.APPROVAL_DRAFT,
            'approval_request_id': False,
        })
        return True
