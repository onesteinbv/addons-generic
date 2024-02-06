=====================================
Website Share Filter Option Technical
=====================================

N.B.:
This is a technical module: it doesn't introduce new features at user-side.
Rather, it implements functionalities and interfaces for other modules to use.

This module adds website-level settings in order to allow the website
administrator to choose on which Social Media or technology a user can share
contents.
This, being a technical module, only introduces the functionality without
applying it to any page. Other modules, depending from this, are responsible
for it (e.g.: website_event_share_filter_option).

This module only impacts default Odoo Sharing Options (Facebook,
Twitter, Linkedin, Whatsapp, Pinterest, Email). If additional options are
implemented by other modules, they should also extend this functionality (e.g.:
module website_share_filter_option_mastodon).

Credits
=======

Authors
~~~~~~~

* Onestein

Contributors
~~~~~~~~~~~~

* Antonio Esposito <a.esposito@onestein.nl>
