{
    "name": "Membership Github Activity",
    "category": "Membership",
    "version": "16.0.1.0.0",
    "author": "Onestein",
    "website": "https://www.onestein.nl",
    "license": "AGPL-3",
    "depends": ["membership_activity", "membership_activity_cde", "queue_job"],
    "external_dependencies": {"python": ["github"]},
    "data": [
        "data/ir_cron_data.xml",
        "data/ir_config_parameter_data.xml",
        "views/project_view.xml",
        "views/res_partner_view.xml",
    ],
}
