from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ApprovalLevel(models.Model):
    _name = 'spsl.approval.level'
    _description = 'SPSL Approval Level'
    _order = 'sequence, id'

    name = fields.Char(
        string='Level Name',
        required=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        required=True,
    )
    model_ids = fields.Many2many(
        'ir.model',
        string='Applicable Models',
    )
    user_ids = fields.Many2many(
        'res.users',
        string='Approvers',
    )
    is_escalation = fields.Boolean(
        string='Escalation Level',
        default=False,
        help='If checked, this level triggers escalation after timeout',
    )
    escalation_hours = fields.Integer(
        string='Escalation Timeout (Hours)',
        default=24,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )


class ApprovalTransition(models.Model):
    _name = 'spsl.approval.transition'
    _description = 'SPSL Approval Transition'

    name = fields.Char(
        string='Transition Name',
        required=True,
    )
    from_level_id = fields.Many2one(
        'spsl.approval.level',
        string='From Level',
    )
    to_level_id = fields.Many2one(
        'spsl.approval.level',
        string='To Level',
    )
    trigger = fields.Selection(
        selection=[
            ('approved', 'On Approval'),
            ('rejected', 'On Rejection'),
            ('manual', 'Manual'),
        ],
        string='Trigger',
        default='approved',
        required=True,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )