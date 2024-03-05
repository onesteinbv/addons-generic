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

#. Change system parameter ``application_set_repo`` to the git repository with the application set manifest
#. Change system parameter ``application_set_repo_directory`` to a empty / non-existent rw directory
#. Change system parameter ``application_set_directory`` to the directory where the instance configuration files are put `(default = instances)`
#. Change system parameter ``application_domain_format`` used in creating domain names for applications if there's none specified

**Assumes https is enabled for all exposed services.**

Installation
############

1. Add to odoo config file:

.. code-block:: ini

    server_wide_modules = web,queue_job

    [queue_job]
    channel = root:1
