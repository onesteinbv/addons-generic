# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.account.models.chart_template import update_taxes_from_templates


def migrate(cr, version):
    update_taxes_from_templates(cr, "l10n_nl_rgs.l10nnl_rgs_chart_template")
