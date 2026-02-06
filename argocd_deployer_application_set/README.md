# ArgoCD Deployer Application Set Management

This module extends the base `argocd_deployer` module to add git repository management capabilities for ArgoCD Application Sets.

## Purpose

This module separates the potentially dangerous git operations (deploy, destroy, config management) from the base `argocd_deployer` module. This separation provides:

1. **Risk Mitigation**: Prevents accidental deletion of multiple applications by deleting an application set
2. **Security**: Prevents users from changing critical autoSync/prune settings via the Odoo interface
3. **Flexibility**: Allows installations where git management is not desired or permitted

## Features

When this module is installed, the following functionality is added to Application Sets:

- **Deployment Operations**: Deploy and destroy application sets in git
- **Config Management**: View and manage YAML configuration (live, desired, diff)
- **Status Tracking**: Monitor deployment status and destruction queue
- **Git Integration**: Full git repository operations for application set management
- **Flexible Git Targets**: Override git repository URL, branch, and deployment directory per application set

## Base Module (argocd_deployer)

The base module contains only application configuration:
- Application repository URL, branch, and deployment directory
- Local storage directory for cloned repositories
- Master/default application set relationships
- Partner followers
- Application relationships

## Extended Module (argocd_deployer_application_set)

This module adds deployment and management capabilities:
- Fields: `template_id`, `namespace_prefix`, `config`, `config_live`, `config_diff`, `is_deployed`, `is_destroying`, `has_deployed_applications`
- Optional override fields: `git_repository_url`, `git_branch`, `git_deployment_directory` (to deploy to different git targets)
- Methods: `deploy()`, `destroy()`, `immediate_deploy()`, `immediate_destroy()`, `abort_destroy()`, `render_config()`
- Extends the form view to add deployment buttons and YAML configuration panels

## Dependencies

- `argocd_deployer`: Base module containing application set definitions

## Installation

Install this module only if you need git management capabilities for application sets. Without this module, application sets can still be created and configured, but deployment/destruction operations will not be available.

## Usage

With this module installed, users with appropriate permissions can:
1. Configure application sets with template and namespace prefix
2. Deploy application sets to git repositories (optionally using different git targets)
3. Redeploy existing application sets with updated configurations
4. Queue destruction of application sets (with configurable delay)
5. Abort queued destructions
6. View diffs between live and desired configurations

## Git Deployment Flexibility

By default, application sets deploy to the same git repository, branch, and directory as the applications. However, you can override these settings:
- **git_repository_url**: Deploy to a different git repository
- **git_branch**: Deploy to a different branch
- **git_deployment_directory**: Deploy to a different directory in the repository

This allows for advanced deployment scenarios where the application set configuration is managed separately from application configurations.
