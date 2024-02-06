Frontend
********

This module adds a form to the website allowing the user to create applications them selves.
It creates a sale order, payment link (for the user). After that `argocd_sale` will
take care of the rest

User can use the portal `/my/home` to see their applications and their health (simple health check)

Technical considerations
************************

For deep insight of application status use the argocd interface or kubectl.

TODO
****

* Use pricelist etc for the price
* Better external links
* Move reseller part of product.product to something more generic seems a bit out of place here
