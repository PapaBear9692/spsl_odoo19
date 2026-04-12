# BRD_12 — Cross-Cutting Concerns
## SPSL ERP System — Project ELEVATE
### Smart Printing Solution Ltd.

---

## Document Control

| Field | Value |
|-------|-------|
| Document ID | SPSL-BRD-12 |
| Version | 1.0 |
| Status | Draft — Pending Sign-off |
| Date | 17 March 2026 |

---

## Table of Contents

1. Purpose and Scope
2. Notification and Alert Framework
3. Approval Workflow Framework
4. Audit Trail Specification
5. Document Management
6. Bangladesh Calendar and Date Handling
7. Multi-Branch Data Access Control
8. Mobile Financial Services (bKash / Nagad) Integration
9. Performance Requirements (Cross-Module)
10. Data Privacy and Security
11. Error Handling Standards
12. Integration Architecture Overview
13. System Monitoring and Alerting
14. Sign-off Matrix

---

## 1. Purpose and Scope

This document specifies all cross-cutting concerns — behaviors and services that apply to multiple modules. Rather than duplicating these specifications in each module BRD, they are defined once here and referenced by ID.

**Cross-cutting concerns covered:**
- Notification events (all modules generate notifications; all routing rules defined here)
- Approval workflows (approval matrix applies to all transaction types)
- Audit trail (all modules write to the same audit log)
- Bangladesh-specific calendar and date handling
- Multi-branch data isolation rules
- Performance benchmarks applicable to all modules
- Security and privacy requirements

Any module BRD that states "see BRD_12 §X" is referring to a section in this document.

---

## 2. Notification and Alert Framework

### 2.1 Notification Channels

| Channel | Use Case | Configuration |
|---------|---------|--------------|
| In-app notification | Real-time alerts within Odoo UI | Always active for all users |
| Email | Formal notifications, documents, reports | Per-event; email must be configured in user profile |
| SMS | Time-critical alerts; field staff | Per-event; gateway: Bangladesh SMS provider; requires mobile number |
| WhatsApp | Customer communication (future phase) | — |
| Push notification (PWA) | Field engineer mobile alerts | Requires engineer to grant push permission |

### 2.2 Notification Event Catalog

Every notification event has: Event ID, Trigger, Recipient(s), Channel, Content Template, Escalation Rule, Configurable?

#### Module: MPS

| Event ID | Trigger | Recipients | Channel | Escalation |
|---------|---------|-----------|---------|-----------|
| NE-001 | MPS invoice generated | Customer billing contact | Email + in-app | — |
| NE-002 | Meter reading not received by Day 3 of month | Customer + assigned Account Manager | Email + SMS | Day 5: MPS Coordinator |
| NE-003 | MPS contract expiry in 90 days | Account Manager | Email + in-app | — |
| NE-004 | MPS contract expiry in 30 days | Account Manager + MPS Manager | Email + SMS | Day 15: Sales Director |
| NE-005 | MPS contract expired (no renewal) | MPS Manager + Sales Director | Email + in-app | — |
| NE-006 | Disputed click record submitted | MPS Manager + Finance Manager | Email + in-app | — |

#### Module: AR / Finance

| Event ID | Trigger | Recipients | Channel | Escalation |
|---------|---------|-----------|---------|-----------|
| NE-010 | AR overdue Day 7 | Customer billing contact | Email (Level 1 dunning) | — |
| NE-011 | AR overdue Day 14 | Customer billing contact | Email + SMS (Level 2 dunning) | — |
| NE-012 | AR overdue Day 30 | Customer + Account Manager | Email + SMS (Level 3) | — |
| NE-013 | AR overdue Day 45 | Customer + Account Manager + Sales Director | Email + Phone call required | MD notification |
| NE-014 | Cash remittance not recorded by 4 PM | Branch Manager | SMS + in-app | 5 PM: Finance Manager |
| NE-015 | Cash remittance variance detected | CFO + Finance Manager | Email + in-app | — |
| NE-016 | Bank reconciliation overdue (>5th of month) | Finance Manager | Email + in-app | 7th: CFO |
| NE-017 | Monthly VAT return due in 5 days | Finance Manager | Email + in-app | — |
| NE-018 | Quarterly TDS return due in 5 days | Finance Manager | Email + in-app | — |
| NE-019 | LC expiry in 30 days | Finance Manager + Purchase Officer | Email + in-app | — |
| NE-020 | LC expiry in 7 days | CFO + Finance Manager | Email + SMS | — |
| NE-021 | Unbanked cash limit exceeded (branch >BDT 50K) | Branch Manager + Finance Manager | SMS + in-app | CFO if not resolved in 2h |

