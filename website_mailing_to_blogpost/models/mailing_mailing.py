from odoo import fields, models


class MailingMailing(models.Model):
    _inherit = "mailing.mailing"

    blog_post_id = fields.Many2one("blog.post")
