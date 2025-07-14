import hashlib
import uuid
from datetime import datetime

from dateutil.relativedelta import relativedelta
from werkzeug import urls

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    email_verification_token = fields.Char()
    email_verification_url = (
        fields.Char()
    )  # This is only useful for debug, in case email doesn't go out

    membership_email_verification_status = fields.Selection(
        [("verified", "Verified"), ("unverified", "Unverified"), ("ignore", "Ignore")],
        default="ignore",
    )

    membership_application_date = fields.Date()

    applicant_ids = fields.One2many("hr.applicant", "partner_id")

    follower_membership_groups_count = fields.Integer(
        string="Following # Membership Groups",
        compute="_compute_membership_group_ids",
        store=True,
    )
    applicant_membership_groups_count = fields.Integer(
        string="Applicant to # Membership Groups",
        compute="_compute_membership_group_ids",
        store=True,
    )
    collaborator_membership_groups_count = fields.Integer(
        string="Collaborating to # Membership Group",
        compute="_compute_membership_group_ids",
        store=True,
    )

    @api.depends(
        "membership_group_member_ids",
        "membership_group_member_ids.group_id",
        "membership_group_member_ids.type",
    )
    def _compute_membership_group_ids(self):
        res = super()._compute_membership_group_ids()
        for partner in self:
            partner.follower_membership_groups_count = len(
                partner.membership_group_member_ids.filtered(
                    lambda x: x.type
                    in ("follower", "applicant_follower", "collaborator_follower")
                ).mapped("group_id")
            )
            partner.applicant_membership_groups_count = len(
                partner.membership_group_member_ids.filtered(
                    lambda x: x.type in ("applicant", "applicant_follower")
                ).mapped("group_id")
            )
            partner.collaborator_membership_groups_count = len(
                partner.membership_group_member_ids.filtered(
                    lambda x: x.type in ("collaborator", "collaborator_follower")
                ).mapped("group_id")
            )
        return res

    @api.constrains("email", "membership_state")
    def _check_mail_unique(self):
        for partner in self:
            if partner.email and partner.membership_state != "none":
                member_found = self.search(
                    [
                        ("email", "=ilike", partner.email),
                        ("id", "!=", partner.id),
                        ("membership_state", "!=", "none"),
                    ],
                    limit=1,
                )
                if member_found:
                    raise ValidationError(
                        self.env._(
                            "Another Member already exists with email %s", partner.email
                        )
                    )
                user_found = self.env["res.users"].search(
                    [
                        ("login", "=ilike", partner.email),
                        ("partner_id", "!=", partner.id),
                    ],
                    limit=1,
                )
                if user_found:
                    raise ValidationError(
                        self.env._(
                            "Another User already exists with email %s", partner.email
                        )
                    )

    @api.model
    def cleanup_unverified_members(self):
        websites = self.env["website"].search(
            [("allow_membership_registration", "=", True)]
        )
        for website in websites:
            cleanup_date = fields.Datetime.now() - relativedelta(
                days=website.cleanup_unverified_members_days
            )
            partners = self.env["res.partner"].search(
                [
                    ("website_id", "=", website.id),
                    ("membership_email_verification_status", "=", "unverified"),
                    ("create_date", "<", cleanup_date),
                    ("user_ids", "=", False),
                    ("email_verification_token", "!=", False),
                ]
            )
            partners_to_unlink = partners
            for partner in partners:
                if partner.invoice_ids:
                    partners_to_unlink -= partner
            partners_to_unlink.unlink()

    @api.model
    def _generate_email_verification_token(self, partner_id, email):
        return hashlib.sha256(
            (
                "%s-%s-%s-%s" % (datetime.now(), str(uuid.uuid4()), partner_id, email)
            ).encode("utf-8")
        ).hexdigest()

    def send_membership_verification_email(self):
        self.ensure_one()

        if not self.email:
            raise ValidationError(
                self.env._("No email address available for this partner")
            )

        self.email_verification_token = self._generate_email_verification_token(
            self.id, self.email
        )

        params = {
            "token": self.email_verification_token,
            "partner_id": self.id,
            "email": self.email,
        }
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        verification_url = (
            base_url + "/apply-for-membership-verify?%s" % urls.url_encode(params)
        )

        self.write(
            {
                "email_verification_url": verification_url,
                "membership_email_verification_status": "unverified",
            }
        )

        mail_template = self.env.ref(
            "website_membership_registration.verification_email"
        )

        mail_template.with_context(verification_url=verification_url).send_mail(
            self.id, force_send=True, raise_exception=False
        )

    def verify_email(self, email, token):
        self.ensure_one()
        if self.email == email and self.email_verification_token == token:
            return self.write({"membership_email_verification_status": "verified"})
        raise ValidationError(self.env._("Verification code is invalid."))

    def create_member_applicant(self):
        self.ensure_one()
        if (
            self.membership_group_member_ids.filtered(lambda x: x.wants_to_collaborate)
            and self.website_id.membership_job_id
        ):
            self.env["hr.applicant"].create(
                [
                    {
                        "candidate_id": self.env["hr.candidate"]
                        .create(
                            [
                                {
                                    "partner_name": "%s - %s"
                                    % (
                                        self.name,
                                        self.website_id.membership_job_id.name,
                                    ),
                                    "partner_id": self.id,
                                }
                            ]
                        )
                        .id,
                        "job_id": self.website_id.membership_job_id.id,
                        "membership_applicant": True,
                    }
                ]
            )

    def create_membership_sale_order(self, product, amount):
        """Create Sale Order of Membership for partners."""
        sale_vals_list = []
        for partner in self:
            addr = partner.address_get(["invoice"])
            if partner.free_member:
                raise UserError(self.env._("Partner is a free Member."))
            if not addr.get("invoice", False):
                raise UserError(
                    self.env._("Partner doesn't have an address to make the invoice.")
                )

            sale_vals_list.append(
                {
                    "partner_id": partner.id,
                    "order_line": [
                        (
                            0,
                            None,
                            {
                                "product_id": product.id,
                                "product_uom_qty": 1,
                                "price_unit": amount,
                                "tax_id": [
                                    (
                                        6,
                                        0,
                                        product.taxes_id.filtered(
                                            lambda t: t.company_id.id
                                            == self.env.company.id
                                        ).ids,
                                    )
                                ],
                            },
                        )
                    ],
                }
            )

        return self.env["sale.order"].create(sale_vals_list)
