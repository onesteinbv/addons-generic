def migrate(cr, version):
    # Create namespace_prefix column in application_set
    cr.execute(
        """
        ALTER TABLE argocd_application_set
        ADD COLUMN namespace_prefix VARCHAR
    """
    )

    cr.execute(
        """
        UPDATE argocd_application_set
        SET namespace_prefix = prefix.name
        FROM argocd_application_namespace_prefix AS prefix
        WHERE prefix.id = argocd_application_set.namespace_prefix_id
    """
    )
