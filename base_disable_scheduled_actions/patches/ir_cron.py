# Copyright 2017-2023 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# This override to ir_cron prevents cron jobs from ever being automatically
# scheduled.
import logging

from odoo.addons.base.models.ir_cron import ir_cron

_logger = logging.getLogger(__name__)


def _patch_get_all_ready_jobs(cls, cr):
    """Prevent jobs from ever being processed by never letting them be found."""
    _logger.info("Scheduled actions were disabled. Not returning any.")
    return []


_logger.info("Patching ir_cron._get_all_ready_jobs to disable scheduled actions...")
ir_cron._get_all_ready_jobs = _patch_get_all_ready_jobs
