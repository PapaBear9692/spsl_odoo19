# Copyright 2026 SPSL - Smart Printing Service Limited
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


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

    # Reminder tracking
    reminder_count = fields.Integer(
        string='Reminder Count',
        default=0,
        copy=False,
        help='Number of reminder notifications sent for this request.',
    )
    last_reminder_date = fields.Datetime(
        string='Last Reminder Date',
        copy=False,
        readonly=True,
        help='Timestamp of the most recent reminder notification.',
    )

    # Computed fields
    res_name = fields.Char(
        string='Document Name',
        compute='_compute_res_name',
        store=True,
    )
    days_pending = fields.Integer(
        string='Days Pending',
        compute='_compute_days_pending',
        store=False,
        help='Number of days since the request was submitted.',
    )
    approver_user_ids = fields.Many2many(
        'res.users',
        string='Eligible Approvers',
        compute='_compute_approver_user_ids',
        store=True,
        help='Resolved user IDs of all eligible approvers (specific user '
             'and group members). Used by record rules for visibility.',
    )

    # ---------------------------------------------------------------
    # Compute methods
    # ---------------------------------------------------------------
    @api.depends('requested_date', 'state')
    def _compute_days_pending(self):
        now = fields.Datetime.now()
        for record in self:
            if record.requested_date and record.state == 'pending':
                delta = now - record.requested_date
                record.days_pending = delta.days
            else:
                record.days_pending = 0

    @api.depends('rule_line_id', 'rule_line_id.approver_user_id', 'rule_line_id.approver_group_id')
    def _compute_approver_user_ids(self):
        for record in self:
            users = self.env['res.users']
            if record.rule_line_id:
                if record.rule_line_id.approver_user_id:
                    users |= record.rule_line_id.approver_user_id
                if record.rule_line_id.approver_group_id:
                    users |= record.rule_line_id.approver_group_id.with_context(
                        active_test=False
                    ).users
            record.approver_user_ids = users

    # ---------------------------------------------------------------
    # Deputy resolution
    # ---------------------------------------------------------------
    def _resolve_approver(self):
        """Resolve the effective approver for this request.

        Checks if the designated approver has an active deputy and
        returns the deputy instead. Sets deputy_approver_id on self
        when a deputy is found.

        Returns:
            res.users: The effective approver (deputy or original).
        """
        self.ensure_one()
        if not self.rule_line_id:
            return self.env['res.users']

        # Determine the intended approver
        approver = self.rule_line_id.approver_user_id
        if not approver and self.rule_line_id.approver_group_id:
            # Pick the first member of the group as the reference user
            group_users = self.rule_line_id.approver_group_id.with_context(
                active_test=False
            ).users
            approver = group_users[:1]

        if not approver:
            return self.env['res.users']

        # Check for active deputy
        deputy = self.env['spsl.approval.deputy']._get_deputy_for_user(approver.id)
        if deputy:
            self.deputy_approver_id = deputy
            return deputy

        return approver

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
        self.env['spsl.audit.log'].sudo()._log_action(
            model_name=self._name,
            record_id=self.id,
            action='write',
            record_name=self.name,
            field_changes='maker_checker_violation',
            old_values='',
            new_values=str({
                'requested_by': self.requested_by.name,
                'attempted_approver': user.name,
                'request_ref': self.name,
                'rule': 'GB-006 Maker-Checker Principle',
            }),
        )

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
        """Submit the approval request for review.

        Validates the record is in draft state, sets state='pending',
        records the submission date, resolves deputy approver if the
        designated approver is unavailable, and triggers the NE-pending
        notification event on the source document.
        """
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_(
                    'Only draft requests can be submitted.'
                ))
            # Pre-resolve deputy so it's visible in the UI
            record._resolve_approver()
        self.write({
            'state': 'pending',
            'requested_date': fields.Datetime.now(),
        })
        # Trigger NE-pending notification for each request
        for record in self:
            record._notify_approval_state('pending')
        return True

    def action_approve(self):
        """Approve the request.

        Resolves deputy approver at approval time (safety net in case
        deputy changed between submit and approve). Enforces GB-006
        Maker-Checker: the current user must not be the same person
        who submitted the request. Sets state='approved', records
        approver and timestamp, then calls _on_approval_complete()
        on the source document via the mixin hook.
        """
        for record in self:
            if record.state != 'pending':
                raise ValidationError(_(
                    'Only pending requests can be approved.'
                ))
            # Re-resolve deputy at approval time
            record._resolve_approver()
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
        # Call post-approval hook on source document and notify
        for record in self:
            # Log deputy approval in chatter
            if record.deputy_approver_id and record.document_ref:
                if hasattr(record.document_ref, 'message_post'):
                    record.document_ref.message_post(
                        body=_(
                            'Approval request %(ref)s was approved by '
                            '<b>%(deputy)s</b> acting as deputy for '
                            '<b>%(approver)s</b>.',
                            ref=record.name,
                            deputy=record.deputy_approver_id.name,
                            approver=record._get_approver_display_name(),
                        ),
                        subtype_xmlid='mail.mt_note',
                    )
            record._notify_approval_state('approved')
            if record.document_ref and hasattr(record.document_ref, '_on_approval_complete'):
                record.document_ref._on_approval_complete(record)
        return True

    def action_reject(self):
        """Reject the request.

        Requires rejection_reason (mandatory). Sets state='rejected',
        records rejecter and timestamp, then calls _on_approval_rejected()
        on the source document via the mixin hook.
        """
        for record in self:
            if record.state != 'pending':
                raise ValidationError(_(
                    'Only pending requests can be rejected.'
                ))
            if not record.rejection_reason:
                raise ValidationError(_(
                    'Rejection reason is required when rejecting a request.'
                ))
        self.write({
            'state': 'rejected',
            'rejected_by': self.env.user.id,
            'rejected_date': fields.Datetime.now(),
        })
        # Call post-rejection hook on source document and notify
        for record in self:
            record._notify_approval_state('rejected')
            if record.document_ref and hasattr(record.document_ref, '_on_approval_rejected'):
                record.document_ref._on_approval_rejected(record)
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
        """Reset a rejected request back to draft for resubmission.

        Only allowed from 'rejected' state. Clears all rejection fields.
        """
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

    # ---------------------------------------------------------------
    # Notification helpers
    # ---------------------------------------------------------------
    def _notify_approval_state(self, state):
        """Trigger notification event for the given approval state change.

        Posts an Odoo chatter message on the source document so that
        followers are notified. Uses the NE-pending / NE-approved /
        NE-rejected notification event codes.
        """
        state_labels = {
            'pending': 'Pending Approval',
            'approved': 'Approved',
            'rejected': 'Rejected',
        }
        for record in self:
            if record.document_ref and hasattr(record.document_ref, 'message_post'):
                record.document_ref.message_post(
                    body=_(
                        'Approval request %(ref)s has been <b>%(state)s</b>'
                        '%(by)s.',
                        ref=record.name,
                        state=state_labels.get(state, state),
                        by=_(' by %s' % self.env.user.name)
                        if state in ('approved', 'rejected') else '',
                    ),
                    subtype_xmlid='mail.mt_note',
                )

    def _notify_escalation(self, new_tier):
        """Post NE-escalation notification to the source document chatter."""
        for record in self:
            if record.document_ref and hasattr(record.document_ref, 'message_post'):
                approver_info = ''
                if new_tier.approver_group_id:
                    approver_info = new_tier.approver_group_id.name
                elif new_tier.approver_user_id:
                    approver_info = new_tier.approver_user_id.name
                record.document_ref.message_post(
                    body=_(
                        'Approval request %(ref)s has been <b>escalated</b> '
                        'to <b>%(approver)s</b> (tier: %(tier)s).',
                        ref=record.name,
                        approver=approver_info,
                        tier=new_tier.rule_id.name,
                    ),
                    subtype_xmlid='mail.mt_note',
                )

    # ---------------------------------------------------------------
    # Cron: Auto-escalation of overdue approvals
    # ---------------------------------------------------------------
    @api.model
    def _cron_escalate_overdue_approvals(self):
        """Scheduled action: escalate approval requests pending > 48 hours.

        For each overdue request:
        1. Find the next higher approval tier from spsl.approval.rule.line
        2. If a higher tier exists, update rule_line_id, set escalated=True
        3. If no higher tier exists, escalate to System Administrator group
        4. Trigger NE-escalation notification
        5. Log all escalations in the audit trail
        """
        cutoff = fields.Datetime.now() - timedelta(hours=48)
        overdue_requests = self.search([
            ('state', '=', 'pending'),
            ('requested_date', '<', cutoff),
            ('escalated', '=', False),
        ])

        for request in overdue_requests:
            next_tier = request._find_next_tier()
            if next_tier:
                request.write({
                    'rule_line_id': next_tier.id,
                    'escalated': True,
                    'escalation_date': fields.Datetime.now(),
                })
                request._notify_escalation(next_tier)
            else:
                # No higher tier — escalate to System Administrator group
                request.write({
                    'escalated': True,
                    'escalation_date': fields.Datetime.now(),
                })
                request._notify_escalation_fallback()

            # Log escalation in audit trail
            request._log_escalation(next_tier)

        _logger.info(
            'Approval escalation cron: processed %d overdue requests.',
            len(overdue_requests),
        )

    def _find_next_tier(self):
        """Find the next higher approval tier for this request.

        Returns the next spsl.approval.rule.line with a higher sequence
        than the current rule_line_id, or False if none exists.
        """
        self.ensure_one()
        if not self.rule_id or not self.rule_line_id:
            return False

        next_tier = self.env['spsl.approval.rule.line'].sudo().search([
            ('rule_id', '=', self.rule_id.id),
            ('sequence', '>', self.rule_line_id.sequence),
        ], limit=1, order='sequence asc')
        return next_tier or False

    def _notify_escalation_fallback(self):
        """Post escalation notification when no higher tier exists."""
        for record in self:
            if record.document_ref and hasattr(record.document_ref, 'message_post'):
                record.document_ref.message_post(
                    body=_(
                        'Approval request %(ref)s has been <b>escalated to '
                        'System Administrator</b> — no higher approval tier '
                        'is configured.',
                        ref=record.name,
                    ),
                    subtype_xmlid='mail.mt_note',
                )

    def _log_escalation(self, next_tier):
        """Log the escalation event in the audit trail."""
        self.ensure_one()
        self.env['spsl.audit.log'].sudo()._log_action(
            model_name=self._name,
            record_id=self.id,
            action='write',
            record_name=self.name,
            field_changes='rule_line_id, escalated',
            old_values=str({
                'rule_line_id': self.rule_line_id.id if self.rule_line_id else False,
                'escalated': False,
            }),
            new_values=str({
                'rule_line_id': next_tier.id if next_tier else False,
                'escalated': True,
                'escalation_date': str(fields.Datetime.now()),
                'next_tier_name': next_tier.rule_id.name if next_tier else 'System Administrator (no higher tier)',
            }),
        )

    # ---------------------------------------------------------------
    # Cron: Approval reminders (NE-reminder-24h / NE-reminder-48h)
    # ---------------------------------------------------------------
    @api.model
    def _cron_send_approval_reminders(self):
        """Scheduled action: send reminder notifications for pending approvals.

        Tiered reminders:
        - Pending > 24h and < 48h: NE-reminder-24h (standard reminder)
        - Pending > 48h (pre-escalation): NE-reminder-48h (urgent reminder)

        Uses reminder_count and last_reminder_date to avoid duplicate
        reminders. A reminder is only sent if:
        - 24h window: reminder_count == 0 (first reminder only)
        - 48h window: reminder_count <= 1 (second reminder, if not already sent)
        """
        now = fields.Datetime.now()
        cutoff_24h = now - timedelta(hours=24)
        cutoff_48h = now - timedelta(hours=48)

        # --- NE-reminder-48h: pending > 48h, urgent, pre-escalation ---
        urgent_requests = self.search([
            ('state', '=', 'pending'),
            ('requested_date', '<', cutoff_48h),
            ('reminder_count', '<=', 1),
        ])
        for request in urgent_requests:
            request._send_reminder_notification('48h')
            request.write({
                'reminder_count': request.reminder_count + 1,
                'last_reminder_date': now,
            })

        # --- NE-reminder-24h: pending > 24h and < 48h, standard ---
        standard_requests = self.search([
            ('state', '=', 'pending'),
            ('requested_date', '<', cutoff_24h),
            ('requested_date', '>=', cutoff_48h),
            ('reminder_count', '=', 0),
        ])
        for request in standard_requests:
            request._send_reminder_notification('24h')
            request.write({
                'reminder_count': request.reminder_count + 1,
                'last_reminder_date': now,
            })

        total = len(urgent_requests) + len(standard_requests)
        _logger.info(
            'Approval reminder cron: sent %d reminders '
            '(%d urgent 48h, %d standard 24h).',
            total, len(urgent_requests), len(standard_requests),
        )

    def _send_reminder_notification(self, reminder_type):
        """Send a reminder notification to the designated approver.

        Posts a chatter message on the source document and sends an
        Odoo internal notification to the approver group/user.

        Args:
            reminder_type: '24h' for standard or '48h' for urgent.
        """
        self.ensure_one()
        is_urgent = reminder_type == '48h'
        urgency_label = _('URGENT') if is_urgent else _('Reminder')
        hours_pending = '48+' if is_urgent else '24+'

        # Build approver info
        approver_info = self._get_approver_display_name()

        # Post chatter message on source document
        if self.document_ref and hasattr(self.document_ref, 'message_post'):
            self.document_ref.message_post(
                body=_(
                    '<b>[%(urgency)s — NE-reminder-%(type)s]</b> '
                    'Approval request %(ref)s has been pending for '
                    '<b>%(hours)s hours</b>. '
                    'Assigned to: %(approver)s.',
                    urgency=urgency_label,
                    type=reminder_type,
                    ref=self.name,
                    hours=hours_pending,
                    approver=approver_info,
                ),
                subtype_xmlid='mail.mt_note',
            )

        # Send internal notification to approver
        self._notify_approver(reminder_type, urgency_label, hours_pending)

    def _get_approver_display_name(self):
        """Return the display name of the designated approver."""
        self.ensure_one()
        if self.rule_line_id:
            if self.rule_line_id.approver_user_id:
                return self.rule_line_id.approver_user_id.name
            if self.rule_line_id.approver_group_id:
                return self.rule_line_id.approver_group_id.name
        return _('Unknown')

    def _notify_approver(self, reminder_type, urgency_label, hours_pending):
        """Send an Odoo activity/notification to the approver(s)."""
        self.ensure_one()
        # If a specific user is set, notify them directly
        if self.rule_line_id and self.rule_line_id.approver_user_id:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=self.rule_line_id.approver_user_id.id,
                note=_(
                    '%(urgency)s: Approval request %(ref)s has been pending '
                    'for %(hours)s hours. Document: %(doc)s',
                    urgency=urgency_label,
                    ref=self.name,
                    hours=hours_pending,
                    doc=self.res_name or '',
                ),
            )
        # If a group is set, notify group members
        elif self.rule_line_id and self.rule_line_id.approver_group_id:
            group_users = self.rule_line_id.approver_group_id.with_context(
                active_test=False
            ).users
            for user in group_users:
                self.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=user.id,
                    note=_(
                        '%(urgency)s: Approval request %(ref)s has been pending '
                        'for %(hours)s hours. Document: %(doc)s',
                        urgency=urgency_label,
                        ref=self.name,
                        hours=hours_pending,
                        doc=self.res_name or '',
                    ),
                )
