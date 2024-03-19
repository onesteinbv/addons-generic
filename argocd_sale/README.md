# ArgoCD Sales Management


Deploy application when an invoice is paid.

How oca_subscription works:
<pre>
sale order -> (payment link + payment) -> first invoice
                                       -> subscription -> recurring invoice
</pre>

Because the first invoice is not linked ot the subscription we skip the sale order and directly use
sale.subscription

## Product configuration

1. Go to Sales > Products > Products
2. Create a product
3. Select an application template for the product
4. Check "Subscribable product" subscription template is not necessary.

## Deployment notifications

1. If you want to a send email to customer when a deployment is queued, please take a look at mail template: **ArgoCD: Deployment Notification (for partner)**
2. Also take a look at the field **"Automatically send deployment notification"** on application templates (ArgoCD > Templates)

## Grace periods

1. Set system parameter `argocd_sale.grace_period` to the amount of **days** you allow
   customers to not pay until the subscription is closed and application is deleted.
2. You can also find these settings in res.config.parameters (tab Sales)

## Roadmap

* Move generic functionality (grace period, invoice paid hook) to subscription_oca
