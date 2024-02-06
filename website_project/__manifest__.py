{
    "name": "Website Project",
    "summary": "Website Project",
    "category": "Website",
    "version": "16.0.1.0.1",
    "author": "Onestein",
    "website": "https://www.onestein.nl",
    "license": "AGPL-3",
    "depends": [
        "project",
        "website",
    ],
    "data": [
        "security/ir.model.access.csv",
        "templates/project_project_template.xml",
        "views/project_project.xml",
        "views/project_project_category.xml",
        "menuitems.xml",
    ],
    "demo": [
        "data/project_category_demo.xml",
        "data/project_project_demo.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "/website_project/static/src/css/website_project.css",
        ],
    },
}
