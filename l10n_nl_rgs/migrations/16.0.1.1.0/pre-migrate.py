# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def _fix_accounts(env):
    rgs_template = env.ref("l10n_nl_rgs.l10nnl_rgs_chart_template")
    for company in (
        env["res.company"]
        .with_context(active_test=False)
        .search([("chart_template_id", "=", rgs_template.id)])
    ):
        account = env["account.account"].search(
            [("code", "=", 1103400), ("company_id", "=", company.id)]
        )
        if account:
            account.write({"code": 1103007})
        account = env["account.account"].search(
            [("code", "=", 1103105), ("company_id", "=", company.id)]
        )
        if account:
            account.write({"deprecated": True})


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute(
        """UPDATE ir_model_data
           SET name=%s
           WHERE module='l10n_nl_rgs' AND name=%s
        """,
        ("1103007", "1103400"),
    )
    _fix_accounts(env)
