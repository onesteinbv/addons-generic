# ArgoCD Frontend

## Set up resellers

Follow the instructions in the ArgoCD Sales Management module to set up resellers and reseller products. This module relies on the reseller and product configuration.

## Configure products

Products must be linked to an ArgoCD Application Template and Sales (`sale_ok`) must be enabled to make them visible on the website.

## Usage

`/application/order` route accepts a `product_id` query parameter to preselect a product on the order page. This allows you to link directly to the order page for a specific product from the website or other marketing materials. If an product is preselected it will show the configured optional products as well to allow customers to easily add them to their order. If no product is preselected, the customer can select any product that is configured for the website and has an application template assigned.

The customers / visitor order on the website is a draft subscription (similar to the eCommerce flow) that allows them to select products and configure their order before confirming it. If the customer is not logged in, they will be prompted to log in or create an account before confirming their order (subscription). Once the customer is logged in the subscription is linked to their account. Or if the customer is a reseller it will create a subscription on behalf of the end customer.

When the customer confirms their order, the subscription is created and the application is automatically deployed based on the selected products and their configuration. The customer can then manage their subscription and applications from their account portal.

## Remove abandoned orders (subscription)

To prevent abandoned orders from being left in a draft state indefinitely, a scheduled action runs daily to check for draft subscriptions that were created more than 14 days ago. These old draft subscriptions are automatically cancelled and deleted to keep the system clean and prevent clutter from abandoned orders.
The amount of days can be configured via the `argocd_website.subscription_abandoned_period` system parameter.

# Roadmap

- Allow resellers to select exising customers when confirming an order on the website. This would allow resellers to place orders on behalf of existing customers and makes an end customer optional (resellers can manage their own applications and of their customers). This would also prevent multiple partners to be created for the same end customer and allow resellers.
- Allow resellers to view and edit their existing customers in the website portal.
