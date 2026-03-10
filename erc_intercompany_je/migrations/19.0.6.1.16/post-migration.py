# License OPL-1 (Odoo Proprietary License v1.0) - (c) 2026 ERC Implementors LTDA

import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.erc_intercompany_je.hooks import (
    _is_param_enabled,
    _run_intercompany_autosetup,
)

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    if not _is_param_enabled(env, "erc_intercompany_je.autosetup_on_upgrade", True):
        _logger.info(
            "Migration 19.0.6.1.16: intercompany autosetup skipped by backend parameter."
        )
        return
    _logger.info(
        "Migration 19.0.6.1.16: running intercompany autosetup for all active companies."
    )
    _run_intercompany_autosetup(env, "Post-migration")