#### Module: Procurement

| Event ID | Trigger | Recipients | Channel | Escalation |
|---------|---------|-----------|---------|-----------|
| NE-025 | Purchase requisition awaiting approval | Approver | Email + in-app | 48h: Auto-escalate |
| NE-026 | PO approved | Purchase Officer | Email + in-app | — |
| NE-027 | PO overdue (delivery date passed, no GRN) | Purchase Officer + Operations Manager | Email + in-app | — |
| NE-028 | 3-way match exception | Finance Manager | Email + in-app | — |

#### Module: Field Engineer

| Event ID | Trigger | Recipients | Channel | Escalation |
|---------|---------|-----------|---------|-----------|
| NE-030 | New service ticket created | Assigned engineer | Push notification + SMS | — |
| NE-031 | Service ticket not acknowledged within 1h | Field Supervisor | SMS + in-app | 2h: Branch Manager |
| NE-032 | SLA response deadline in 1 hour | Engineer + Field Supervisor | Push + SMS | — |
| NE-033 | SLA response deadline breached | Engineer + Field Supervisor + Branch Manager | SMS + in-app | — |
| NE-034 | SLA resolution deadline in 2 hours | Engineer + Field Supervisor | Push + SMS | — |
| NE-035 | SLA resolution deadline breached | Field Supervisor + Branch Manager + MPS Manager | SMS + in-app | Operations Director |
| NE-036 | Parts requisition approved | Engineer | Push + in-app | — |
| NE-037 | Job card completed | Customer (via email) | Email | — |

#### Module: HR / Payroll

| Event ID | Trigger | Recipients | Channel | Escalation |
|---------|---------|-----------|---------|-----------|
| NE-040 | Payroll batch approved | All employees | Email (payslip PDF) | — |
| NE-041 | BEFTN file ready for bank submission | Payroll Officer + CFO | Email + in-app | — |
| NE-042 | Salary not credited (3 days after payroll run) | HR Manager + CFO | Email + in-app | — |
| NE-043 | Employee contract expiry in 30 days | HR Manager | Email + in-app | — |
| NE-044 | Leave request awaiting approval | Manager | Email + in-app | 48h: HR Manager |

#### Module: Inventory

| Event ID | Trigger | Recipients | Channel | Escalation |
|---------|---------|-----------|---------|-----------|
| NE-045 | Stock below reorder point | Inventory Manager + Purchase Officer | Email + in-app | — |
| NE-046 | Inter-branch transfer request awaiting approval | Destination branch Inventory Manager | Email + in-app | — |
| NE-047 | Expiry approaching (consumable batch within 60 days) | Inventory Manager | Email + in-app | — |

#### System / Security

| Event ID | Trigger | Recipients | Channel | Escalation |
|---------|---------|-----------|---------|-----------|
| NE-050 | Failed login (3 consecutive attempts) | System Administrator | Email + in-app | — |
| NE-051 | New user account created | New user (welcome) + IT Support | Email | — |
| NE-052 | Backup job failed | System Administrator | Email + SMS | — |
| NE-053 | Server disk usage > 80% | System Administrator | Email + in-app | >90%: SMS |
| NE-054 | Database replication lag > 5 min | System Administrator | SMS | — |
| NE-055 | Scheduled batch job failed | System Administrator + module owner | Email | — |
| NE-056 | API integration error (bKash / Nagad / NBR) | System Administrator + Integration Owner | Email | 3 consecutive: SMS to CFO |

