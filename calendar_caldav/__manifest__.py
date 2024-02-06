{
    "name": "CalDAV",
    "summary": "Synchronize your CalDAV calendar with Odoo",
    "version": "16.0.1.0.0",
    "category": "Productivity/Calendar",
    "license": "AGPL-3",
    "author": "Onestein",
    "website": "https://www.onestein.nl",
    "depends": [
        "calendar",
        "queue_job",
        "multi_step_wizard",
        "calendar_monthly_multi",
        "base_sparse_field",
    ],
    "external_dependencies": {"python": ["caldav"]},
    "data": [
        "data/ir_cron_data.xml",
        "security/ir_model_access.xml",
        "security/ir_rule.xml",
        "views/calendar_event_view.xml",
        "wizards/calendar_caldav_sync_wizard_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "calendar_caldav/static/src/views/**/*",
        ]
    },
}
