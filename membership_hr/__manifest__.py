# Copyright 2020 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Membership HR",
    "category": "Membership",
    "version": "16.0.1.0.0",
    "author": "Onestein",
    "license": "AGPL-3",
    "website": "https://www.onestein.nl",
    "depends": [
        "membership",
        "membership_section",
        "hr",
    ],
    "data": [
        "views/hr_employee_view.xml",
        "views/hr_department.xml",
        "views/membership_section.xml",
    ],
    "demo": [
        "data/hr_department_demo.xml",
        "data/hr_job_demo.xml",
        "data/res_users_demo.xml",
        "data/hr_employee_demo.xml",
    ],
}
