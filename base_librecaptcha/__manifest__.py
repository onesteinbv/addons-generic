{
    "name": "LibreCaptcha",
    "summary": "Base module for LibreCaptcha",
    "author": "Onestein",
    "website": "https://onestein.nl",
    "category": "Tools",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["base", "portal"],
    "external_dependencies": {"python": ["requests"]},
    "data": [
        "data/ir_cron_data.xml",
        "templates/captcha.xml",
        "templates/auth_signup_login_templates.xml",
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "web.assets_frontend": ["base_librecaptcha/static/src/js/captcha.esm.js"]
    },
}
