=============================
Website Hide Navbar Technical
=============================

N.B.:
This is a technical module: it doesn't introduce new features at user-side.
Rather, it implements functionalities and interfaces for other modules to use.

This module extends the website.user_navbar template and introduces the
evaluation of a new parameter 'no_navbar' when deciding if the website
navigation bar must be visible or not.

On pages where you wish to hide the navigation bar, simply call the template
website.frontend_layout passing the no_navbar parameter set True.

For an example, you can look at the module 'website_two_steps_share_technical'.


Credits
=======

Authors
~~~~~~~

* Onestein

Contributors
~~~~~~~~~~~~

* Antonio Esposito <a.esposito@onestein.nl>