### 2.3 Notification Template Standards

All notification emails must:
- Use SPSL letterhead and branding
- Include SPSL contact information for queries
- Be available in both English and Bangla
- Include direct link to the relevant record in the ERP
- Customer-facing notifications: signed from "Smart Printing Solution Ltd." with unsubscribe for marketing emails only (transactional notifications are mandatory)

### 2.4 Notification Configuration

Configurable settings per event:
- Enable/disable (only for non-mandatory events)
- Delay before trigger (e.g., send AR reminder at 9 AM, not midnight)
- Recipient override (add CC/BCC)

Mandatory events (cannot be disabled): NE-013, NE-014, NE-015, NE-021, NE-035, NE-052

---

## 3. Approval Workflow Framework

### 3.1 Global Approval Matrix

This matrix defines the minimum approval authority required for each transaction type and amount band. Individual module BRDs may specify stricter rules.

| Transaction Type | < BDT 50,000 | BDT 50K–500K | BDT 500K–5M | > BDT 5M |
|----------------|-------------|-------------|------------|---------|
| Sales Discount | Sales Rep (self-approve up to 5%) / Sales Manager (>5%) | Sales Manager | Sales Director | MD |
| Purchase Order | Dept Manager | Dept Head | CFO | MD |
| Manual Journal Entry | Accountant (prepared) + Finance Manager (approved) | Finance Manager | CFO | MD |
| Cash Advance | Branch Manager | Finance Manager | CFO | MD + Board approval |
| Petty Cash Disbursement | Branch Manager (self-approve up to limit) | Not applicable | Not applicable | Not applicable |
| Credit Note (Sales) | Sales Manager | Finance Manager | CFO | MD |
| Credit Note (MPS) | MPS Manager | Finance Manager | CFO | MD |
| Asset Write-off | Not allowed | Fixed Asset Manager + Finance Manager | CFO | MD |
| Bad Debt Write-off | Not allowed | Finance Manager | CFO | MD |
| Vendor Payment | Finance Manager (prepared) + CFO (approved) | CFO | CFO + MD | MD + Board |
| Inter-company Transaction | Not allowed | CFO | CFO | CFO + MD |
| LC Application | CFO | CFO | CFO + MD | MD + Board |
| Employee Loan | HR Manager | HR Manager + CFO | CFO | MD |
| Salary Revision | HR Manager | HR Manager + CFO | CFO | MD |

### 3.2 Approval Routing Rules

**AR-001 — Maker-Checker:**
The approver cannot be the same person as the preparer. This applies to all financial transactions without exception. System enforces: the "Approve" button is hidden for the creator of the record.

**AR-002 — Deputy Approver:**
Each approver role must have a pre-configured deputy in the system. If the primary approver has set an "Out of Office" flag, approvals auto-route to the deputy without timeout.

**AR-003 — Timeout Escalation:**
If an approval is not acted on within 48 business hours (i.e., 48 hours of Saturday–Thursday, 9 AM–6 PM):
1. System sends reminder notification to the approver
2. At 72 hours: system auto-escalates to the next level in the hierarchy
3. The original approver is notified of the escalation
4. Escalation is logged in the audit trail

**AR-004 — Approval Immutability:**
Once a transaction is approved, it cannot be edited. To correct an approved transaction:
1. Approver must reject and return to preparer with notes
2. Preparer corrects and resubmits
3. Full approval flow restarts
Exception: CFO may make corrections to posted journal entries with a mandatory correction reason and dual-custody requirement.

**AR-005 — Batch Approval:**
Module owners may approve up to 50 records in a single batch approval action. Batch approval is only permitted when records are of identical type and the approver has reviewed each record individually (confirmation dialog required).

**AR-006 — Approval Delegation:**
A user may formally delegate their approval authority to a deputy for a specified date range (leave, travel). Delegation must be recorded with start/end dates and approved by the System Administrator. Any approvals made under delegation are logged with the delegator's identity shown.

