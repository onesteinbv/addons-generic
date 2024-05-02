# Copyright 2017-2023 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Disable Scheduled Actions",
    "summary": "In certain cases, for example when running multiple "
    "instances of Odoo on a single database, responsibility "
    "for handling crons should lie with a single instance. "
    "This module disables automatic handling of crons "
    "by installing this module as a server-wide module. "
    "It's still possible to execute the crons manually."
    "Must be declared as a server-wide module.",
    "author": "Onestein",
    "website": "https://www.onestein.nl",
    "category": "Tools",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "base",
    ],
    "installable": True,
}
