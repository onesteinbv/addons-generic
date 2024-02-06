# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Import Debrand",
    "summary": "Debrands import module (base_import)",
    "author": "Onestein",
    "license": "AGPL-3",
    "website": "https://www.onestein.nl",
    "category": "Technical Settings",
    "version": "16.0.1.0.0",
    "depends": ["base_import"],
    "assets": {
        "web.assets_backend": [
            "base_import_debranding/static/src/xml/*.xml",
        ],
    },
    "installable": True,
}
