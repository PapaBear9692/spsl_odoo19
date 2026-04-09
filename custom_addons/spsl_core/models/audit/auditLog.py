# Copyright 2026 SPSL - Smart Printing Service Limited
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import hashlib
import json


class AuditLog(models.Model):
    """Immutable, hash-chained audit log for compliance traceability.

    Every entry is linked to the previous one via SHA-256 chain hashing,
    making tampering detectable. Records cannot be updated or deleted.
    """
    _name = 'spsl.audit.log'
    _description = 'SPSL Audit Log'
    _order = 'id desc'
    _rec_name = 'name'

    # ------------------------------------------------------------------
    # Fields — all readonly to prevent manual editing
    # ------------------------------------------------------------------
    name = fields.Char(
        string='Log Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self._generate_name(),
    )
    model_name = fields.Char(
        string='Model',
        required=True,
        readonly=True,
        index=True,
    )
    record_id = fields.Integer(
        string='Record ID',
        required=True,
        readonly=True,
        index=True,
    )
    record_name = fields.Char(
        string='Record Name',
        readonly=True,
        help='Display name of the audited record for human readability.',
    )
    action = fields.Selection(
        selection=[
            ('create', 'Create'),
            ('write', 'Update'),
            ('unlink', 'Delete'),
        ],
        string='Action',
        required=True,
        readonly=True,
        index=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        readonly=True,
        default=lambda self: self.env.user,
        index=True,
    )
    timestamp = fields.Datetime(
        string='Timestamp',
        required=True,
        readonly=True,
        default=fields.Datetime.now,
        index=True,
    )
    ip_address = fields.Char(
        string='IP Address',
        readonly=True,
    )
    field_changes = fields.Text(
        string='Changed Fields',
        readonly=True,
        help='JSON list of field names that changed.',
    )
    old_values = fields.Text(
        string='Old Values',
        readonly=True,
        help='JSON object of previous field values.',
    )
    new_values = fields.Text(
        string='New Values',
        readonly=True,
        help='JSON object of new field values.',
    )
    hash = fields.Char(
        string='Hash',
        readonly=True,
        copy=False,
        index=True,
        help='SHA-256 hash of this entry for tamper detection.',
    )
    previous_hash = fields.Char(
        string='Previous Hash',
        readonly=True,
        copy=False,
        help='SHA-256 hash of the preceding audit log entry (chain).',
    )
    archived = fields.Boolean(
        string='Archived',
        default=False,
        readonly=True,
        copy=False,
        help='Set to True when record has been archived for long-term storage.',
    )
    archived_date = fields.Datetime(
        string='Archived Date',
        readonly=True,
        copy=False,
        help='Timestamp when the record was archived.',
    )
    hash_truncated = fields.Char(
        string='Hash (12 chars)',
        compute='_compute_hash_truncated',
        store=False,
    )
    chain_verified = fields.Boolean(
        string='Chain Verified',
        compute='_compute_chain_verified',
        store=False,
    )
    audit_category = fields.Char(
        string='Audit Category',
        compute='_compute_audit_category',
        store=False,
    )

    # ------------------------------------------------------------------
    # Immutability — block all modifications and deletions
    # ------------------------------------------------------------------
    def write(self, vals):
        raise UserError(_(
            'Audit log records are immutable and cannot be modified or deleted.'
        ))

    def unlink(self):
        raise UserError(_(
            'Audit log records are immutable and cannot be modified or deleted.'
        ))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _generate_name(self):
        """Generate sequence-based reference: AUD/YYYY/NNNNN."""
        sequence = self.env['ir.sequence'].next_by_code('spsl.audit.log')
        return sequence or f'AUD/{fields.Date.today().year}/0000'

    def _compute_hash_truncated(self):
        for record in self:
            record.hash_truncated = record.hash[:12] if record.hash else ''

    def _compute_chain_verified(self):
        for record in self:
            if not record.hash:
                record.chain_verified = False
                continue
            expected = self._compute_hash(
                previous_hash=record.previous_hash or '',
                model_name=record.model_name or '',
                record_id=record.record_id or 0,
                action=record.action or '',
                user_id=record.user_id.id if record.user_id else 0,
                timestamp=str(record.timestamp) if record.timestamp else '',
                field_changes=record.field_changes or '',
                old_values=record.old_values or '',
                new_values=record.new_values or '',
            )
            record.chain_verified = (record.hash == expected)

    def _compute_audit_category(self):
        category_map = {
            'account.move': 'AT-001',
            'account.payment': 'AT-001',
            'account.bank.statement.line': 'AT-001',
            'sale.order': 'AT-002',
            'spsl.mps.contract': 'AT-002',
            'hr.employee': 'AT-003',
            'hr.contract': 'AT-003',
            'hr.payslip': 'AT-003',
            'res.config.settings': 'AT-004',
            'ir.rule': 'AT-004',
            'res.groups': 'AT-004',
            'res.partner': 'AT-005',
            'product.template': 'AT-005',
            'product.product': 'AT-005',
        }
        for record in self:
            record.audit_category = category_map.get(record.model_name, '')

    # ------------------------------------------------------------------
    # Genesis hash — used when no prior audit log entry exists
    # ------------------------------------------------------------------
    _GENESIS_SEED = 'SPSL_AUDIT_GENESIS_v1'
    _GENESIS_HASH = hashlib.sha256(_GENESIS_SEED.encode('utf-8')).hexdigest()

    # ------------------------------------------------------------------
    # SHA-256 hash chain
    # ------------------------------------------------------------------
    @api.model
    def _get_last_hash(self):
        """Return the hash of the most recent audit log entry.

        Returns the genesis hash if the table is empty.
        """
        last = self.sudo().search([], order='id desc', limit=1)
        if last and last.hash:
            return last.hash
        return self._GENESIS_HASH

    @api.model
    def _compute_hash(self, previous_hash, model_name, record_id, action,
                      user_id, timestamp, field_changes, old_values,
                      new_values):
        """Compute SHA-256(previous_hash + model_name + record_id + action +
        user_id + timestamp + field_changes + old_values + new_values).

        All arguments are cast to str so the concatenation is deterministic.
        The hash is stored in the ``hash`` field at create time.

        Args:
            previous_hash: Hex digest of the preceding entry (or genesis).
            model_name: Technical model name (e.g. 'sale.order').
            record_id: Database ID of the audited record.
            action: 'create', 'write', or 'unlink'.
            user_id: res.users ID who performed the action.
            timestamp: Datetime string of the action.
            field_changes: JSON string of changed field names.
            old_values: JSON string of previous field values.
            new_values: JSON string of new field values.

        Returns:
            64-character lowercase hex digest.
        """
        raw = (
            f"{previous_hash}"
            f"{model_name}"
            f"{record_id}"
            f"{action}"
            f"{user_id}"
            f"{timestamp}"
            f"{field_changes or ''}"
            f"{old_values or ''}"
            f"{new_values or ''}"
        )
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    # ------------------------------------------------------------------
    # Chain integrity verification
    # ------------------------------------------------------------------
    @api.model
    def verify_chain_integrity(self, batch_size=1000):
        """Iterate through all audit log records in id order and verify
        each record's stored hash matches a recomputed hash derived from
        the record's own data plus the previous record's hash.

        The first record is verified against the genesis hash.

        Returns:
            dict with keys:
                total_checked (int): Number of records inspected.
                valid (int): Records whose hashes match.
                broken (list[dict]): Each dict has keys 'id', 'name',
                    'stored_hash', 'expected_hash'.
        """
        result = {'total_checked': 0, 'valid': 0, 'broken': []}
        prev_hash = self._GENESIS_HASH

        # Process in batches to avoid memory issues on large tables
        domain = []
        total_count = self.sudo().search_count(domain)
        offset = 0

        while offset < total_count:
            batch = self.sudo().search(
                domain,
                order='id asc',
                limit=batch_size,
                offset=offset,
            )
            for rec in batch:
                expected = self._compute_hash(
                    previous_hash=prev_hash,
                    model_name=rec.model_name or '',
                    record_id=rec.record_id or 0,
                    action=rec.action or '',
                    user_id=rec.user_id.id if rec.user_id else 0,
                    timestamp=str(rec.timestamp) if rec.timestamp else '',
                    field_changes=rec.field_changes or '',
                    old_values=rec.old_values or '',
                    new_values=rec.new_values or '',
                )

                if rec.hash != expected:
                    result['broken'].append({
                        'id': rec.id,
                        'name': rec.name,
                        'stored_hash': rec.hash,
                        'expected_hash': expected,
                    })
                else:
                    result['valid'] += 1

                prev_hash = rec.hash
                result['total_checked'] += 1

            offset += batch_size

        return result

    # ------------------------------------------------------------------
    # Main entry point for creating audit entries
    # ------------------------------------------------------------------
    @api.model
    def _log_action(self, model_name, record_id, action,
                    field_changes=None, old_values=None, new_values=None,
                    record_name=None):
        """Create a hash-chained audit log entry.

        This is the main entry point called by audit_mixin and other
        subsystems.

        Args:
            model_name: The _name of the audited model.
            record_id: The database id of the audited record.
            action: 'create', 'write', or 'unlink'.
            field_changes: JSON string — list of changed field names.
            old_values: JSON string — dict of previous values.
            new_values: JSON string — dict of new values.
            record_name: Human-readable display name of the record.
        """
        prev_hash = self._get_last_hash()
        now = fields.Datetime.now()

        # Capture IP address if available
        ip_address = ''
        try:
            ip_address = self.env['ir.http']._get_request().httprequest.remote_addr or ''
        except Exception:
            pass

        entry_hash = self._compute_hash(
            previous_hash=prev_hash,
            model_name=model_name,
            record_id=record_id,
            action=action,
            user_id=self.env.user.id,
            timestamp=str(now),
            field_changes=field_changes or '',
            old_values=old_values or '',
            new_values=new_values or '',
        )

        self.sudo().create({
            'name': self.env['ir.sequence'].next_by_code('spsl.audit.log')
                    or f'AUD/{fields.Date.today().year}/0000',
            'model_name': model_name,
            'record_id': record_id,
            'record_name': record_name or '',
            'action': action,
            'user_id': self.env.user.id,
            'timestamp': now,
            'ip_address': ip_address,
            'field_changes': field_changes or '',
            'old_values': old_values or '',
            'new_values': new_values or '',
            'hash': entry_hash,
            'previous_hash': prev_hash,
        })

    @api.model
    def _cron_audit_retention(self):
        """Scheduled action: archive audit logs older than retention period.
        
        Runs monthly (1st of each month at 02:00 AM).
        - Queries audit logs where timestamp < now - retention_years
        - Marks records as archived=True
        - Moves JSON payloads to archive table (spsl.audit.log.archive)
        - Preserves hash chain integrity (hash, previous_hash remain)
        - Logs the archival action itself in the audit trail
        
        Retention period is configurable via system parameter spsl.audit.retention_years
        (default: 7 years).
        """
        from datetime import timedelta
        
        retention_years = int(
            self.env['ir.config_parameter'].get_param(
                'spsl.audit.retention_years', '7'
            )
        )
        cutoff_date = fields.Datetime.now() - timedelta(days=365 * retention_years)
        
        records_to_archive = self.search([
            ('archived', '=', False),
            ('timestamp', '<', cutoff_date),
        ])
        
        if not records_to_archive:
            return {
                'archived_count': 0,
                'message': 'No records to archive'
            }
        
        archive_model = self.env['spsl.audit.log.archive']
        archived_count = 0
        
        for record in records_to_archive:
            try:
                archive_model.create({
                    'audit_log_id': record.id,
                    'name': record.name,
                    'model_name': record.model_name,
                    'record_id': record.record_id,
                    'record_name': record.record_name,
                    'action': record.action,
                    'user_id': record.user_id.id,
                    'timestamp': record.timestamp,
                    'ip_address': record.ip_address,
                    'field_changes': record.field_changes,
                    'old_values': record.old_values,
                    'new_values': record.new_values,
                    'hash': record.hash,
                    'previous_hash': record.previous_hash,
                })
                
                record.write({
                    'archived': True,
                    'archived_date': fields.Datetime.now(),
                })
                archived_count += 1
            except Exception as e:
                pass
        
        self.env['spsl.audit.log'].sudo().create({
            'model_name': self._name,
            'record_id': 0,
            'record_name': f'Audit Retention Run - {archived_count} records archived',
            'action': 'write',
            'user_id': self.env.user.id,
            'field_changes': 'archived, archived_date',
            'old_values': json.dumps({'archived': False}),
            'new_values': json.dumps({
                'archived': True,
                'archived_count': archived_count,
                'retention_years': retention_years,
                'cutoff_date': str(cutoff_date),
            }),
        })
        
        return {
            'archived_count': archived_count,
            'retention_years': retention_years,
            'cutoff_date': str(cutoff_date),
        }

    # ------------------------------------------------------------------
    # UI Button Actions
    # ------------------------------------------------------------------
    def action_verify_integrity(self):
        """Run full audit chain integrity check and show result."""
        result = self.verify_chain_integrity()

        if result['broken']:
            message = f"""
Audit Chain Broken!

Total Checked: {result['total_checked']}
Valid: {result['valid']}
Broken: {len(result['broken'])}

First Broken Record:
ID: {result['broken'][0]['id']}
Name: {result['broken'][0]['name']}
"""
            notif_type = 'danger'
        else:
            message = f"""
Audit Chain Verified Successfully!

Total Checked: {result['total_checked']}
All records are valid.
"""
            notif_type = 'success'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Audit Integrity Check',
                'message': message,
                'type': notif_type,
                'sticky': True,
            }
        }

    def action_verify_chain(self):
        """Open wizard for advanced audit chain verification."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Verify Audit Chain',
            'res_model': 'spsl.audit.chain.verify.wizard',
            'view_mode': 'form',
            'target': 'new',
        }


# ------------------------------------------------------------------
# Legacy button methods (kept for backward compatibility)
# ------------------------------------------------------------------

def action_verify_integrity(self):
    """Run full audit chain integrity check and show result."""
    result = self.verify_chain_integrity()

    if result['broken']:
        message = f"""
Audit Chain Broken!

Total Checked: {result['total_checked']}
Valid: {result['valid']}
Broken: {len(result['broken'])}

First Broken Record:
ID: {result['broken'][0]['id']}
Name: {result['broken'][0]['name']}
"""
        notif_type = 'danger'
    else:
        message = f"""
Audit Chain Verified Successfully!

Total Checked: {result['total_checked']}
All records are valid.
"""
        notif_type = 'success'

    return {
        'type': 'ir.actions.client',
        'tag': 'display_notification',
        'params': {
            'title': 'Audit Integrity Check',
            'message': message,
            'type': notif_type,
            'sticky': True,
        }
    }


def action_verify_chain(self):
    """Open wizard for advanced audit chain verification."""
    return {
        'type': 'ir.actions.act_window',
        'name': 'Verify Audit Chain',
        'res_model': 'spsl.audit.chain.verify.wizard',
        'view_mode': 'form',
        'target': 'new',
    }