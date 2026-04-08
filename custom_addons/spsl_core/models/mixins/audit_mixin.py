# Copyright 2026 SPSL - Smart Printing Service Limited
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html)

import json
from odoo import models, api, fields
# from odoo.osv import expression  # Deprecated in Odoo 19


class AuditMixin(models.AbstractModel):
    """Abstract model providing audit trail functionality.

    Inherit from this mixin to automatically track create, write, and unlink
    operations on records. Audit logs are stored in spsl.audit.log model.
    """

    _name = 'spsl.mixin.audit'
    _description = 'Audit Trail Mixin'

    def _get_audit_config(self):
        """Check if audit is enabled for this model."""
        self.env.cr.execute(
            """
            SELECT audit_enabled, track_create, track_write, track_delete
            FROM spsl_audit_config
            WHERE model_name = %s AND active = TRUE
            """,
            (self._name,)
        )
        return self.env.cr.dictfetchone()

    def _create_audit_log(self, operation, old_values=None, new_values=None):
        """Create an audit log entry for the current operation."""
        self.ensure_one()

        audit_config = self._get_audit_config()
        if not audit_config:
            return False

        # Determine which fields to track
        tracked_fields = self._get_tracked_fields()

        def filter_values(values):
            if not values:
                return {}
            return {k: v for k, v in values.items() if k in tracked_fields}

        audit_log = self.env['spsl.audit.log'].create({
            'model_name': self._name,
            'res_id': self.id,
            'operation': operation,
            'user_id': self.env.user.id,
            'old_values': json.dumps(filter_values(old_values), default=str) if old_values else False,
            'new_values': json.dumps(filter_values(new_values), default=str) if new_values else False,
        })
        return audit_log

    def _get_tracked_fields(self):
        """Return list of field names to track in audit logs.

        Override this method in inheriting models to customize which fields
        are tracked. By default, tracks all non-computed, non-related fields.
        """
        self.ensure_one()
        tracked = []
        for name, field in self._fields.items():
            # Skip auto fields, computed fields, and related fields
            if name in ('id', 'create_date', 'create_uid', 'write_date', 'write_uid'):
                continue
            if field.compute or field.related:
                continue
            tracked.append(name)
        return tracked

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to log audit entries."""
        audit_config = self._get_audit_config()
        track_create = audit_config and audit_config.get('track_create', True)

        records = super().create(vals_list)

        if track_create:
            for record in records:
                new_values = {field: record[field] for field in record._get_tracked_fields() if field in record}
                record._create_audit_log('create', new_values=new_values)

        return records

    def write(self, vals):
        """Override write to log audit entries."""
        audit_config = self._get_audit_config()
        track_write = audit_config and audit_config.get('track_write', True)

        if track_write:
            # Store old values before write
            tracked_fields = self._get_tracked_fields()
            old_values_map = {}
            for record in self:
                old_values_map[record.id] = {
                    field: record[field] for field in tracked_fields if field in record
                }

        result = super().write(vals)

        if track_write:
            for record in self:
                new_values = {field: record[field] for field in tracked_fields if field in record and field in vals}
                old_values = {k: v for k, v in old_values_map.get(record.id, {}).items() if k in vals}
                if new_values != old_values:
                    record._create_audit_log('write', old_values=old_values, new_values=new_values)

        return result

    def unlink(self):
        """Override unlink to log audit entries."""
        audit_config = self._get_audit_config()
        track_delete = audit_config and audit_config.get('track_delete', True)

        if track_delete:
            # Store record info before deletion
            for record in self:
                old_values = {field: record[field] for field in record._get_tracked_fields() if field in record}
                record._create_audit_log('unlink', old_values=old_values)

        return super().unlink()
