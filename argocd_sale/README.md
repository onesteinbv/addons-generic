# ArgoCD Sales Management


Deploy application when an invoice is paid.
Use system parameter (configurable via res.config.settings) sale.automatic_invoice

<pre>
sale order -> (payment link + payment) -> first invoice
                                       -> subscription -> recurring invoice
</pre>

## Product configuration

1. Go to Sales > Products > Products
2. Create a product
3. Select an application template for the product

## Deployment notifications

1. If you want to a send email to customer when a deployment is queued, please take a look at mail template: **ArgoCD: Deployment Notification (for partner)**
2. Also take a look at the field **"Automatically send deployment notification"** on application templates (ArgoCD > Templates)

## Grace periods

1. Set system parameter `argocd_sale.grace_period` to the amount of **days** you allow
   customers to not pay until the subscription is closed and application is deleted.

## Roadmap

* Move generic functionality (last payment date, grace period) to subscription_oca
