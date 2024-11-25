# Copyright 2024 Onestein
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Currency Rate Update Mapping",
    "version": "16.0.1.0.0",
    "author": "Onestein BV",
    "website": "https://www.onestein.nl",
    "license": "AGPL-3",
    "category": "Financial Management/Configuration",
    "summary": "Allows to add mappings for currency rate providers",
    "depends": ["currency_rate_update"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_currency.xml",
    ],
    "installable": True,
}
