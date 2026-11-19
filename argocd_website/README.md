# ArgoCD Frontend

## Set up resellers

Follow the instructions in the ArgoCD Sales Management module to set up resellers and
reseller products. This module relies on the reseller and product configuration.

## Configure products

Products must be linked to an ArgoCD Application Template and Sales (`sale_ok`) must be
enabled to make them visible on the website.

## Usage

`/application/order` route accepts a `product_id` query parameter to preselect a product
on the order page. This allows you to link directly to the order page for a specific
product from the website or other marketing materials. If an product is preselected it
will show the configured optional products as well to allow customers to easily add them
to their order. If no product is preselected, the customer can select any product that
is configured for the website and has an application template assigned.

The customer or visitor order on the website is a draft subscription (similar to the
eCommerce flow) that allows them to select products and configure their order before
confirming it. If the customer is not logged in, they will be prompted to log in or
create an account before confirming their order. Once the customer is logged in, the
subscription is linked to their account. A reseller can also create a subscription on
behalf of an end customer.

When the customer confirms their order, they are sent to the payment form. The
subscription is locked while the initial payment is in progress. The first invoice is
created only after the payment transaction succeeds, at which point the subscription
starts and the application is deployed. The customer can then manage their subscription
and application from their account portal.

## Remove abandoned orders (subscription)

To prevent abandoned orders from being left indefinitely, a scheduled action runs daily
to check for draft subscriptions and subscriptions with an unpaid initial payment that
are older than the configured period (14 days by default). These subscriptions and their
associated payment transactions are deleted. The period can be configured via the
`argocd_website.subscription_abandoned_period` system parameter.

# Roadmap

- Allow resellers to select exising customers when confirming an order on the website.
  This would allow resellers to place orders on behalf of existing customers and makes
  an end customer optional (resellers can manage their own applications and of their
  customers). This would also prevent multiple partners to be created for the same end
  customer and allow resellers.
- Allow resellers to view and edit their existing customers in the website portal.
- Move reseller logic to a separate module to decouple it from argocd
