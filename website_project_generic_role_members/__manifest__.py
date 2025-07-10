{
    "name": "Website Project Generic Role Members",
    "summary": "Website Project Generic Role Members",
    "category": "Website",
    "version": "18.0.1.0.0",
    "author": "Onestein",
    "website": "https://www.onestein.nl",
    "license": "AGPL-3",
    "depends": [
        "project",
        "project_role",
        "project_role_members",
        "website",
        "website_membership",
        "website_project_generic",
    ],
    "data": [
        "templates/portal_template.xml",
        "templates/project_project_template.xml",
        "views/res_partner_view.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "/website_project_generic_role_members/static/src/css/website_project_generic_role_members.css",
        ],
    },
}
