# Part of Odoo. See LICENSE file for full copyright and licensing details.
import itertools
import logging

from odoo import http
from odoo.http import request

from odoo.addons.website_hr_recruitment.controllers.main import WebsiteHrRecruitment

_logger = logging.getLogger(__name__)


def job_routes():
    prefix = "/jobs"
    filters = [
        '/country/<model("res.country"):country>',
        '/department/<model("hr.department"):department>',
        "/office/<int:office_id>",
        "/employment_type/<int:contract_type_id>",
        "/label_ids/<models('hr.job.label'):label_ids>",
    ]
    routes = ["/jobs"]
    for L in range(len(filters) + 1):
        for subset in itertools.combinations(filters, L):
            routes.append(prefix + "".join(subset))
    return routes


class WebsiteHrRecruitmentLabel(WebsiteHrRecruitment):
    def sitemap_jobs(self, rule, qs):
        if not qs or qs.lower() in "/jobs":
            yield {"loc": "/jobs"}

    @http.route(
        job_routes(), type="http", auth="public", website=True, sitemap=sitemap_jobs
    )
    def jobs(
        self,
        country=None,
        department=None,
        office_id=None,
        contract_type_id=None,
        label_ids=None,
        **kwargs
    ):
        res = super(WebsiteHrRecruitmentLabel, self).jobs(
            country, department, office_id, contract_type_id, **kwargs
        )
        env = request.env(
            context=dict(request.env.context, show_address=True, no_tag_br=True)
        )

        # Filters any remaining jobs according to the selected labels in
        # label_ids
        context = res.qcontext
        jobs = context["jobs"]
        remaining_jobs = jobs
        if label_ids:
            labels = env["hr.job.label"].sudo().browse(label_ids)
            for cat in labels.category_id:
                final_jobs = set()
                cat_label_ids = labels.filtered(lambda r: r.category_id == cat)
                for job in remaining_jobs:
                    if set(cat_label_ids.ids) & set(job.label_ids.ids):
                        final_jobs.add(job)
                remaining_jobs = final_jobs

        # Returns all the labels that are used, grouped per category. If there is
        # only one label used in that category, this whole category will not be included
        label_split_up = []
        categories = (
            env["hr.job.label.category"].sudo().search([("allow_filtering", "=", True)])
        )
        all_jobs = env["hr.job"].search([])
        for cat in categories:
            if not cat.label_ids:
                continue
            cat_dict = {"category": cat}
            amount_of_labels_used = 0
            children = []
            for label in cat.label_ids.sorted(key=lambda r: r.sequence):
                if all_jobs.filtered(lambda r: label in r.label_ids and r.is_published):
                    amount_of_labels_used += 1
                    children.append(
                        {
                            "label": label,
                            "count": sum(
                                [
                                    1
                                    if (x.is_published and label in x.label_ids)
                                    else 0
                                    for x in jobs
                                ]
                            ),
                        }
                    )
            if amount_of_labels_used >= 2:
                cat_dict["children"] = children
                label_split_up.append(cat_dict)

        res.qcontext.update(
            {
                "jobs": list(remaining_jobs),
                "labels_split_up": label_split_up,
                "label_ids": label_ids,
            }
        )
        return res
