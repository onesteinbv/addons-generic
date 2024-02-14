import logging

from odoo import models

from odoo.addons.base.models import ir_http

_logger = logging.getLogger(__name__)


# Changed/Fixes the ModelsConverter In Odoo
# By default Odoo accepts a list of ids, then converts them to module.model(1,2,
# 3). Then it puts those models in the URL again, it'll try to filter out a list of
# ids, but it is given module.model(1,2,3), and crashes on it.
# This Converter is also not used in default Odoo, so this shouldn't break anything.
class ModelsConverter(ir_http.ModelsConverter):
    def to_python(self, value):
        return [int(x) for x in value.split(",")]

    def to_url(self, value):
        if type(value) == int:
            return str(value)
        return ",".join([str(i) for i in value])


class IrHttp(models.AbstractModel):
    _inherit = ["ir.http"]

    rerouting_limit = 10

    @classmethod
    def _get_converters(cls):
        return dict(
            super(IrHttp, cls)._get_converters(),
            models=ModelsConverter,
        )
