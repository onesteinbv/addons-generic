{
    "name": "ArgoCD Deployer Application Set Management",
    "author": "Onestein",
    "website": "https://onestein.nl",
    "license": "AGPL-3",
    "category": "Tools",
    "version": "18.0.1.0.0",
    "summary": "Manage ArgoCD Application Set deployments from Odoo",
    "data": [
        "data/application_set_template.xml",
        "views/application_set_template_view.xml",
        "views/application_set_view.xml",
        "security/ir.model.access.csv",
        "menuitems.xml",
    ],
    "demo": [
        "demo/application_set_demo.xml",
    ],
    "depends": ["argocd_deployer"],
    "installable": False,  # There's no real use case for now. And refactoring will take time
}
