import logging
import re

from odoo.addons.mail.models.fetchmail import __name__ as fetchmail_name

_mail_logger = logging.getLogger(fetchmail_name)
_logger = logging.getLogger(__name__)

CAPTURE_PATTERNS = [
    r"General failure when trying to fetch mail",
]


class LogHandler(logging.Handler):
    def emit(self, record):
        for pattern in CAPTURE_PATTERNS:
            if re.match(pattern, record.msg):
                _logger.error(record.getMessage(), exc_info=record.exc_info)
                break


handler = LogHandler()
handler.setLevel(logging.INFO)
_mail_logger.addHandler(handler)
