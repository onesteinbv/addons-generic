This module solves some problems of the *Access Rights* group of core Odoo by introducing
a new group: *Manage Companies*.

**The problem with the Access Rights / Settings groups:**

When you assign the *Access Rights* group to a user, the user can still get access to everything
by just creating a new user with full access.
Also the user can alter the admin account e.g. change it's password locking the system administrator
out of the system.
Giving the user Settings group (base.group_system) will give the user access to critical model
e.g. views, users, groups, and system parameters
