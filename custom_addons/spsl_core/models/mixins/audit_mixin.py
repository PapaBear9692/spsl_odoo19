# Copyright 2026 SPSL - Smart Printing Service Limited
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html)

import json
from odoo import models, api, fields
from odoo.exceptions import UserError


class AuditMixin(models.AbstractModel):
    """Abstract model providing audit trail functionality.

    Inherit from this mixin to automatically track create, write, and unlink
    operations on records. Audit logs are stored in spsl.audit.log model
    with SHA-256 hash chain for tamper detection.
    """

    _name = 'spsl.mixin.audit'
    _description = 'Audit Trail Mixin'

    _SKIP_FIELD_TYPES = ('binary', 'one2many', 'many2many')
    _SKIP_FIELD_NAMES = (
        'id', 'create_date', 'create_uid', 'write_date', 'write_uid',
        'message_ids', 'message_follower_ids', 'activity_ids',
    )

    def _get_audit_config(self):
        """Check if audit is enabled for this model.
        
        Returns dict with audit_enabled, track_create, track_write, track_delete.
        Uses the new category-based config (spsl.audit.config) to check if model
        is explicitly listed in an active audit category.
        """
        try:
            config_model = self.env['spsl.audit.config']
            result = config_model._is_model_audited(self._name)
            if result:
                return result
        except Exception:
            pass
        return None

    def _get_tracked_fields(self):
        """Return list of field names to track in audit logs.

        Override this method in inheriting models to customize which fields
        are tracked. By default, tracks all non-computed, non-related fields
        except Binary and One2many fields.
        """
        tracked = []
        for name, field in self._fields.items():
            if name in self._SKIP_FIELD_NAMES:
                continue
            if field.compute:
                continue
            if field.related:
                continue
            if field.type in self._SKIP_FIELD_TYPES:
                continue
            tracked.append(name)
        return tracked

    def _serialize_value(self, field_name, value):
        """Serialize a field value for audit logging.
        
        Handles Binary fields gracefully (skips large blobs) and serializes
        One2many fields as summary counts.
        """
        if value is None:
            return None
        
        field = self._fields.get(field_name)
        if not field:
            return str(value)
        
        if field.type == 'binary':
            if value:
                return '<binary data skipped>'
            return None
        
        if field.type in ('one2many', 'many2many'):
            if hasattr(value, '__iter__') and not isinstance(value, str):
                return f'<{field.type}: {len(list(value))} records>'
            return f'<{field.type}: {value}>'
        
        if field.type == 'many2one':
            if value:
                return {'id': value.id, 'display_name': value.display_name} if hasattr(value, 'id') else str(value)
            return None
        
        try:
            return json.dumps(value, default=str)
        except (TypeError, ValueError):
            return str(value)

    def _create_audit_log(self, action, old_values=None, new_values=None, field_changes=None):
        """Create an audit log entry for the current operation.
        
        Uses sudo() to ensure audit entries are created regardless of 
        the current user's permissions on the audit log model.
        
        Args:
            action: 'create', 'write', or 'unlink'
            old_values: dict of previous field values
            new_values: dict of new field values  
            field_changes: list of field names that changed (for write)
        """
        self.ensure_one()

        audit_config = self._get_audit_config()
        if not audit_config or not audit_config.get('audit_enabled', True):
            return False

        tracked_fields = self._get_tracked_fields()

        def serialize_values(values):
            if not values:
                return {}
            result = {}
            for k, v in values.items():
                if k in tracked_fields:
                    result[k] = self._serialize_value(k, v)
            return result

        serialized_old = serialize_values(old_values) if old_values else {}
        serialized_new = serialize_values(new_values) if new_values else {}

        try:
            record_name = ''
            try:
                record_name = self.display_name or ''
            except Exception:
                pass
            self.env['spsl.audit.log'].sudo().create({
                'model_name': self._name,
                'record_id': self.id,
                'record_name': record_name,
                'action': action,
                'user_id': self.env.user.id,
                'field_changes': json.dumps(field_changes) if field_changes else '',
                'old_values': json.dumps(serialized_old, default=str) if serialized_old else '',
                'new_values': json.dumps(serialized_new, default=str) if serialized_new else '',
            })
        except Exception as e:
            pass

        return True

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to log audit entries after record creation.
        
        After super().create(), calls _create_audit_log(action='create', 
        new_values=record_data) for each created record.
        """
        audit_config = self._get_audit_config()
        track_create = audit_config.get('track_create', True) if audit_config else True

        records = super().create(vals_list)

        if track_create:
            for record in records:
                tracked_fields = record._get_tracked_fields()
                new_values = {}
                for field in tracked_fields:
                    if field in record:
                        try:
                            new_values[field] = record[field]
                        except Exception:
                            pass
                record._create_audit_log(action='create', new_values=new_values)

        return records

    def write(self, vals):
        """Override write to log audit entries.
        
        Before super().write(), captures old values for changed fields.
        After super().write(), calls _create_audit_log(action='write', 
        old_values=old_data, new_values=vals, field_changes=list(vals.keys())).
        """
        audit_config = self._get_audit_config()
        track_write = audit_config.get('track_write', True) if audit_config else True

        tracked_fields = self._get_tracked_fields()
        old_values_map = {}

        if track_write and vals:
            for record in self:
                old_values = {}
                for field in tracked_fields:
                    if field in vals:
                        try:
                            old_values[field] = record[field]
                        except Exception:
                            pass
                old_values_map[record.id] = old_values

        result = super().write(vals)

        if track_write and vals:
            for record in self:
                old_values = old_values_map.get(record.id, {})
                field_changes = list(vals.keys())
                record._create_audit_log(
                    action='write',
                    old_values=old_values,
                    new_values=vals,
                    field_changes=field_changes
                )

        return result

    def unlink(self):
        """Override unlink to log audit entries before deletion.
        
        Before super().unlink(), captures full record data.
        Calls _create_audit_log(action='unlink', old_values=record_data).
        """
        audit_config = self._get_audit_config()
        track_delete = audit_config.get('track_delete', True) if audit_config else True

        if track_delete:
            for record in self:
                tracked_fields = record._get_tracked_fields()
                old_values = {}
                for field in tracked_fields:
                    try:
                        old_values[field] = record[field]
                    except Exception:
                        pass
                record._create_audit_log(action='unlink', old_values=old_values)

        return super().unlink()
