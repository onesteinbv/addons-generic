# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class XafAuditfileExport(models.Model):
    _inherit = "xaf.auditfile.export"

    def _get_auditfile_template(self):
        """return the qweb template to be rendered"""
        return "l10n_nl_rgs_xaf_auditfile_export.auditfile_template"
