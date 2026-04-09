# SPSL Core Module - Development Report

## Module Status: ✅ Installed & Running

---

## Issues Encountered & Solutions

### 1. Missing Model Files
**Problem:** `__init__.py` files referenced models that didn't exist:
- `approvalTransition.py` → Already defined in `approvalLevel.py` as `ApprovalTransition`
- `commissionEntry.py` → Already defined in `commissionRule.py` as `CommissionEntry`

**Solution:** Commented out duplicate imports in:
- `custom_addons/spsl_core/models/approval/__init__.py`
- `custom_addons/spsl_core/models/commission/__init__.py`

---

### 2. Many2one ondelete Parameter
**Problem:** `spsl.audit.config` had Many2one to `ir.model` with unsupported `ondelete='restrict'`

**Solution:** Changed to `ondelete='cascade'` in `models/audit/auditConfig.py`

---

### 3. Deprecated Model Reference (account.period)
**Problem:** `spsl.commission.aggregation` referenced `account.period` (removed in Odoo 17+)

**Solution:** Replaced with `date_from` and `date_to` Date fields in `models/commission/commissionAggregation.py`

---

### 4. Unknown Field Parameter (unique) ✅ FIXED
**Problem:** Fields using `unique=True` parameter which is not valid in Odoo 19

**Files affected:**
- `models/notification/notificationEvent.py`
- `models/notification/notificationTemplate.py`
- `models/commission/commissionRule.py`

**Solution:** Removed `unique=True` from all three files. Odoo 19 does not support the `unique` field parameter.

---

### 5. res.groups Fields Removed in Odoo 19
**Problem:** `category_id` and `users` fields removed from `res.groups` model in Odoo 19

**Solution:** Removed both fields from security XML in `security/spsl_core_groups.xml`

---

### 6. operating_unit Module Incompatible
**Problem:** OCA's `operating_unit` module has incompatible version with Odoo 19

**Solution:** Commented out dependency in `__manifest__.py` and `models/mixins/branch_mixin.py`

---

### 7. employee_id References (hr.employee) ✅ COMMENTED OUT
**Problem:** Models referenced `hr.employee` but `hr` module not installed

**Files affected:**
- `models/commission/commissionAggregation.py`
- `models/commission/commissionRule.py`

**Solution:** Commented out `employee_id` fields until `hr` module is installed

---

### 8. CommissionMixin commission_entry_id ✅ COMMENTED OUT
**Problem:** `commissionMixin` referenced `spsl.commission.entry` via Many2one

**Solution:** Commented out `commission_entry_id` field in `models/commission/commissionMixin.py`

---

### 9. Malformed ir.model.access.csv ✅ FIXED
**Problem:** CSV file had `#` comments, line breaks, and missing columns (not allowed in Odoo CSV)

**Solution:** Rewrote CSV with proper 8-column format: `id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink`

---

### 10. _sql_constraints Deprecation Warning
**Problem:** `_sql_constraints` attribute no longer supported in Odoo 19

**Warning:**
```
Model attribute '_sql_constraints' is no longer supported, please define model.Constraint on the model.
```

**Solution:** Pending — needs migration to `model.Constraint` (Odoo 19 convention)

---

### 11. Blank Page — Missing JS Registry Import ✅ FIXED
**Problem:** Browser showed blank page. `spsl_core.js` used `registry` without importing it.

**Error:** `ReferenceError: registry is not defined` crashed the entire Odoo web client.

**Solution:** Added `import { registry } from "@web/core/registry";` in `static/src/js/spsl_core.js`

**Key lesson:** A broken JS module in `web.assets_backend` can crash the entire Odoo web interface. Always import all dependencies.

---

### 12. odoo.osv.expression Deprecated ✅ FIXED
**Problem:** `audit_mixin.py` imported `from odoo.osv import expression` which is deprecated in Odoo 19

**Warning:**
```
Since 19.0, odoo.osv is deprecated use odoo.fields.Domain
```

**Solution:** Commented out the import in `models/mixins/audit_mixin.py`

---

## Models Updated

### spsl.approval.request — Major Update ✅
**File:** `models/approval/approvalRequest.py`

**Changes:**
- Replaced `model` + `res_id` with `document_ref` (Reference field)
- Added `model_name` and `record_id` as computed fields from `document_ref`
- Added `rule_id` (Many2one to `spsl.approval.rule`)
- Added `rule_line_id` (Many2one to `spsl.approval.rule.line` — matched tier)
- Added `escalated` (Boolean) and `escalation_date` (Datetime)
- Added `deputy_approver_id` (Many2one to `res.users`)
- Added `comments` (Text)
- Added state transition validation in `action_submit()`, `action_approve()`, `action_reject()`
- Added `action_escalate()` and `action_reset_to_draft()` methods
- Added `_check_escalation_date` constraint

### spsl.approval.rule — New ✅
**File:** `models/approval/approval_rule.py`

**Fields:** name, model_name (Selection from ir.model), field_trigger, active, company_id, line_ids (One2many)
**Constraint:** `_check_field_trigger_exists` validates field exists on target model

### spsl.approval.rule.line — New ✅
**File:** `models/approval/approval_rule.py`

**Fields:** rule_id, sequence, amount_from, amount_to, approver_group_id, approver_user_id, require_all
**Constraint:** `_check_amount_range` validates `amount_from < amount_to` (when `amount_to > 0`)

---

## Models Created (Full List)

