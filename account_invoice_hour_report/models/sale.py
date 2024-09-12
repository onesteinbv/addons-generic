# Copyright 2024 Onestein (<http://www.onestein.eu>)

import base64

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _create_invoices(self, grouped=False, final=False, date=None):
        res = super()._create_invoices(grouped=grouped, final=final, date=date)
        report_obj = self.env["ir.actions.report"]
        for move in res:
            ctx = {
                "tz": self.env.user.tz,
                "uid": self.env.uid,
                "lang": move.partner_id.lang,
            }
            timesheet_lines = move.timesheet_ids
            if timesheet_lines:
                pdf, _ = report_obj.with_context(ctx)._render_qweb_pdf(
                    "account_invoice_hour_report.report_invoice_hours_report",
                    res_ids=timesheet_lines.ids,
                )
                self.env["ir.attachment"].create(
                    {
                        "name": "timesheet_detail.pdf",
                        "res_id": move.id,
                        "res_model": str(move._name),
                        "datas": base64.b64encode(pdf),
                        "mimetype": "application/pdf",
                    }
                )
        return res
