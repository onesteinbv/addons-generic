{
    "name": "LibreCaptcha",
    "summary": "Base module for LibreCaptcha",
    "author": "Onestein",
    "website": "https://www.onestein.nl",
    "category": "Tools",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["base", "portal"],
    "external_dependencies": {"python": ["requests"]},
    "data": ["data/ir_config_parameters_data.xml", "templates/captcha.xml"],
    "assets": {"web.assets_frontend": ["base_librecaptcha/static/src/js/captcha.js"]},
}