### 3.3 Approval Audit Requirements

Every approval action records:
- Approver identity
- Timestamp
- Action taken (approved / rejected / escalated)
- Comments (mandatory if rejected)
- IP address
- Record reference

This data feeds the audit trail (Section 4).

---

## 4. Audit Trail Specification

### 4.1 Scope of Audit Logging

**AT-001 — What is logged:**

| Category | Models Covered | Operations Logged |
|---------|---------------|------------------|
| Financial records | account.move, account.payment, account.move.line | Create, Write, Cancel, Delete-attempt |
| Contract records | mps.contract, purchase.lc, sale.order, purchase.order | Create, Write, State Change, Delete-attempt |
| Master data (sensitive) | res.partner (customer/vendor), hr.employee (salary fields), mps.device | Create, Write of sensitive fields |
| HR / Payroll | hr.payslip, hr.payslip.run, spsl.wppf.record | Create, Approve, Cancel |
| System / Security | res.users, res.groups | Create, Write, Delete |
| Cash management | spsl.cash.remittance, account.bank.statement | Create, Write, Validate |

**AT-002 — What is NOT logged:**
- Read operations on non-sensitive records (to avoid log bloat)
- Temporary draft records that are discarded without posting
- System-generated computed field updates (e.g., balance recalculation)

### 4.2 Audit Record Structure

Every audit log entry contains:

| Field | Description |
|-------|-------------|
| `log_id` | Auto-increment unique ID |
| `user_id` | User who performed the action |
| `timestamp` | UTC datetime of action |
| `ip_address` | Client IP address |
| `model_name` | Odoo model (e.g., `account.move`) |
| `record_id` | ID of the affected record |
| `record_display` | Human-readable reference (e.g., "INV/2026/04521") |
| `operation` | `create` / `write` / `state_change` / `delete_attempt` |
| `field_name` | Field changed (for write operations) |
| `old_value` | Value before change (serialized) |
| `new_value` | Value after change (serialized) |
| `session_id` | Browser session identifier |
| `source` | `ui` / `api` / `scheduled_action` / `import` |

### 4.3 Audit Log Access and Retention

**AT-003 — Access:**
- Read access: CFO, System Administrator, Auditor (Read-only) role
- Export (encrypted PDF): CFO and System Administrator only
- No role can modify or delete audit log entries
- Audit log tables use database-level INSERT-only permissions (no UPDATE, no DELETE via SQL)

**AT-004 — Retention:**
Minimum 7 years from transaction date (Bangladesh Companies Act 1994). After 7 years, records may be archived to cold storage but must remain retrievable within 48 hours for compliance requests.

**AT-005 — Tamper Evidence:**
Each audit log entry includes a cryptographic hash of its own fields. Any modification (including by DBAs) will invalidate the hash. Monthly hash verification report generated automatically.

### 4.4 Sensitive Field List (Always Audited)

- Salary fields: `x_basic_salary`, `x_hra`, payslip amounts
- Contract rates: `cpc_mono`, `cpc_color`, `base_monthly_fee`
- Customer credit limit: `x_credit_limit`
- User roles: `res.groups` membership
- Bank account details on vendors/employees
- Tax numbers (TIN, BIN)

---

## 5. Document Management

### 5.1 Mandatory Attachment Policy

Documents that must be attached before a record can be posted/confirmed:

| Transaction | Mandatory Attachment | Who Verifies |
|------------|---------------------|-------------|
| MPS Contract (active) | Signed contract scan | MPS Coordinator |
| Foreign PO (LC) | Proforma invoice from supplier | Purchase Officer |
| GRN (>BDT 100K) | Delivery challan / packing list | Inventory Manager |
| Vendor invoice (>BDT 100K) | Supplier invoice copy | Accountant |
| Cash advance (>BDT 10K) | Approval note | Finance Manager |
| Employee loan disbursement | Signed loan agreement | HR Manager |
| Asset acquisition | Purchase invoice | Fixed Asset Manager |
| Asset disposal | Board approval note (>BDT 500K) | CFO |

