from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import MissingError


class ApplicationStat(models.Model):
    _name = "argocd.application.stat"
    _description = "Application Statistics"
    _order = "date desc"

    application_id = fields.Many2one(
        comodel_name="argocd.application", required=True, ondelete="cascade"
    )
    type_id = fields.Many2one(
        comodel_name="argocd.application.stat.type", required=True
    )
    date = fields.Datetime(help="The date when the measurement was done", required=True)
    message = fields.Char()
    value = fields.Float()

    @api.model
    def create_stats(self, application_name, stats):
        """
        Create argocd.application.stat easier

        @param application_name: name of the application the stats relate to
        @param stats: list of stats (dicts):
            - type: Key of argocd.application.stat.type
            - date: date Odoo formatted (YY-MM-dd HH:mm:ss)
            - value: float value
            - message: string value
        @return: ids of the created records
        """
        application = self.env["argocd.application"].search(
            [("name", "=", application_name)]
        )
        if not application:
            raise MissingError(
                "Application with name `%s` doesn't exist" % application_name
            )
        type_ids = {}
        to_create = []
        for stat in stats:
            stat_type_key = stat["type"]
            if stat_type_key not in type_ids:
                stat_type = self.env["argocd.application.stat.type"].search(
                    [("key", "=", stat_type_key)]
                )
                if not stat_type:
                    raise MissingError(
                        "Statistics Type with key `%s` doesn't exist" % stat_type_key
                    )
                type_ids[stat_type_key] = stat_type.id
            type_id = type_ids[stat_type_key]
            values = {
                "application_id": application,
                "type_id": type_id,
                "date": stat["date"],
                "value": float(stat.get("value", "0")),
                "message": stat.get("message"),
            }
            to_create.append(values)

        return self.create(to_create).ids

    def _cron_cleanup_old_stats(self):
        retention = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("argocd.application_stat_retention_days", "0")
        )
        if not retention:
            return
        abandoned_date = fields.Datetime.now() - timedelta(days=retention)
        self.search(
            [("date", "<=", fields.Datetime.to_string(abandoned_date))]
        ).unlink()
