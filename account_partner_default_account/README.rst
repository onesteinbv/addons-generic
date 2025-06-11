=======================
Partner Default Account
=======================

This module allows to automatically select the account of invoice lines
based on the selected partner instead of the selected product which is the standard Odoo way.

Configuration
~~~~~~~~~~~~~

To be able to configure the account per partner:

- Be sure you belong to group `Show Accounting Features - Readonly`
- Open a partner form and select the `Invoicing` tab
- Under "Accounting Entries" set the field `Partner Default Account`

Notice that field `Partner Default Account` is company-dependent.

Usage
~~~~~

When creating an invoice, select a partner. The account of invoice
lines will be selected accordingly.
