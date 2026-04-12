"""
Expand wage / contract_wage visibility beyond the default hr.group_hr_manager.

Task 3.6.7 (a): Employee salary fields must be visible to
    HR Manager, Payroll Officer, CFO  (and transitively System Administrator).

The groups string is resolved lazily by the ORM, so referencing
spsl_access groups defined in the same module is safe — they will
exist by the time any user accesses the field.
"""

from odoo import fields, models


class HrVersion(models.Model):
    _inherit = "hr.version"

    wage = fields.Monetary(
        groups="hr.group_hr_manager,"
               "spsl_access.group_payroll_officer,"
               "spsl_access.group_cfo",
    )
    contract_wage = fields.Monetary(
        groups="hr.group_hr_manager,"
               "spsl_access.group_payroll_officer,"
               "spsl_access.group_cfo",
    )


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    # contract_wage is an explicit related field on hr.employee with its own
    # groups attribute — must be overridden separately from hr.version.
    contract_wage = fields.Monetary(
        groups="hr.group_hr_manager,"
               "spsl_access.group_payroll_officer,"
               "spsl_access.group_cfo",
    )
