# Copyright 2020 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Website Membership Registration",
    "category": "Website",
    "version": "16.0.1.0.0",
    "author": "Onestein",
    "license": "AGPL-3",
    "website": "https://www.onestein.nl",
    "depends": [
        "mass_mailing_membership_section",
        "membership_extension",
        "membership_hr",
        "membership_hr_recruitment",
        "membership_origin",
        "membership_section",
        "portal",
        "website",
        "website_membership_section",
        "website_partner",
        "website_sale",
    ],
    "data": [
        "data/ir_cron_data.xml",
        "data/mail_template_data.xml",
        "views/hr_applicant_view.xml",
        "views/hr_employee_view.xml",
        "views/membership_section_view.xml",
        "views/product_template_view.xml",
        "views/res_config_settings_view.xml",
        "views/res_partner_view.xml",
        "templates/website.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_membership_registration/static/src/js/website_membership_registration.js",
            "website_membership_registration/static/src/scss/website_membership_registration.scss",
        ],
    },
    "demo": [
        "data/product_demo.xml",
        "data/res_partner_demo.xml",
        "data/website_demo.xml",
    ],
}
