{
    "name": "Deutschland SKR49 - Accounting",
    "version": "16.0.1.0.0",
    "author": "humanilog",
    "website": "https://www.onestein.nl",
    "category": "Localization",
    "description": """
Dieses Modul beinhaltet einen deutschen Kontenrahmen basierend auf dem SKR49.
=========================================================================================

German accounting chart and localization for the SKR49.
  """,
    "depends": ["l10n_de"],
    "license": "LGPL-3",
    "data": [
        "data/account_data.xml",
        "data/account_account_tags_data.xml",
        "data/l10n_de_skr49_chart_data.xml",
        "data/account_chart.xml",
        "data/account_tax_fiscal_position.xml",
        "data/account_chart_template_data.xml",
    ],
    "installable": True,
    "auto_install": True,
}
