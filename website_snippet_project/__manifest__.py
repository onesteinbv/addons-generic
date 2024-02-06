{
    "name": "Project List Snippet",
    "summary": "A website snippet that lists published website projects.",
    "category": "Website",
    "version": "16.0.1.0.0",
    "author": "Onestein",
    "website": "https://www.onestein.nl",
    "license": "AGPL-3",
    "depends": [
        "website_project",
    ],
    "data": [
        "views/snippets/s_dynamic_project_list_templates.xml",
        "views/snippets/s_dynamic_project_list.xml",
        "views/snippets/options.xml",
        "data/ir_actions_server.xml",
        "data/ir_filters.xml",
        "data/website_snippet_filter.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "/website_snippet_project/static/src/snippets/s_project_list/000.esm.js",
            "/website_snippet_project/static/src/snippets/s_project_list/000.scss",
        ],
        "web_editor.assets_wysiwyg": [
            "/website_snippet_project/static/src/snippets/s_project_list/options.esm.js",
        ],
    },
}
