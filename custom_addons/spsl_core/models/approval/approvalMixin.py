from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError
from datetime import datetime, timedelta


class ApprovalMixin(models.AbstractModel):
    _name = 'spsl.approval.mixin'
    _description = 'SPSL Approval Mixin'

    approval_request_id = fields.Many2one(
        'spsl.approval.request',
        string='Approval Request',
        copy=False,
        index=True,
    )
    approval_state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('pending', 'Pending Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('cancelled', 'Cancelled'),
        ],
        string='Approval State',
        default='draft',
        copy=False,
        index=True,
    )
    approval_required = fields.Boolean(
        string='Approval Required',
        default=False,
        copy=False,
    )
    approved_by = fields.Many2one(
        'res.users',
        string='Approved By',
        copy=False,
        index=True,
    )
    approved_date = fields.Datetime(
        string='Approved Date',
        copy=False,
        index=True,
    )
    rejection_reason = fields.Text(
        string='Rejection Reason',
        copy=False,
    )

    def action_submit_for_approval(self):
        for record in self:
            if not record.approval_required:
                continue
            if record.approval_state != 'draft':
                continue
            request = self.env['spsl.approval.request'].create({
                'model': record._name,
                'res_id': record.id,
                'requested_by': self.env.user.id,
            })
            record.write({
                'approval_request_id': request.id,
                'approval_state': 'pending',
            })
        return True

    def action_approve(self):
        for record in self:
            if record.approval_state != 'pending':
                continue
            record.write({
                'approval_state': 'approved',
                'approved_by': self.env.user.id,
                'approved_date': fields.Datetime.now(),
            })
            if record.approval_request_id:
                record.approval_request_id.action_approve()
        return True

    def action_reject(self, reason=''):
        for record in self:
            if record.approval_state != 'pending':
                continue
            record.write({
                'approval_state': 'rejected',
                'rejection_reason': reason,
            })
            if record.approval_request_id:
                record.approval_request_id.action_reject(reason)
        return True

    def action_cancel(self):
        for record in self:
            if record.approval_state in ['draft', 'pending']:
                record.write({'approval_state': 'cancelled'})
        return True