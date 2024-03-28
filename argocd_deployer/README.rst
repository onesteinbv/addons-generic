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

System parameters
-----------------
The following system parameters can be configured.

- ``argocd.application_set_repo``: Set to the SSH URL of the repository that stores the application sets.
- ``argocd.application_set_branch``: Set to the branch that contains the application sets. Should normally be HEAD or main.
- ``argocd.application_set_repo_directory``: The local folder that contains the .git folder of the repository that contains the application sets.
- ``argocd.application_set_deployment_directory``: The folder inside the repository that will contain the application sets.
- ``argocd.git_simulation_mode``: For debugging purposes. Can be set to values like ``none``, ``push``, ``pull``, ``push&pull``. By setting one of these values, the corresponding git action will be simulated.

Application sets
----------------
Application sets contain definitions of ArgoCD application sets. These application sets
contain base settings for applications that can be deployed. The only requirement is that the combination
of repository, branch and deployment directory is unique.

Example: A large change has been made to the application repository, and it now uses a different
configuration of the database. Auto-syncing the applications in the application set
would cause all existing pods to break. Instead, it's possible to either
configure a different directory for the applications that need to have this update
applied, or a different branch. Or both.

Application sets can be configured in the ArgoCD app. They take the following
fields:

- Name: must contain only lowercase letters, numbers, or numbers: the unique name
  under which the application set will be deployed. Must be unique, as it will be used to create a namespace in the cluster.
- Description: detailed description of the application set.
- Template: the application set template to used to create the application set's YAML file.
- Repository URL: the repository in which the application set's apps are stored
- Branch: the branch in which the apps are stored
- Repository Directory: the local folder where the repository clone lives
- Deployment Directory: the folder inside the repository where apps are deployed
- Domain format: when an app is deployed, this determines at what domain it will be deployed.
- Subdomain format: when an app is deployed through a reseller, this is the format of its domain.

An application set can be deployed or destroyed. This will cause the master
repository to updated.

.. warning::
  The master application set can also be deployed/destroyed! By destroying it, ArgoCD should
  not respond to any changes in the deployments anymore.

Applications
------------
Applications can be configured as follows:

- Name: must contain only lowercase letters, numbers, or numbers: the unique name
  under which the application will be deployed. Must be unique, even across application sets,
  as it will be used to create a namespace in the cluster.
- Partner: the name of the partner holding the subscription.
- Subscription: the subscription linked to this deployment.
- Application Set: the application set in which the application will be deployed.
- Template: a set of YAML instructions customizing the application.
- Repository URL: the repository in which the application set's apps are stored
- Tags: tags that can be used to automatically adjust the application's configuration
- Repository Directory: the local folder where the repository clone lives
- Deployment Directory: the folder inside the repository where apps are deployed
- Domain format: when an app is deployed, this determines at what domain it will be deployed.
- Subdomain format: when an app is deployed through a reseller, this is the format of its domain.


Installation
############

1. Add to odoo config file:

.. code-block::

  server_wide_modules = web,queue_job
  [queue_job]
  channel = root:1
