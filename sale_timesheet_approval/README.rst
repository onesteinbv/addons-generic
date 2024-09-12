.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

==================
Timesheet Approval
==================

In Odoo 8.0 you could invoice hours based on timesheet lines.
In later versions of Odoo this option is gone (all timesheet lines that are connected to a sales orderline will be invoiced immediately).

This module allows to approve timesheet lines. Only timesheet lines that are approved can be invoiced.

To be able to approve timesheet lines (and create invoices), the related timesheet must be in status 'approved' as well.
It is not possible to delete or edit timesheet lines AFTER they are validated: to invoice another amount of hours, the user must change that on the invoice line.

NOTICE: this module could be conflicting with enterprise module timesheet_grid !

Known issues / Roadmap
======================

 * Move "week_number" field and related filters to a separate module

Credits
=======

Contributors
------------

* Andrea Stirpe <a.stirpe@onestein.nl>
* Antonio Esposito <a.esposito@onestein.nl>
* Anjeel Haria <a.haria@onestein.nl>
