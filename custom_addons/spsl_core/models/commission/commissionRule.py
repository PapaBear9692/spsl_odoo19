from odoo import models, fields, api


class CommissionRule(models.Model):
    _name = 'spsl.commission.rule'
    _description = 'SPSL Commission Rule'
    _order = 'sequence, id'

    name = fields.Char(
        string='Rule Name',
        required=True,
    )
    code = fields.Char(
        string='Rule Code',
        required=True,
        unique=True,
        index=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    model_id = fields.Many2one(
        'ir.model',
        string='Applicable Model',
    )
    calculation_type = fields.Selection(
        selection=[
            ('percentage', 'Percentage'),
            ('fixed', 'Fixed Amount'),
            ('tiered', 'Tiered'),
        ],
        string='Calculation Type',
        required=True,
        default='percentage',
    )
    percentage = fields.Float(
        string='Percentage (%)',
        digits=(5, 2),
        default=0.0,
    )
    fixed_amount = fields.Monetary(
        string='Fixed Amount',
        currency_field='currency_id',
        default=0.0,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )


class CommissionEntry(models.Model):
    _name = 'spsl.commission.entry'
    _description = 'SPSL Commission Entry'
    _order = 'date_from, id'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self._generate_name(),
    )
    # TODO: Uncomment when hr module is installed
    # employee_id = fields.Many2one(
    #     'hr.employee',
    #     string='Employee',
    #     required=True,
    #     index=True,
    # )
    date_from = fields.Date(
        string='From Date',
        required=True,
        index=True,
    )
    date_to = fields.Date(
        string='To Date',
        required=True,
        index=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('computed', 'Computed'),
            ('approved', 'Approved'),
            ('paid', 'Paid'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        index=True,
    )
    line_ids = fields.One2many(
        'spsl.commission.entry.line',
        'entry_id',
        string='Lines',
    )
    total_amount = fields.Monetary(
        string='Total Amount',
        currency_field='currency_id',
        compute='_compute_total_amount',
        store=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )

    def _generate_name(self):
        sequence = self.env['ir.sequence'].next_by_code('spsl.commission.entry')
        return sequence or f'CME/{fields.Date.today().year}/0000'

    @api.depends('line_ids.amount')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = sum(record.line_ids.mapped('amount'))

    def action_compute(self):
        return True

    def action_approve(self):
        self.write({'state': 'approved'})
        return True


class CommissionEntryLine(models.Model):
    _name = 'spsl.commission.entry.line'
    _description = 'SPSL Commission Entry Line'

    entry_id = fields.Many2one(
        'spsl.commission.entry',
        string='Entry',
        required=True,
        index=True,
    )
    rule_id = fields.Many2one(
        'spsl.commission.rule',
        string='Rule',
        required=True,
    )
    model = fields.Char(
        string='Source Model',
    )
    res_id = fields.Integer(
        string='Source ID',
        index=True,
    )
    amount = fields.Monetary(
        string='Amount',
        currency_field='currency_id',
        required=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )