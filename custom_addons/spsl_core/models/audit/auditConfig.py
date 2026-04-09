from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AuditConfig(models.Model):
    _name = 'spsl.audit.config'
    _description = 'SPSL Audit Configuration by Category'
    _rec_name = 'category'

    CATEGORY_SELECTION = [
        ('AT-001', 'Financial Transactions'),
        ('AT-002', 'Contract Changes'),
        ('AT-003', 'HR Master Data'),
        ('AT-004', 'System Configuration'),
        ('AT-005', 'Master Data'),
    ]

    category = fields.Selection(
        selection=CATEGORY_SELECTION,
        string='Audit Category',
        required=True,
    )
    name = fields.Char(
        string='Category Name',
        compute='_compute_name',
        store=True,
    )
    model_ids = fields.Many2many(
        'ir.model',
        'spsl_audit_config_model_rel',
        'config_id',
        'model_id',
        string='Models to Audit',
        help='Select models to include in this audit category',
    )
    audit_enabled = fields.Boolean(
        string='Enable Audit',
        default=True,
    )
    retention_years = fields.Integer(
        string='Retention (Years)',
        default=7,
    )
    track_create = fields.Boolean(
        string='Track Creation',
        default=True,
    )
    track_write = fields.Boolean(
        string='Track Updates',
        default=True,
    )
    track_delete = fields.Boolean(
        string='Track Deletion',
        default=True,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    @api.depends('category')
    def _compute_name(self):
        for record in self:
            record.name = dict(self.CATEGORY_SELECTION).get(record.category, '')

    @api.constrains('category')
    def _check_unique_category(self):
        for record in self:
            existing = self.search([
                ('category', '=', record.category),
                ('id', '!=', record.id),
            ])
            if existing:
                raise ValidationError(
                    f'Only one config allowed per category. Category {record.category} already exists.'
                )

    def _is_model_audited(self, model_name):
        """Check if a model is configured for auditing in any active category.
        
        Args:
            model_name: The technical model name (e.g., 'res.partner')
            
        Returns:
            dict with audit_enabled, track_create, track_write, track_delete
            or None if model is not in any active audit category
        """
        for config in self.search([('active', '=', True), ('audit_enabled', '=', True)]):
            model_names = config.model_ids.mapped('model')
            if model_name in model_names:
                return {
                    'audit_enabled': config.audit_enabled,
                    'track_create': config.track_create,
                    'track_write': config.track_write,
                    'track_delete': config.track_delete,
                    'category': config.category,
                }
        return None