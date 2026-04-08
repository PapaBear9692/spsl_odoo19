/** @odoo-module **/

/**
 * Copyright 2026 SPSL - Smart Printing Service Limited
 * License OPL-1
 *
 * SPSL Core JavaScript Module
 * Provides frontend utilities and components for the SPSL Core module
 */

import { Component, useState, useRef } from "@odoo/owl";

class ApprovalWidget extends Component {
    static template = "spsl_core.approval_badge";
    static props = {
        state: { type: String },
        request_id: { type: Number, optional: true },
    };

    setup() {
        this.state = this.props.state;
    }
}

class NotificationBadge extends Component {
    static template = "spsl_core.notification_badge";
    static props = {
        has_unread: { type: Boolean },
        count: { type: Number, optional: true },
    };

    setup() {
        this.has_unread = this.props.has_unread;
        this.count = this.props.count || 0;
    }
}

class ApprovalStatusCard extends Component {
    static template = "spsl_core.approval_status_card";
    static props = {
        state: { type: String },
        request_id: { type: Number, optional: true },
    };

    setup() {
        this.state = this.props.state;
        this.request_id = this.props.request_id;
    }
}

registry.category("view_widgets").add("approval_widget", ApprovalWidget);
registry.category("view_widgets").add("notification_badge", NotificationBadge);
registry.category("view_widgets").add("approval_status_card", ApprovalStatusCard);
