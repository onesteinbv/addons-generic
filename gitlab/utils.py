from datetime import timezone

from dateutil import parser


def _gitlab_datetime_to_odoo(datetime_string):
    dt = parser.parse(datetime_string)
    dt = dt.astimezone(timezone.utc)
    dt = dt.replace(tzinfo=None)
    return dt
