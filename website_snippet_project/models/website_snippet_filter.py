from odoo import api, models
from odoo.osv import expression


class WebsiteSnippetFilter(models.Model):
    _inherit = "website.snippet.filter"

    @api.model
    def _get_projects(self, mode, context):
        dynamic_filter = context.get("dynamic_filter")
        handler = getattr(
            self, "_get_projects_%s" % mode, self._get_all_published_projects
        )
        website = self.env["website"].get_current_website()
        search_domain = context.get("search_domain")
        limit = context.get("limit")
        domain = expression.AND(
            [
                [("is_published", "=", True)],
                [("company_id", "in", [False, website.company_id.id])],
                search_domain or [],
            ]
        )
        projects = handler(website, limit, domain, context)
        return dynamic_filter._filter_records_to_values(projects, False)

    def _get_projects_for_category(self, website, limit, domain, context):
        return self._get_all_published_projects(website, limit, domain, context)

    def _get_all_published_projects(self, website, limit, domain, context):
        return (
            self.env["project.project"]
            .search(domain, limit=limit)
            .sorted(key=lambda p: p.name)
        )
