from odoo import api, models


class Website(models.Model):
    _inherit = "website"

    def unlink(self):
        """We need access to res.company because deletion of websites
        recomputes res.company.website_id field (manually in unlink method of the website model).
        website.unlink will not delete the company so it is fine.
        """
        if self.user_has_groups("website_security.group_website_security_config"):
            return super(Website, self.sudo()).unlink()
        return super().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        """We need access to res.company because creation of websites
        recomputes res.company.website_id field (manually in create method of the website model)
        """
        if self.user_has_groups("website_security.group_website_security_config"):
            return super(Website, self.sudo()).create(vals_list)
        return super().create(vals_list)

    def create_and_redirect_configurator(self):
        if self.user_has_groups("website_security.group_website_security_config"):
            return super(Website, self.sudo()).create_and_redirect_configurator()
        return super().create_and_redirect_configurator()
