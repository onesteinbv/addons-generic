***********************
ArgoCD Sales Management
***********************

Deploy application when an invoice is paid.
Use system parameter (configurable via res.config.settings) sale.automatic_invoice

Product configuration
*********************

#. Go to Sales > Products > Products
#. Create a product
#. Select an application template for the product

Deployment notifications
************************

#. If you want to a send email to customer when a deployment is queued, please take a look at mail template: **ArgoCD: Deployment Notification (for partner)**
#. Also take a look at the field **"Automatically send deployment notification"** on application templates (ArgoCD > Templates)
