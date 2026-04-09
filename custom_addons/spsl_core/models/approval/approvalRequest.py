# Copyright 2026 SPSL - Smart Printing Service Limited
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ApprovalRequest(models.Model):
    """Tracks approval requests for any document in the system.

    Each request links to a source document via a Reference field,
    binds to an approval rule and its matched tier, and tracks
    the full lifecycle from draft through approval/rejection.
    """
    _name = 'spsl.approval.request'
    _description = 'SPSL Approval Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _rec_name = 'name'

    # Identification
    name = fields.Char(
        string='Request Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self._generate_name(),
    )

    # Document reference (Odoo Reference — links to any model/record)
    document_ref = fields.Reference(
        selection='_selection_target_model',
        string='Document',
        required=True,
        readonly=True,
        index=True,
    )
    model_name = fields.Char(
        string='Model Name',
        compute='_compute_model_name',
        store=True,
        index=True,
    )
    record_id = fields.Integer(
        string='Record ID',
        compute='_compute_record_id',
        store=True,
        index=True,
    )

    # Rule binding
    rule_id = fields.Many2one(
        'spsl.approval.rule',
        string='Approval Rule',
        readonly=True,
        index=True,
    )
    rule_line_id = fields.Many2one(
        'spsl.approval.rule.line',
        string='Matched Tier',
        readonly=True,
        index=True,
        help='The approval tier line that matched the document amount.',
    )

    # State machine
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        string='Status',
        default='draft',
        required=True,
        copy=False,
        index=True,
        tracking=True,
    )

    # Request metadata
    requested_by = fields.Many2one(
        'res.users',
        string='Requested By',
        required=True,
        default=lambda self: self.env.user,
        index=True,
        readonly=True,
    )
    requested_date = fields.Datetime(
        string='Requested Date',
        default=fields.Datetime.now,
        readonly=True,
        index=True,
    )

    # Approval metadata
    approved_by = fields.Many2one(
        'res.users',
        string='Approved By',
        copy=False,
        readonly=True,
        index=True,
    )
    approved_date = fields.Datetime(
        string='Approved Date',
        copy=False,
        readonly=True,
    )

    # Rejection metadata
    rejected_by = fields.Many2one(
        'res.users',
        string='Rejected By',
        copy=False,
        readonly=True,
        index=True,
    )
    rejected_date = fields.Datetime(
        string='Rejected Date',
        copy=False,
        readonly=True,
    )

    # Comments & reason
    comments = fields.Text(
        string='Comments',
    )
    rejection_reason = fields.Text(
        string='Rejection Reason',
        copy=False,
    )

    # Escalation
    escalated = fields.Boolean(
        string='Escalated',
        default=False,
        copy=False,
    )
    escalation_date = fields.Datetime(
        string='Escalation Date',
        copy=False,
        readonly=True,
    )

    # Deputy approver
    deputy_approver_id = fields.Many2one(
        'res.users',
        string='Deputy Approver',
        help='User designated to approve on behalf of the original approver.',
    )

    # Computed fields
    res_name = fields.Char(
        string='Document Name',
        compute='_compute_res_name',
        store=True,
    )

    # ---------------------------------------------------------------
    # Constraints
    # ---------------------------------------------------------------
    @api.constrains('escalated', 'escalation_date')
    def _check_escalation_date(self):
        for record in self:
            if record.escalated and not record.escalation_date:
                raise ValidationError(_(
                    'Escalation date is required when request is escalated.'
                ))

    @api.constrains('approved_by')
    def _check_maker_checker(self):
        """GB-006 Maker-Checker Principle: preparer cannot be approver.

        Hard constraint — no override, not even for System Administrator.
        The same person who submitted a request cannot approve it.
        """
        for record in self:
            if record.approved_by and record.requested_by and record.approved_by == record.requested_by:
                # Log violation attempt in audit trail
                record._log_maker_checker_violation(record.approved_by)
                raise ValidationError(_(
                    'Maker-Checker Violation (GB-006): '
                    'The person who submitted this request (%(submitter)s) '
                    'cannot approve their own submission. '
                    'This is a hard constraint with no override.',
                    submitter=record.requested_by.name,
                ))

    # ---------------------------------------------------------------
    # Compute methods
    # ---------------------------------------------------------------
    @api.model
    def _selection_target_model(self):
        """Populate model selection from configured approval rules."""
        rules = self.env['spsl.approval.rule'].search([('active', '=', True)])
        model_names = set(rules.mapped('model_name'))
        result = []
        for model_name in sorted(model_names):
            if model_name in self.env:
                model_rec = self.env['ir.model']._get(model_name)
                if model_rec:
                    result.append((model_name, model_rec.name))
        return result

    @api.depends('document_ref')
    def _compute_model_name(self):
        for record in self:
            record.model_name = record.document_ref._name if record.document_ref else False

    @api.depends('document_ref')
    def _compute_record_id(self):
        for record in self:
            record.record_id = record.document_ref.id if record.document_ref else False

    @api.depends('document_ref')
    def _compute_res_name(self):
        for record in self:
            if record.document_ref:
                record.res_name = record.document_ref.display_name
            else:
                record.res_name = False

    # ---------------------------------------------------------------
    # Internal
    # ---------------------------------------------------------------
    def _log_maker_checker_violation(self, user):
        """Log a maker-checker violation attempt to the audit trail."""
        self.env['spsl.audit.log'].sudo().create({
            'model_name': self._name,
            'res_id': self.id,
            'operation': 'maker_checker_violation',
            'user_id': user.id,
            'old_values': False,
            'new_values': str({
                'requested_by': self.requested_by.name,
                'attempted_approver': user.name,
                'request_ref': self.name,
                'rule': 'GB-006 Maker-Checker Principle',
            }),
        })

    # ---------------------------------------------------------------
    # CRUD
    # ---------------------------------------------------------------
    def _generate_name(self):
        """Generate sequence-based reference: APR/YYYY/NNNNN."""
        sequence = self.env['ir.sequence'].next_by_code('spsl.approval.request')
        return sequence or f'APR/{fields.Date.today().year}/0000'

    # ---------------------------------------------------------------
    # Actions
    # ---------------------------------------------------------------
    def action_submit(self):
        """Submit the approval request for review."""
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_(
                    'Only draft requests can be submitted.'
                ))
        self.write({'state': 'pending'})
        return True

    def action_approve(self):
        """Approve the request.

        Enforces GB-006 Maker-Checker: the current user must not be
        the same person who submitted the request.
        """
        for record in self:
            if record.state != 'pending':
                raise ValidationError(_(
                    'Only pending requests can be approved.'
                ))
            # GB-006 Maker-Checker check
            if record.requested_by == self.env.user:
                record._log_maker_checker_violation(self.env.user)
                raise ValidationError(_(
                    'Maker-Checker Violation (GB-006): '
                    'You (%(user)s) submitted this request and cannot approve it. '
                    'A different user must review and approve.',
                    user=self.env.user.name,
                ))
        self.write({
            'state': 'approved',
            'approved_by': self.env.user.id,
            'approved_date': fields.Datetime.now(),
        })
        return True

    def action_reject(self, reason=''):
        """Reject the request."""
        for record in self:
            if record.state != 'pending':
                raise ValidationError(_(
                    'Only pending requests can be rejected.'
                ))
        self.write({
            'state': 'rejected',
            'rejected_by': self.env.user.id,
            'rejected_date': fields.Datetime.now(),
            'rejection_reason': reason,
        })
        return True

    def action_escalate(self):
        """Escalate the request to a higher authority."""
        for record in self:
            if record.state != 'pending':
                raise ValidationError(_(
                    'Only pending requests can be escalated.'
                ))
        self.write({
            'escalated': True,
            'escalation_date': fields.Datetime.now(),
        })
        return True

    def action_reset_to_draft(self):
        """Reset a rejected request back to draft for resubmission."""
        for record in self:
            if record.state != 'rejected':
                raise ValidationError(_(
                    'Only rejected requests can be reset to draft.'
                ))
        self.write({
            'state': 'draft',
            'rejected_by': False,
            'rejected_date': False,
            'rejection_reason': False,
        })
        return True