### 5.2 Document Naming Convention

Format: `[ENTITY_TYPE]-[REFERENCE_NUMBER]-[DESCRIPTION]-[DATE].ext`
Example: `MPS-CONTRACT-MPS-2026-00234-SIGNED-COPY-20260315.pdf`

### 5.3 Document Versioning

For contracts and agreements, versioning is required:
- Major version (v1, v2): substantive content changes
- Minor version (v1.1): corrections or addenda
- Superseded versions retained; current version flagged

### 5.4 Storage and Access

- Documents stored in Odoo filestore (or configured S3-compatible storage)
- Access controlled by the record's access rules (same as the parent record)
- CFO and Auditor roles can access all financial document attachments

---

## 6. Bangladesh Calendar and Date Handling

### 6.1 Working Week

| Day | Status |
|-----|--------|
| Saturday | Working day |
| Sunday | Working day |
| Monday | Working day |
| Tuesday | Working day |
| Wednesday | Working day |
| Thursday | Working day |
| Friday | **Weekly holiday** |

All SLA calculations, approval timeouts, and filing deadline calculations use the working week definition above.

### 6.2 Public Holiday Calendar

Managed in model `spsl.public.holiday`. Must be updated annually before the fiscal year starts.

**Standard Bangladesh public holidays included:**
- National holidays: Independence Day (March 26), Victory Day (December 16), National Mourning Day (August 15), Bangla New Year (April 14)
- Religious holidays: Eid-ul-Fitr (3 days), Eid-ul-Adha (3 days), Shab-e-Barat, Shab-e-Qadar, Durga Puja, Christmas
- Government-declared holidays (variable each year — loaded from annual circular)

System Administrator loads the holiday calendar by January 1 each calendar year.

### 6.3 Business Hours

Standard business hours for SLA calculation: **9:00 AM to 6:00 PM (Asia/Dhaka), Saturday–Thursday**

Government office hours (for NBR/BB deadline purposes): **9:00 AM to 5:00 PM, Saturday–Thursday**

### 6.4 Fiscal Year

Bangladesh fiscal year: **July 1 to June 30**

All financial period locks, budget years, and tax periods align to this fiscal year.

### 6.5 Date Display

- System stores dates in ISO format (YYYY-MM-DD) and timestamps in UTC
- All UI displays: DD-MMM-YYYY format (e.g., 15-Mar-2026)
- Bangla calendar display: available as optional display field on reports; not used for calculations
- Invoice dates on customer documents: DD Month YYYY in English; DD মাস YYYY in Bangla

---

## 7. Multi-Branch Data Access Control

### 7.1 Default Data Isolation Rules

**Rule 7.1.1:** All records that have a `branch_id` field are filtered by the user's assigned branch by default. A user assigned to Chattagram branch cannot see Dhaka branch records in list views.

**Rule 7.1.2:** The following roles have implicit all-branch access:
- Managing Director
- CFO
- Finance Manager
- Sales Director
- Operations Manager
- MPS Manager
- HR Manager
- System Administrator
- Auditor (Read-only)
- BI Analyst

**Rule 7.1.3:** Branch Managers have full read access to their own branch and read-only access to their branch's data in consolidated reports.

**Rule 7.1.4:** All other roles (Accountant Branch, Sales Rep, Field Engineer, etc.) see only records for their assigned branch. If a user is assigned to multiple branches (configurable), they see records for all assigned branches.

### 7.2 Branch Context Switching

For users with multi-branch access:
- A "Current Branch" selector is displayed in the top navigation bar
- When a branch is selected, all new records are created in that branch context
- "All Branches" option shows consolidated view (no new record creation in this mode)
- The selected branch context is recorded in the user's session

### 7.3 HQ Override Capability

