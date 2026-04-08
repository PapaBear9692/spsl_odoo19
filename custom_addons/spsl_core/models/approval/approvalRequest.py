from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ApprovalRequest(models.Model):
    _name = 'spsl.approval.request'
    _description = 'SPSL Approval Request'
    _order = 'id desc'
    _rec_name = 'id'

    name = fields.Char(
        string='Request Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self._generate_name(),
    )
    model = fields.Char(
        string='Model',
        required=True,
        index=True,
    )
    res_id = fields.Integer(
        string='Resource ID',
        required=True,
        index=True,
    )
    res_model_id = fields.Many2one(
        'ir.model',
        string='Document Model',
        compute='_compute_res_model_id',
        store=True,
        index=True,
    )
    res_name = fields.Char(
        string='Document Name',
        compute='_compute_res_name',
        store=True,
    )
    requested_by = fields.Many2one(
        'res.users',
        string='Requested By',
        required=True,
        default=lambda self: self.env.user.id,
        index=True,
    )
    requested_date = fields.Datetime(
        string='Requested Date',
        required=True,
        default=fields.Datetime.now,
        index=True,
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
    rejected_by = fields.Many2one(
        'res.users',
        string='Rejected By',
        copy=False,
        index=True,
    )
    rejected_date = fields.Datetime(
        string='Rejected Date',
        copy=False,
        index=True,
    )
    rejection_reason = fields.Text(
        string='Rejection Reason',
        copy=False,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        copy=False,
        index=True,
    )
    approval_level_id = fields.Many2one(
        'spsl.approval.level',
        string='Current Approval Level',
        copy=False,
        index=True,
    )
    note = fields.Text(
        string='Notes',
    )

    @api.depends('model', 'res_id')
    def _compute_res_model_id(self):
        for record in self:
            if record.model:
                record.res_model_id = self.env['ir.model']._get_id(record.model)
            else:
                record.res_model_id = False

    @api.depends('model', 'res_id')
    def _compute_res_name(self):
        for record in self:
            if record.model and record.res_id:
                res = self.env[record.model].browse(record.res_id)
                record.res_name = res.display_name if res.exists() else False
            else:
                record.res_name = False

    def _generate_name(self):
        sequence = self.env['ir.sequence'].next_by_code('spsl.approval.request')
        return sequence or f'APR/{fields.Date.today().year}/0000'

    def action_submit(self):
        self.write({'state': 'pending'})
        return True

    def action_approve(self):
        self.write({
            'state': 'approved',
            'approved_by': self.env.user.id,
            'approved_date': fields.Datetime.now(),
        })
        return True

    def action_reject(self, reason=''):
        self.write({
            'state': 'rejected',
            'rejected_by': self.env.user.id,
            'rejected_date': fields.Datetime.now(),
            'rejection_reason': reason,
        })
        return True

    def action_cancel(self):
        self.write({'state': 'cancelled'})
        return True