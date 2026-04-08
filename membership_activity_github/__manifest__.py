{
    "name": "Membership Github Activity",
    "category": "Membership",
    "version": "18.0.1.0.0",
    "author": "Onestein",
    "website": "https://www.onestein.nl",
    "license": "AGPL-3",
    "depends": ["membership_activity", "membership_activity_cde", "queue_job"],
    "external_dependencies": {"python": ["PyGithub==1.59.0"]},
    "data": [
        "data/ir_cron_data.xml",
        "data/ir_config_parameter_data.xml",
        "data/queue_job_function_data.xml",
        "views/project_view.xml",
    ],
}
