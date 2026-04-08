# Copyright 2026 SPSL - Smart Printing Service Limited
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import models, fields


class TestApprovalModel(models.Model):
    """Test model to verify ApprovalMixin functionality."""
    _name = 'spsl.test.approval'
    _description = 'Test Approval Model'
    _inherit = ['spsl.mixin.approval']

    name = fields.Char(required=True)
    amount = fields.Float(default=0.0)


class TestAuditModel(models.Model):
    """Test model to verify AuditMixin functionality."""
    _name = 'spsl.test.audit'
    _description = 'Test Audit Model'
    _inherit = ['spsl.mixin.audit']

    name = fields.Char(required=True)
    value = fields.Integer(default=0)


class TestBranchModel(models.Model):
    """Test model to verify BranchMixin functionality."""
    _name = 'spsl.test.branch'
    _description = 'Test Branch Model'
    _inherit = ['spsl.mixin.branch']

    name = fields.Char(required=True)
