from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """
    Migrate application.domain.scope to use new model argocd.application.domain.scope
    Get all existing domains with the old scope field, and create argocd.application.domain.scope
    """
    cr.execute(
        """
        SELECT DISTINCT scope FROM argocd_application_domain
        WHERE scope IS NOT NULL AND scope != ''
    """
    )
    scopes = cr.fetchall()
    env = api.Environment(cr, SUPERUSER_ID, {})
    domain_scope_model = env["argocd.application.domain.scope"]
    for (scope_name,) in scopes:
        domain_scope_model.create({"name": scope_name})

    cr.execute(
        """
        UPDATE argocd_application_domain SET scope_id = scope.id
        FROM argocd_application_domain_scope AS scope WHERE scope.name = argocd_application_domain.scope
    """
    )
