import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Populates the slugs of the projects
    """
    _logger.info(
        "Post-migration 16.0.1.0.1 - repopulating computed slugs of projects..."
    )
    env = api.Environment(cr, SUPERUSER_ID, {})
    Project = env["project.project"]
    all_projects = Project.sudo().with_context(active_test=False).search([])
    if not all_projects:
        _logger.info("Post-migration 16.0.1.0.1 - no projects to update")
        return

    env.add_to_compute(Project._fields["slug"], all_projects)
    all_projects.invalidate_recordset(fnames=["slug"])
    all_slugs = all_projects.mapped("slug")
    assert all(all_slugs)
    _logger.info("Post-migration 16.0.1.0.1 - slugs repopulated.")
