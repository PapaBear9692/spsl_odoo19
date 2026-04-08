from odoo import models, fields, api


class CommissionAggregation(models.Model):
    _name = 'spsl.commission.aggregation'
    _description = 'SPSL Commission Aggregation'
    _order = 'date_from desc'  # Removed employee_id from order

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
    total_sales = fields.Monetary(
        string='Total Sales',
        currency_field='currency_id',
        default=0.0,
    )
    total_commission = fields.Monetary(
        string='Total Commission',
        currency_field='currency_id',
        default=0.0,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('computed', 'Computed'),
            ('approved', 'Approved'),
            ('paid', 'Paid'),
        ],
        string='Status',
        default='draft',
        required=True,
        index=True,
    )

    def _generate_name(self):
        sequence = self.env['ir.sequence'].next_by_code('spsl.commission.aggregation')
        return sequence or f'CMA/{fields.Date.today().year}/0000'