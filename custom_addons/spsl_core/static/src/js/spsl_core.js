/** @odoo-module **/

/**
 * Copyright 2026 SPSL - Smart Printing Service Limited
 * License LGPL-3
 *
 * SPSL Core JavaScript Module
 */

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Field } from "@web/views/fields/field";

// ---------------------------------------------------------------------------
// ApprovalStatusBadge — field widget for approval_state
// ---------------------------------------------------------------------------
// Usage in XML:  <field name="approval_state" widget="approval_status_badge"/>
// Reads approval_state from the record and renders a coloured badge.
// When the state is 'approved' or 'rejected' it also displays the
// approver/rejecter name and date from sibling fields.
// ---------------------------------------------------------------------------

export class ApprovalStatusBadge extends Field {
    static template = "spsl_core.ApprovalStatusBadge";

    get badgeClass() {
        const colourMap = {
            draft: "spsl-badge-draft",
            pending: "spsl-badge-pending",
            approved: "spsl-badge-approved",
            rejected: "spsl-badge-rejected",
        };
        return colourMap[this.props.value] || "spsl-badge-draft";
    }

    get stateLabel() {
        const labels = {
            draft: "Draft",
            pending: "Pending Approval",
            approved: "Approved",
            rejected: "Rejected",
        };
        return labels[this.props.value] || this.props.value;
    }

    get showMeta() {
        return this.props.value === "approved" || this.props.value === "rejected";
    }

    get metaUser() {
        if (this.props.value === "approved") {
            return this.props.record.data.approved_by
                ? this.props.record.data.approved_by[1]
                : "";
        }
        if (this.props.value === "rejected") {
            return this.props.record.data.rejected_by
                ? this.props.record.data.rejected_by[1]
                : "";
        }
        return "";
    }

    get metaDate() {
        if (this.props.value === "approved") {
            return this.props.record.data.approved_date || "";
        }
        if (this.props.value === "rejected") {
            return this.props.record.data.rejected_date || "";
        }
        return "";
    }
}

ApprovalStatusBadge.props = {
    ...standardFieldProps,
    value: { type: String, optional: true },
};

ApprovalStatusBadge.displayName = "ApprovalStatusBadge";
ApprovalStatusBadge.supportedTypes = ["selection"];

registry.category("fields").add("approval_status_badge", ApprovalStatusBadge);
