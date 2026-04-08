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

## Models Created

| Model | File | Type | Status |
|-------|------|------|--------|
| `spsl.mixin.approval` | `models/mixins/approval_mixin.py` | Abstract | ✅ |
| `spsl.mixin.audit` | `models/mixins/audit_mixin.py` | Abstract | ✅ |
| `spsl.mixin.branch` | `models/mixins/branch_mixin.py` | Abstract | ✅ (partial) |
| `spsl.approval.request` | `models/approval/approvalRequest.py` | Model | ✅ |
| `spsl.approval.level` | `models/approval/approvalLevel.py` | Model | ✅ |
| `spsl.approval.transition` | `models/approval/approvalLevel.py` | Model | ✅ |
| `spsl.approval.rule` | `models/approval/approval_rule.py` | Model | ✅ NEW |
| `spsl.approval.rule.line` | `models/approval/approval_rule.py` | Model | ✅ NEW |
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

## Remaining Tasks

1. **Migrate `_sql_constraints`** to Odoo 19 `model.Constraint` format in `approval_rule.py`
2. **Install OCA modules** when available for Odoo 19:
   - `operating_unit` → enables branch mixin
   - `hr` → enables employee fields
3. **Uncomment commented fields** after installing dependencies
4. **Add unit tests** in `tests/` directory
5. **Create views** for approval rule configuration UI

---

## How to Test Later

### Step 1: Install missing modules
```bash
# When OCA releases Odoo 19 compatible versions
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
