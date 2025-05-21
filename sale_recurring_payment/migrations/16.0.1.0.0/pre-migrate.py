def migrate(cr, installed_version):
    # Move field is_revoked from sale_subscription to payment_provider_mandate
    cr.execute(
        """
        ALTER TABLE payment_provider_mandate
        ADD COLUMN IF NOT EXISTS is_revoked bool DEFAULT false;
        """
    )
    cr.execute(
        """
        UPDATE payment_provider_mandate
        SET is_revoked = sale_subscription.is_payment_provider_mandate_terminated
        FROM sale_subscription
        WHERE sale_subscription.payment_provider_mandate_id = payment_provider_mandate.id;
        """
    )
