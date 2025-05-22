===================
Subscription Portal
===================

Subscription Portal

Roadmap
-------

* Add cancelled stage to `subscription_oca`. Field `date_stop` is there to prevent refactoring
  alot of the OCA module. Ideally there should be cancelled stage before the closed stage in case the customer
  cancels their subscription their subscription should stay active until the next payment date
  (in case the subscription is a service). Because `sale.subscription.close_subscription` sets
  `recurring_next_date` to False we can't know until when we need to provide the service. Also setting
  finish date (`date`) will be buggy because the subscription can be created in a payment provider
  (in sale_recurring_payment module). It then requires the subscription cron to run before the automatic
  payment is done which we can't guarantee resulting in one extra payment.
