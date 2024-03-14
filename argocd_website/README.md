# ArgoCD Frontend

This module adds a form to the website allowing the user to create applications themselves.
It creates a subscription and a payment link to the first invoice. After that `argocd_sale` will
take care of the rest.

User can use the portal `/my/home` to see their applications and their health (simple health check)

## Configuration

1. Create a subscription template
2. Configure the `argocd_website.subscription_template_id` with the id of the created subscription template.
   This template is used for creating new subscriptions from the website.

   **Make sure invoicing mode is on Invoice & send and duration is on forever**

## Technical considerations

For deep insight of application status use the argocd interface or kubectl.

## TODO

* Use pricelist etc for the price
* Move reseller part of product.product to something more generic seems a bit out of place here
