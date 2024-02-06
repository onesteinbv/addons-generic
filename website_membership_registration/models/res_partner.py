import hashlib
import uuid
from datetime import datetime

from dateutil.relativedelta import relativedelta
from werkzeug import urls

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    nickname = fields.Char()

    email_verification_token = fields.Char()
    email_verification_url = (
        fields.Char()
    )  # This is only useful for debug, in case email doesn't go out

    membership_email_verification_status = fields.Selection(
        [("verified", "Verified"), ("unverified", "Unverified"), ("ignore", "Ignore")],
        default="ignore",
    )

    membership_application_date = fields.Date()
    membership_origin = fields.Selection(
        selection_add=[("website_form", "Website Form")]
    )

    applicant_ids = fields.One2many("hr.applicant", "partner_id")

    follower_sections_count = fields.Integer(
        string="Following # Sections",
        compute="_compute_section_ids",
        store=True,
    )
    applicant_sections_count = fields.Integer(
        string="Applicant to # Sections",
        compute="_compute_section_ids",
        store=True,
    )
    collaborator_sections_count = fields.Integer(
        string="Collaborating to # Sections",
        compute="_compute_section_ids",
        store=True,
    )

    def _get_name(self):
        if self.nickname and not self.website_published:
            return self.nickname
        return super(ResPartner, self)._get_name()

    @api.depends(
        "is_company",
        "name",
        "parent_id.display_name",
        "type",
        "company_name",
        "commercial_company_name",
        "nickname",
        "website_published",
    )
    def _compute_display_name(self):  # pylint: disable=missing-return
        for partner in self:
            if partner.nickname and not partner.website_published:
                partner.display_name = partner.nickname
            else:
                super(ResPartner, partner)._compute_display_name()

    @api.depends(
        "section_membership_ids",
        "section_membership_ids.section_id",
        "section_membership_ids.on_mailing_list",
        "section_membership_ids.wants_to_collaborate",
        "employee_ids",
        "applicant_ids",
    )
    def _compute_section_ids(self):
        res = super(ResPartner, self)._compute_section_ids()
        for partner in self:
            partner.follower_sections_count = len(
                partner.section_membership_ids.filtered(
                    lambda x: x.on_mailing_list
                ).mapped("section_id")
            )
            partner.applicant_sections_count = len(
                partner.section_membership_ids.filtered(
                    lambda x: x.type == "applicant"
                ).mapped("section_id")
            )
            partner.collaborator_sections_count = len(
                partner.section_membership_ids.filtered(
                    lambda x: x.type == "collaborator"
                ).mapped("section_id")
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
                        _("Another Member already exists with email %s", partner.email)
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
                        _("Another User already exists with email %s", partner.email)
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
            partners.unlink()

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
            raise ValidationError(_("No email address available for this partner"))

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
        raise ValidationError(_("Verification code is invalid."))

    def create_member_applicant(self):
        self.ensure_one()
        if (
            self.section_membership_ids.filtered(lambda x: x.wants_to_collaborate)
            and self.website_id.membership_job_id
        ):
            self.env["hr.applicant"].create(
                {
                    "name": "%s - %s"
                    % (self.name, self.website_id.membership_job_id.name),
                    "partner_name": self.name,
                    "partner_id": self.id,
                    "job_id": self.website_id.membership_job_id.id,
                    "membership_applicant": True,
                }
            )

    def create_membership_sale_order(self, product, amount):
        """Create Sale Order of Membership for partners."""
        sale_vals_list = []
        for partner in self:
            addr = partner.address_get(["invoice"])
            if partner.free_member:
                raise UserError(_("Partner is a free Member."))
            if not addr.get("invoice", False):
                raise UserError(
                    _("Partner doesn't have an address to make the invoice.")
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
                                "tax_id": [(6, 0, product.taxes_id.ids)],
                            },
                        )
                    ],
                }
            )

        return self.env["sale.order"].create(sale_vals_list)
