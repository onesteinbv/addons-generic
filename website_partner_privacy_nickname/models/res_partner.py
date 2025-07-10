from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    website_privacy = fields.Selection(ondelete={"nickname": "set default"})

    def website_privacy_selection(self):
        res = super().website_privacy_selection()
        res.append(("nickname", "Use Nickname"))
        return res

    @api.model_create_multi
    def create(self, values_list):
        for vals in values_list:
            if "website_privacy" in vals and vals["website_privacy"] == "nickname":
                if not vals.get("nickname"):
                    raise ValidationError(
                        self.env._(
                            "Nickname should be specified if Website Privacy is set to Use Nickname"
                        )
                    )
                else:
                    vals.update({"seo_name": vals["nickname"]})
        return super().create(values_list)

    def write(self, vals):
        if "website_privacy" in vals and vals["website_privacy"] == "nickname":
            for record in self:
                if not vals.get("nickname", record.nickname):
                    raise ValidationError(
                        self.env._(
                            "Nickname should be specified if Website Privacy is set to Use Nickname"
                        )
                    )
                else:
                    vals.update({"seo_name": vals.get("nickname", record.nickname)})
        return super().write(vals)

    def _get_complete_name(self):
        name = super(ResPartner, self)._get_complete_name()
        if self._context.get("website_id"):
            if (
                self.website_privacy
                and self.website_privacy == "nickname"
                and self.nickname
            ):
                name = self.nickname
        return name
