def migrate(cr, version):
    """Rename argocd_name to argocd_value in product.attribute.value"""

    cr.execute(
        """
        ALTER TABLE product_attribute_value
        ADD COLUMN argocd_value VARCHAR
    """
    )

    cr.execute(
        """
        UPDATE product_attribute_value
        SET argocd_value = argocd_name
    """
    )
