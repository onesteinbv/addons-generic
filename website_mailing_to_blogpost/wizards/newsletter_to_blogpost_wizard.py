# Copyright 2024 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class NewsletterToBlogpostWizard(models.TransientModel):
    _name = "newsletter.to.blogpost.wizard"
    _description = "Convert to Blogpost"

    publish = fields.Boolean(default=True)
    mailing_id = fields.Many2one("mailing.mailing", required=True)
    blog_id = fields.Many2one("blog.blog", required=True)
    tag_ids = fields.Many2many(
        comodel_name="blog.tag",
        required=True,
        default=lambda self: self.env["blog.tag"]
        .search([("name", "=", "General Newsletter")])
        .ids,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self._context.get("active_model") == "mailing.mailing" and self._context.get(
            "active_id"
        ):
            res["mailing_id"] = self._context["active_id"]
        return res

    def newsletter_to_blogpost(self):
        self.ensure_one()
        slug = self.env["ir.http"]._slug
        new_blog_post = self.env["blog.post"].create(
            [
                {
                    "name": self.mailing_id.subject,
                    "content": self.mailing_id.body_arch,
                    "blog_id": self.blog_id.id,
                    "tag_ids": self.tag_ids.ids,
                    "is_published": self.publish,
                }
            ]
        )
        self.mailing_id.blog_post_id = new_blog_post.id
        return {
            "type": "ir.actions.act_url",
            "url": "/blog/%s/post/%s"
            % (slug(new_blog_post.blog_id), slug(new_blog_post)),
            "target": "self",
        }
