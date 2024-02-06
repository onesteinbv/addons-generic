# Copyright 2017-2023 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Auto Create Fiscal Periods",
    "summary": "Auto Create Fiscal Periods",
    "author": "Onestein",
    "website": "https://www.onestein.nl",
    "category": "Tools",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "date_range",
    ],
    "data": [
        "data/date_range_type.xml",
        "data/date_range_cron.xml",
        "views/date_range_type.xml",
    ],
    "installable": True,
}
