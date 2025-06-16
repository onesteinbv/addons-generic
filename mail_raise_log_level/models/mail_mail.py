import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class Mail(models.Model):
    _inherit = "mail.mail"

    @api.model
    def _get_failures_to_log(self):
        return ["unknown", "mail_smtp"]

    def _postprocess_sent_message(
        self, success_pids, failure_reason=False, failure_type=None
    ):
        res = super()._postprocess_sent_message(
            success_pids, failure_reason=failure_reason, failure_type=failure_type
        )
        failures_to_log = self._get_failures_to_log()
        if failure_type and failure_type in failures_to_log:
            _logger.error(
                "Outgoing mail failure (%s): %s",
                failure_type,
                failure_reason or ",".join(self.mapped("failure_reason")) or "unknown",
            )
        return res
