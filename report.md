# SPSL Core Module - Development Report

## Module Status: ✅ Installable (with workarounds)

---

## Issues Encountered & Solutions

### 1. Missing Model Files
**Problem:** `__init__.py` files referenced models that didn't exist:
- `approvalTransition.py`
- `commissionEntry.py`

**Solution:** Commented out imports in:
- `custom_addons/spsl_core/models/approval/__init__.py`
- `custom_addons/spsl_core/models/commission/__init__.py`

```python
# from . import approvalTransition  # TODO: Create this file
# from . import commissionEntry  # TODO: Create this file
```

---

### 2. Many2one ondelete Parameter
**Problem:** `spsl.audit.config` model had Many2one to `ir.model` with unsupported `ondelete='restrict'`

**Error:**
```
ValueError: Field model_id of model spsl.audit.config is defined as ondelete='restrict' while having ir.model as comodel, the 'restrict' mode is not supported for this type of field
```

**Solution:** Changed to `ondelete='cascade'` in:
- `custom_addons/spsl_core/models/audit/auditConfig.py`

```python
model_id = fields.Many2one(
    'ir.model',
    string='Model',
    required=True,
    ondelete='cascade',  # Fixed
)
```

---

### 3. Deprecated Model Reference (account.period)
**Problem:** `spsl.commission.aggregation` referenced `account.period` which was removed in Odoo 17+

**Error:**
```
AssertionError: Field spsl.commission.aggregation.period_id with unknown comodel_name 'account.period'
```

**Solution:** Replaced Many2one with Date fields in:
- `custom_addons/spsl_core/models/commission/commissionAggregation.py`

```python
# Before:
period_id = fields.Many2one('account.period', ...)

# After:
date_from = fields.Date(string='From Date', required=True, index=True)
date_to = fields.Date(string='To Date', required=True, index=True)
```

---

### 4. Unknown Field Parameter (unique)
**Problem:** Fields using `unique=True` parameter which is not valid in Odoo 19

**Warning:**
```
Field spsl.notification.event.code: unknown parameter 'unique'
Field spsl.notification.template.code: unknown parameter 'unique'
Field spsl.commission.rule.code: unknown parameter 'unique'
```

**Solution:** Remove `unique` parameter or override `_valid_field_parameter` method. (Pending fix)

---

### 5. res.groups category_id Field Removed
**Problem:** In Odoo 19, `category_id` field was removed from `res.groups` model

**Error:**
```
ValueError: Invalid field 'category_id' in 'res.groups'
```

**Solution:** Simplified security XML in:
- `custom_addons/spsl_core/security/spsl_core_security.xml`

```xml
<!-- Before: -->
<record id="spsl_core_group_user" model="res.groups">
    <field name="name">User</field>
    <field name="category_id" ref="module_category_spsl"/>  <!-- REMOVED -->
    <field name="implied_ids" eval="[(4, ref('base.group_user'))]"/>
</record>

<!-- After: -->
<record id="spsl_core_group_user" model="res.groups">
    <field name="name">SPSL Core: User</field>
    <field name="implied_ids" eval="[(4, ref('base.group_user'))]"/>
</record>
```

---

### 6. operating_unit Module Incompatible
**Problem:** OCA's `operating_unit` module has incompatible version with Odoo 19

**Warning:**
```
WARNING SPSL odoo.modules.module: The module operating_unit has an incompatible version, setting installable=False
```

**Solution:** Commented out dependency and related code in:
1. `custom_addons/spsl_core/__manifest__.py`
2. `custom_addons/spsl_core/models/mixins/branch_mixin.py`

---

### 7. Commission Aggregation employee_id (Commented out
**Problem:** `spsl.commission.aggregation` referenced `hr.employee` model

**Solution:** Commented out the `employee_id` field and:
- `custom_addons/spsl_core/models/commission/commissionAggregation.py`

```python
_order = 'date_from desc'  # Removed employee_id from order

```

---

### 8. CommissionMixin commission_entry_id (Commented out
**Problem:** `commissionMixin` referenced `spsl.commission.entry` model which doesn't exist

**Solution:** Commented out the `commission_entry_id` field in:
- `custom_addons/spsl_core/models/commission/commissionMixin.py`

---

## Files Commented Out for Testing

**Files:**
- `custom_addons/spsl_core/models/__init__.py`
```python
# from . import test_model  # TODO: Uncomment when testing mixins
```
- `custom_addons/spsl_core/__manifest__.py`
```python
# Test Views (remove in production)
# "views/test_views.xml",
`` ```

- `custom_addons/spsl_core/models/__init__.py`
```python
# from . import mixins
from . import test_model
```

---

### 9. CommissionEntry employee_id Commented out
**Problem:** `CommissionEntry` model referenced `hr.employee` which doesn't exist

**Solution:** Commented out the `employee_id` field in:
- `custom_addons/spsl_core/models/commission/commissionRule.py`
    - `custom_addons/spsl_core/models/commission/commissionAggregation.py`

---

## How to Test Mixins later

When ready to test the mixin functionality:

### Step 1: Install operating_unit Module
```bash
# Download OCA operating_unit module compatible with Odoo 19
# Place in custom_addons folder
git clone https://github.com/OCA/operating-unit.git -b 19.0
```

### Step 2: Uncomment Files

**File:** `custom_addons/spsl_core/__manifest__.py`
```python
"depends": [
    "base",
    "mail",
    "operating_unit",  # UNCOMMENT THIS
],
```

**File:** `custom_addons/spsl_core/models/__init__.py`
```python
from . import test_model  # UNCOMMENT THIS
```

**File:** `custom_addons/spsl_core/__manifest__.py` (data section)
```python
"views/test_views.xml",  # UNCOMMENT THIS
```

**File:** `custom_addons/spsl_core/models/mixins/branch_mixin.py`
```python
# UNCOMMENT operating_unit_id field and related methods
```

### Step 3: Update Module
```bash
python odoo-bin -c odoo.conf -d S SLSL -u sp_sl_core
```

### Step 4: Test in UI
1. Go to **Settings → Technical → Test Approval** - Test ApprovalMixin
2. Go to **Settings → Technical → Test Audit** - Test AuditMixin
3. Go to **Settings → Technical → Test Branch** - Test BranchMixin

4. Check `spsl.audit.log` model for audit entries

5. Test via Shell
```bash
python odoo-bin -c odoo.conf -d SPSL --shell

```

### Remaining Tasks

1. Fix `unique` parameter warnings - Override `_valid_field_parameter` or remove `unique=True`
2. Create missing model files:
   - `approvalTransition.py`
   - `commissionEntry.py`
3. Install OCA operating_unit module (when available for Odoo 19)
4. Add unit tests in `tests/` directory
5. Add missing access rules for CSV warning:
