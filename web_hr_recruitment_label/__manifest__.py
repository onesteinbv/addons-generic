# Copyright 2017-2023 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Website HR recruitment labels",
    "summary": "Adds the option to filter/display job labels on the website",
    "author": "Onestein",
    "website": "https://www.onestein.nl",
    "category": "Human Resources/Recruitment",
    "version": "16.0.1.0.15",
    "license": "AGPL-3",
    "depends": ["hr_recruitment_label", "website_hr_recruitment"],
    "data": [
        "views/hr_job_label_category_views.xml",
        "views/website_hr_recruitment_label_templates.xml",
        "views/snippets.xml",
    ],
    "demo": [
        "data/web_hr_recruitment_label.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "/web_hr_recruitment_label/static/src/js/job_filter.js",
            "/web_hr_recruitment_label/static/src/css/style.css",
        ]
    },
}