Finance Manager and above can view all branch records. To edit a branch record (e.g., correct an error in Chattagram's books), Finance Manager must explicitly select that branch context and log a reason. This action is audit-logged.

---

## 8. Mobile Financial Services (bKash / Nagad) Integration

### 8.1 Integration Purpose

- Customer portal: online payment of invoices via bKash / Nagad
- HR Payroll: salary disbursement to field staff via bKash / Nagad (MFS disbursement file)
- Reconciliation: automatic matching of payment notifications to AR invoices

### 8.2 bKash Payment Integration Sequence

```
Customer initiates payment on SPSL portal
    → Portal calls bKash Payment Gateway API (createPayment)
    → bKash returns PaymentID
    → Customer completes payment on bKash (OTP confirmation)
    → bKash sends payment confirmation webhook to SPSL portal
    → SPSL system validates webhook signature (HMAC)
    → System records payment in Odoo (account.payment)
    → Invoice marked as paid / partially paid
    → Customer receives payment confirmation email
    → Daily: bKash settlement report reconciled against Odoo payments
```

### 8.3 Nagad Payment Integration

Same sequence as bKash using Nagad's merchant API. Separate merchant account and API keys required.

### 8.4 Failure Handling

- If webhook not received within 10 minutes of payment: system queries bKash/Nagad API to check status
- Retry logic: 3 retries with exponential backoff (2m, 4m, 8m)
- After 3 failures: alert sent to System Administrator + Finance Manager
- Manual reconciliation workflow available as fallback

### 8.5 MFS Salary Disbursement

For employees with `x_salary_payment_method = 'mfs'`:
1. Payroll run generates MFS disbursement file (CSV format: employee_name, mfs_type, wallet_number, amount)
2. File submitted to bKash/Nagad merchant portal
3. Disbursement confirmation file reconciled against payroll records
4. Employees receive SMS from bKash/Nagad confirming salary credit

### 8.6 Security Requirements for MFS Integration

- API keys stored in encrypted Odoo system parameters (not in source code)
- All bKash/Nagad callbacks validated with HMAC signature
- MFS disbursement files encrypted before transmission
- Transaction logs retained for 7 years

---

## 9. Performance Requirements (Cross-Module)

These benchmarks apply to the production system post-go-live with 100+ concurrent users.

| Benchmark ID | Operation | Target | Measurement Method |
|-------------|-----------|--------|-------------------|
| PERF-001 | Single invoice generation (any type) | < 3 seconds | Browser timer, P95 |
| PERF-002 | MPS batch billing run (800 contracts) | < 30 minutes | Scheduled action log |
| PERF-003 | Any dashboard load (initial) | < 5 seconds | Browser timer, P95 |
| PERF-004 | Any list view load (default filter) | < 2 seconds | Browser timer, P95 |
| PERF-005 | Any search result (single field) | < 2 seconds | Browser timer, P95 |
| PERF-006 | Report generation (< 10,000 rows) | < 10 seconds | Server-side timer |
| PERF-007 | Report generation (10,000–100,000 rows) | < 60 seconds | Server-side timer |
| PERF-008 | Data import (1,000 records) | < 2 minutes | Import job log |
| PERF-009 | PWA job queue load (Field Engineer) | < 3 seconds on 4G | Mobile browser timer |
| PERF-010 | Payroll batch run (500 employees) | < 15 minutes | Scheduled action log |
| PERF-011 | GL consolidation (9 branches, 1 month) | < 2 minutes | Server-side timer |
| PERF-012 | Database backup completion | < 1 hour | Backup log |

**Load Profile:**
- Peak concurrent users: 120 (20% headroom above 100 target)
- Peak load timing: 1st–7th of each month (MPS invoicing period)
- Geographical distribution: 10 locations (9 branches + 1 customer portal)

**Performance Testing Requirement:**
Vendor must conduct load testing at 120 concurrent users simulating the monthly billing scenario before UAT sign-off. Test results must be provided to SPSL.

---

## 10. Data Privacy and Security

### 10.1 Personal Identifiable Information (PII) Classification

| Data Category | Examples | Protection Level |
|-------------|---------|----------------|
| PII — Employee | NID, salary, bank account, TIN, medical records | Encrypted at rest; field-level RBAC |
| PII — Customer | Contact details, NID, BIN | Encrypted at rest for NID/BIN |
| Financial — Sensitive | CPC rates, credit limits, payroll amounts | Field-level RBAC; audit-logged |
| Business Confidential | Contract terms, pricing, supplier terms | Access restricted to relevant roles |

### 10.2 Encryption Requirements

- Database encryption: PostgreSQL Transparent Data Encryption (TDE) or filesystem-level encryption (LUKS on Linux)
- Sensitive fields (NID, bank account numbers, API keys): application-level encryption using Fernet/AES-256
- Data in transit: TLS 1.2 minimum (TLS 1.3 preferred) for all connections
- Backup files: AES-256 encryption before offsite transfer

### 10.3 Field-Level Security

| Field | Roles that can read | Roles that can write |
|-------|--------------------|--------------------|
| Employee salary (`x_basic_salary`) | HR Manager, Payroll Officer, CFO, MD, Auditor | HR Manager, CFO |
| Customer credit limit | Sales Manager+, Finance+, MPS Manager+ | Finance Manager, CFO |
| MPS CPC rates | MPS Manager, Finance Manager, CFO, MD, Auditor | MPS Manager, CFO |
| Vendor bank account | Finance Manager, Payroll Officer, CFO, SysAdmin | Finance Manager, CFO |
| Audit log | CFO, SysAdmin, Auditor | None (read-only) |

### 10.4 Session Security

- Session timeout: 30 minutes inactivity
- Warning at 25 minutes (pop-up: "Your session will expire in 5 minutes")
- After timeout: redirect to login; form state preserved for 10 minutes (user can resume after re-login)
- Concurrent sessions: maximum 3 per user (configurable)
- Session invalidation on password change: all existing sessions terminated

### 10.5 Password Policy

- Minimum length: 10 characters
- Complexity: minimum 1 uppercase, 1 lowercase, 1 digit, 1 special character
- Rotation: every 90 days
- History: last 5 passwords cannot be reused
- Lockout: 5 consecutive failed attempts → account locked for 15 minutes → System Admin reset required after 3 lockouts

### 10.6 Network Security

- All external access via HTTPS (HTTP redirects to HTTPS)
- Admin panel (`/web/settings`): accessible only from SPSL internal network or VPN
- IP whitelisting for System Administrator login (configurable)
- Rate limiting on login endpoint: 10 attempts per minute per IP

---

## 11. Error Handling Standards

### 11.1 User-Facing Validation Errors

- Displayed inline, immediately below the offending field
- Clear, actionable message in English (Bangla translation for customer-facing portal)
- Never display technical error codes to end users
- Mandatory fields: "This field is required"
- Format errors: "Please enter a valid [field type] (e.g., [example])"
- Business rule violations: descriptive message referencing the rule (e.g., "Payment cannot exceed the invoice outstanding balance of BDT 45,000")

### 11.2 System Error Handling

- System errors (500-level): logged to Odoo error log with full traceback
- User sees: "An unexpected error occurred. Your work has been saved. Please try again or contact IT Support (Ref: [error_code])."
- System Administrator receives notification NE-055 (batch) or email (interactive error > 3 occurrences within 5 minutes)

### 11.3 Batch Job Failure Handling

- All batch jobs (payroll, MPS billing, scheduled reports) run within a transaction
- On failure: **full rollback** — no partial records
- Failure notification sent to System Administrator + module owner (NE-055)
- Failed job log: timestamp, job name, records processed, failure point, error message
- Re-run capability: System Administrator can re-trigger failed batch from the last successful checkpoint

### 11.4 Integration Failure Handling

For external integrations (bKash, Nagad, NBR e-filing, BEFTN):
1. Attempt 1: immediate
2. Attempt 2: 2 minutes later
3. Attempt 3: 8 minutes later
4. After 3 failures: alert NE-056 (email) to System Administrator + Finance Manager / Integration Owner
5. Manual processing fallback activated; operations staff notified

### 11.5 Data Import Error Handling

- Bulk import: records with errors are rejected; valid records proceed
- Error report: downloadable CSV listing rejected rows with specific error per row
- Re-import of failed rows is supported after correction
- No partial row import (each row either fully imported or fully rejected)

---

## 12. Integration Architecture Overview

### 12.1 External System Integrations

| System | Direction | Method | Priority |
|--------|---------|--------|---------|
| Bangladesh Bank Nikash-BEFTN | Outbound (payroll file) | File upload (CSV/TXT format per BB spec) | High |
| bKash Payment Gateway | Bidirectional | REST API (OAuth 2.0) | Medium |
| Nagad Payment Gateway | Bidirectional | REST API (OAuth 2.0) | Medium |
| NBR etaxnbr.gov.bd (VAT filing) | Outbound | File export (NBR XML/CSV format) | High |
| SMS Gateway (Bangladesh) | Outbound | REST API | High |
| Email (SMTP) | Outbound | SMTP (TLS) | Critical |
| Google Maps | Outbound | Maps Embed / Directions API | Medium (Engineer PWA) |
| IoT Meter Reader (future) | Inbound | REST API (designed; not Phase 1) | Future |

### 12.2 Internal Integration Points

| Source Module | Target Module | Data Flow |
|-------------|-------------|---------|
| MPS click.record | account.move | Auto-create invoice |
| sale.order | account.move | Invoice from order |
| purchase.order | stock.picking + account.move | GRN + vendor bill |
| hr.payslip | account.move | Salary journal entry |
| stock.inventory | account.move | Inventory adjustment journal |
| field.service.ticket | stock.move | Parts consumption |
| account.move (payment) | bKash/Nagad API | Payment confirmation |

### 12.3 API Documentation Requirement

Vendor must provide a REST API reference document (Swagger/OpenAPI format) for all custom endpoints created during implementation. This enables future integrations (mobile apps, third-party tools) without requiring vendor involvement.

---

## 13. System Monitoring and Alerting

### 13.1 Health Check Endpoints

The system must expose:
- `/health` — HTTP 200 if system is up
- `/health/db` — HTTP 200 if database connection is healthy
- `/health/redis` — HTTP 200 if session cache is healthy

These endpoints are used by monitoring tools and load balancers.

### 13.2 Monitoring Dashboard (IT Admin)

| Metric | Alert Threshold | Channel |
|--------|---------------|---------|
| Server CPU usage | > 80% for 5 min | SMS to SysAdmin |
| Server RAM usage | > 85% | Email to SysAdmin |
| Disk usage | > 80% | Email; > 90% → SMS |
| Database response time | > 2 seconds average | Email to SysAdmin |
| Failed login attempts | > 10 per hour | SMS to SysAdmin |
| Backup last completed | > 25 hours ago | SMS to SysAdmin |
| Odoo worker queue length | > 100 pending jobs | Email to SysAdmin |

### 13.3 Uptime Target

System availability: ≥ 99.5% measured monthly (excludes planned maintenance windows)
Planned maintenance window: Friday 10 PM – 2 AM BDT (monthly)
Maintenance notification: at least 5 days in advance via in-app notice to all users

---

## 14. Sign-off Matrix

| Role | Name | Date | Signature |
|------|------|------|-----------|
| SPSL CFO | — | — | _____________ |
| SPSL IT Administrator | — | — | _____________ |
| SPSL MPS Manager | — | — | _____________ |
| SPSL Operations Manager | — | — | _____________ |
| Vendor Project Manager | — | — | _____________ |
| Vendor Technical Lead | — | — | _____________ |
| SPSL Project Manager | — | — | _____________ |

---

*Document end — BRD_12 Cross-Cutting Concerns v1.0*
*Project ELEVATE | Smart Printing Solution Ltd. | Strictly Confidential*
