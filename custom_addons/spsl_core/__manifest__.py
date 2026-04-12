# Copyright 2026 SPSL - Smart Printing Service Limited
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html)

{
    "name": "SPSL Core",
    "version": "19.0.1.0.0",
    "category": "SPSL",
    "summary": "Core shared services for all SPSL custom modules",
    "author": "Unisoft Solutions",
    "website": "https://spslbd.com",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mail",
        # "operating_unit",  # TODO: Install from OCA when available
    ],
    "data": [
        # Security
        "security/spsl_core_groups.xml",
        "security/ir.model.access.csv",
        "security/approval_rules.xml",
        "security/audit_rules.xml",
        # Data
        "data/sequence_data.xml",
        "data/mail_template_data.xml",
        "data/approval_rules_data.xml",
        "data/cron_data.xml",
        "data/audit_config_data.xml",
        "data/system_params_data.xml",
        "data/notification_channel_data.xml",
        "data/notification_template_data.xml",
        "data/notification_events_01.xml",
        "data/notification_events_02.xml",
        "data/notification_events_03.xml",
        "data/notification_qweb_templates.xml",
        "data/test_notification_dispatch.xml",
        # Views
        "views/approval_views.xml",
        "views/approval_queue_views.xml",
        "views/audit_config_views.xml",
        "views/audit_log_views.xml",
        "views/audit_chain_verify_views.xml",
        "views/notification_log_views.xml",
        "views/notification_template_views.xml",
        # Test Views (remove in production)
        # "views/test_views.xml",
    ],
    "demo": [],
    "assets": {
        "web.assets_backend": [
            "spsl_core/static/src/js/spsl_core.js",
            "spsl_core/static/src/css/spsl_core.css",
            "spsl_core/static/src/xml/spsl_core.xml",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}
