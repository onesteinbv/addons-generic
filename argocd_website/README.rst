Frontend
********

This module adds a form to the website allowing the user to create applications them selves.
It creates a sale order, payment link (for the user). After that `argocd_sale` will
take care of the rest

User can use the portal `/my/home` to see their applications and their health (simple health check)

`/my/applications/1/domain-names` allows users to configure custom domain names for their application, but in fact it
just creates argocd.application.value_ids with a formatted key like this: `domain_%(tag_key)`. Which then can be used
the rendering of the yaml.

Technical considerations
************************

For deep insight of application status use the argocd interface or kubectl.

TODO
****

* Use pricelist etc for the price
* Better external links
* Move reseller part of product.product to something more generic seems a bit out of place here
* Make the string format (for the key field) used in custom domain name configuration configurable.
  Currently it's hardcoded as "domain_%(tag_key)"