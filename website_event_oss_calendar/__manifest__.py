{
    "name": "Events: generic & open source calendar options",
    "version": "18.0.1.0.0",
    "category": "Events",
    "summary": "Add generic and open source calendar options to events (alongside the branded ones)",
    "depends": [
        "website_event",
    ],
    "data": [
        "templates/website_event_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_event_oss_calendar/static/src/scss/website.scss",
        ],
    },
    "auto_install": True,
}
