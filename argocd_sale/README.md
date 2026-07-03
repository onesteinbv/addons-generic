# ArgoCD Sales Management

This module integrates ArgoCD application deployment with Odoo's sales and subscription
management. It enables automated deployment of applications based on paid subscriptions,
supports reseller hierarchies, and provides usage-based billing for deployed
applications.

## Set up resellers

Mark partners as resellers by enabling the "Is Reseller" checkbox. Resellers can have
customers linked to them and can be restricted to sell only specific products. Configure
the reselling products on the reseller partner form.

For subscriptions with a reseller as the partner, you can optionally specify an end
customer using the "End Customer" field. This end customer must be registered as a
customer of that reseller.

### Constraints

The module enforces several validation rules to maintain data integrity and prevent
misconfiguration:

- Resellers cannot have a parent partner or be a customer of another reseller (prevents
  pyramid schemes)
- Partners with a reseller parent cannot have child partners keeping simple structure
  for resellers. Normal structure would be: Reseller Company -> Persons e.g. Company X
  -> John Doe, Jane Doe, etc. and not Reseller Company -> Reseller Company 2 -> John
  Doe, Jane Doe, etc.
- Non-reseller partners cannot have reselling products or reseller customers assigned

If a reseller company has child partners, those child partners are considered employees
of the reseller allowing them to sell products on behalf of the reseller. But they don't
have products assigned to them directly, they inherit the products from the reseller
company. This allows for a simple structure where a reseller company can have multiple
employees (child partners).

## Product configuration

Products must be linked to an ArgoCD Application Template and Application Set to enable
automated deployment. Configure these fields on the product form along with the standard
subscription settings.

Products can also be configured with statistics-based products for usage billing, which
will be automatically invoiced based on application statistics (e.g., storage, API
calls).

### Product variants / attributes

Product attributes can be assigned an "ArgoCD Identifier" field, and attribute values
can have an "ArgoCD Value" field. These values are used when rendering the YAML
configuration for the deployed applications, making it easier to map product variants to
application configuration.

### Reseller only products

Products with assigned resellers (via the "Resellers" field) are only available to those
specific resellers. If no resellers are assigned, the product is publicly available to
all customers.

## Grace period

Configure a grace period in days via Settings > Sales > Subscription Grace Period.

A scheduled action checks for subscriptions where the paid-for date is earlier than
today minus the grace period. These late subscriptions are automatically closed, and
their applications are terminated according to the configured termination action
(destroy application or add tag).

Subscription termination actions can be configured in Settings: either destroy the
application immediately or add a specific tag to mark it for termination.

## Usage

1. Create a sales order/subscription with products that have application templates
   configured
2. When the first invoice is paid, the application is automatically created with a
   unique name based on the partner and product
3. The application configuration is rendered using the product's template and any
   product variant attributes
4. The application is automatically deployed to the configured ArgoCD application set
5. Subsequent invoices will include any statistics-based products based on actual
   application usage
6. When changing product variants or quantities, applications are automatically
   redeployed with the updated configuration
7. When a subscription is closed, applications are terminated based on the configured
   termination action (either destroyed immediately or tagged for later removal)

## Roadmap

- Constrain subscriptions to only allow reseller products to be sold by configured
  resellers
- Refactor statistics-based products to be more flexible and support different types of
  usage metrics and measurement methods
- Add support to link products to multiple application sets to allow distributed
  application deployments across multiple clusters
- Allow a product attribute value to override the application set. E.g. a product could
  be linked to a default application set, but if a specific attribute value is selected,
  it could deploy to a different application set/cluster. Use case would be to select
  different regions for deployment based on the selected attribute value.
