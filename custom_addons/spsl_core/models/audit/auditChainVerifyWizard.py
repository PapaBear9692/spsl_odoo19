# Copyright 2026 SPSL - Smart Printing Service Limited
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import models, fields, api


class AuditChainVerifyWizard(models.TransientModel):
    """Wizard to display audit chain verification results."""
    
    _name = 'spsl.audit.chain.verify.wizard'
    _description = 'Audit Chain Verification Wizard'
    
    total_checked = fields.Integer(
        string='Total Records Checked',
        readonly=True,
    )
    valid_count = fields.Integer(
        string='Valid Hashes',
        readonly=True,
    )
    broken_count = fields.Integer(
        string='Broken Links',
        readonly=True,
    )
    first_broken_timestamp = fields.Datetime(
        string='First Broken Link Timestamp',
        readonly=True,
    )
    broken_details = fields.Text(
        string='Broken Records Details',
        readonly=True,
    )
    is_valid = fields.Boolean(
        string='Chain Intact',
        compute='_compute_is_valid',
        store=False,
    )
    
    @api.depends('broken_count')
    def _compute_is_valid(self):
        for record in self:
            record.is_valid = record.broken_count == 0
    
    def action_close(self):
        """Close the wizard."""
        return {'type': 'ir.actions.act_window_close'}