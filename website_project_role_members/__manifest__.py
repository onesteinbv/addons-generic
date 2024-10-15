{
    "name": "Website Project Role Members",
    "summary": "Website Project Role Members",
    "category": "Website",
    "version": "16.0.1.0.0",
    "author": "Onestein",
    "website": "https://www.onestein.nl",
    "license": "AGPL-3",
    "depends": [
        "project",
        "project_role",
        "project_role_members",
        "website",
        "website_membership",
        "website_project",
    ],
    "data": [
        "templates/project_project_template.xml",
        "templates/portal_template.xml",
        "views/res_partner_view.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "/website_project_role_members/static/src/css/website_project.css",
        ],
    },
}
