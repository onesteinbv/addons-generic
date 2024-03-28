**************
ArgoCD Deloyer
**************

This module manages a git repository which is deployed as an ArgoCD application set.
Info on application sets: `<https://argo-cd.readthedocs.io/en/stable/user-guide/application-set>`_ and
`<https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/Generators-Git/#git-generator-directories>`_
It uses a git generator (directory) to spawn e.g. Curq instances.
By simply adding a file in like this ``instances/**/config.yaml`` the application set generates a new application.
This is how the repo should look like: `Example application set <git@github.com:onesteinbv/odoo-generator-k8s.git>`_


Configuration
#############

Adjust the "Default" application set in the "Application Sets" menu
There are 4 parameters to configure for the application set:
1. The URL of the repository where the repo is hosted
2. The branch that is adjusted by this application set
3. The directory where the repository is stored locally
4. The directory inside the repository where the application configurations are stored.
4. The domain format used in creating domain names for applications if there's none specified

Installation
############

1. Add to odoo config file:

.. code-block:: ini

    server_wide_modules = web,queue_job

    [queue_job]
    channel = root:1
