from odoo import fields, models


class ApplicationTag(models.Model):
    _name = "argocd.application.tag"
    _description = "Application Tag"

    name = fields.Char(required=True)
    key = fields.Char(required=True, copy=False)
    is_odoo_module = fields.Boolean(string="Is additional Odoo Module")
    domain_yaml_path = fields.Char(
        help="Path where to find the domain in the yaml (e.g. nextcloud.domain)"
    )
    domain_override_ids = fields.One2many(
        "argocd.application.tag.domain.override", inverse_name="tag_id"
    )

    _sql_constraints = [("application_tag_key_unique", "unique(key)", "Already exists")]

    def get_domain_yaml_path(self, application_set=False):
        self.ensure_one()
        if not application_set or application_set.id not in self.domain_override_ids.application_set_id.ids:
            return self.domain_yaml_path or ""
        return self.domain_override_ids.filtered(
            lambda do: do.application_set_id == application_set
        ).domain_yaml_path or ""