| Model | File | Type | Status |
|-------|------|------|--------|
| `spsl.mixin.approval` | `models/mixins/approval_mixin.py` | Abstract | ✅ |
| `spsl.mixin.audit` | `models/mixins/audit_mixin.py` | Abstract | ✅ |
| `spsl.mixin.branch` | `models/mixins/branch_mixin.py` | Abstract | ✅ (partial) |
| `spsl.approval.request` | `models/approval/approvalRequest.py` | Model | ✅ Updated |
| `spsl.approval.level` | `models/approval/approvalLevel.py` | Model | ✅ |
| `spsl.approval.transition` | `models/approval/approvalLevel.py` | Model | ✅ |
| `spsl.approval.rule` | `models/approval/approval_rule.py` | Model | ✅ New |
| `spsl.approval.rule.line` | `models/approval/approval_rule.py` | Model | ✅ New |
| `spsl.audit.log` | `models/audit/auditLog.py` | Model | ✅ |
| `spsl.audit.config` | `models/audit/auditConfig.py` | Model | ✅ |
| `spsl.notification.event` | `models/notification/notificationEvent.py` | Model | ✅ |
| `spsl.notification.template` | `models/notification/notificationTemplate.py` | Model | ✅ |
| `spsl.notification.log` | `models/notification/notificationLog.py` | Model | ✅ |
| `spsl.commission.rule` | `models/commission/commissionRule.py` | Model | ✅ |
| `spsl.commission.entry` | `models/commission/commissionRule.py` | Model | ✅ |
| `spsl.commission.entry.line` | `models/commission/commissionRule.py` | Model | ✅ |
| `spsl.commission.aggregation` | `models/commission/commissionAggregation.py` | Model | ✅ (partial) |

---

## Files Commented Out

| File | What | Reason |
|------|------|--------|
| `__manifest__.py` | `"operating_unit"` dependency | OCA module incompatible with Odoo 19 |
| `__manifest__.py` | `"views/test_views.xml"` | Test only |
| `models/__init__.py` | `from . import test_model` | Test only |
| `models/mixins/branch_mixin.py` | `operating_unit_id` field | `operating.unit` model missing |
| `models/commission/commissionAggregation.py` | `employee_id` field | `hr.employee` model missing |
| `models/commission/commissionRule.py` | `employee_id` field | `hr.employee` model missing |
| `models/commission/commissionMixin.py` | `commission_entry_id` field | Self-referencing issue |
| `models/approval/__init__.py` | `approvalTransition` import | Already in `approvalLevel.py` |
| `models/commission/__init__.py` | `commissionEntry` import | Already in `commissionRule.py` |

---

## Security Groups Created

| Group ID | Name | Implies |
|----------|------|---------|
| `spsl_core_group_user` | SPSL Core: User | `base.group_user` |
| `spsl_core_group_manager` | SPSL Core: Manager | `spsl_core_group_user` |
| `spsl_core_group_admin` | SPSL Core: Administrator | `spsl_core_group_manager` |
| `group_spsl_approval_manager` | Approval Manager | `spsl_core_group_user` |
| `group_spsl_audit_viewer` | Audit Viewer | `spsl_core_group_user` |
| `group_spsl_notification_admin` | Notification Admin | `spsl_core_group_user` |
| `group_spsl_commission_manager` | Commission Manager | `spsl_core_group_user` |
| `group_hq_all_branches` | HQ All Branches | `spsl_core_group_manager` |

---

## Odoo 19 Breaking Changes Encountered

| Feature | Old (Odoo ≤18) | New (Odoo 19) | Impact |
|---------|----------------|---------------|--------|
| `category_id` on `res.groups` | Supported | Removed | Security XML simplified |
| `users` field on `res.groups` | Supported | Removed | Cannot assign users via XML |
| `unique=True` field param | Supported | Not supported | Removed from 3 models |
| `_sql_constraints` | Supported | Deprecated | Warning only, needs migration |
| `account.period` model | Available | Removed | Replaced with Date fields |
| `odoo.osv.expression` | Available | Deprecated | Use `odoo.fields.Domain` |
| JS module imports | Lenient | Strict | Missing import crashes web client |

---

## Testing Status

### Not Tested ⚠️

The following features could not be tested due to missing UI views:

1. **Approval Request** — No form/list view available for `spsl.approval.request` model
2. **Approval Queue** — Views exist in `views/approval_queue_views.xml` but not verified functional
3. **Chain Integrity** — Model exists but no dedicated UI to verify chain integrity
4. **Verify Audit Chain** — No page to display and verify audit chain records

Views need to be created or verified for:
- `spsl.approval.request` form and tree views
- Approval queue functionality
- Audit chain verification UI

---

## Remaining Tasks

1. **Migrate `_sql_constraints`** to Odoo 19 `model.Constraint` format in `approval_rule.py`
2. **Install OCA modules** when available for Odoo 19:
   - `operating_unit` → enables branch mixin
   - `hr` → enables employee fields
3. **Uncomment commented fields** after installing dependencies
4. **Add unit tests** in `tests/` directory
5. **Create views** for approval rule configuration UI
6. **Verify approval queue views** in `views/approval_queue_views.xml`
7. **Create audit chain verification views**

---

## How to Test Later

### Step 1: Install missing modules
```bash
git clone https://github.com/OCA/operating-unit.git -b 19.0 custom_addons/operating_unit
```

### Step 2: Uncomment files
- `__manifest__.py` → uncomment `"operating_unit"` and `"views/test_views.xml"`
- `models/__init__.py` → uncomment `from . import test_model`
- `models/mixins/branch_mixin.py` → uncomment `operating_unit_id` field
- `models/commission/*.py` → uncomment `employee_id` fields

### Step 3: Update module
```bash
python odoo-bin -c odoo.conf -d SPSL -u spsl_core
```

### Step 4: Verify
1. Settings → Technical → Test Approval
2. Settings → Technical → Test Audit
3. Settings → Technical → Test Branch
