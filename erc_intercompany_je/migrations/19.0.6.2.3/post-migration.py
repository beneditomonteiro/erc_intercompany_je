# License OPL-1 (Odoo Proprietary License v1.0) - (c) 2026 ERC Implementors LTDA

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    # 1. Create the new cron if it doesn't exist (noupdate="1" won't auto-create on upgrade)
    cron_xmlid = "erc_intercompany_je.ir_cron_daily_intercompany_order_journal_realign"
    existing = env.ref(cron_xmlid, raise_if_not_found=False)
    if not existing:
        _logger.info("Migration 19.0.6.2.3: creating IC order journal realignment cron.")
        company_model = env["ir.model"].search([("model", "=", "res.company")], limit=1)
        cron = env["ir.cron"].create({
            "name": "Intercompany Order Journal Realignment (Daily)",
            "active": True,
            "user_id": env.ref("base.user_root").id,
            "interval_number": 1,
            "interval_type": "days",
            "model_id": company_model.id,
            "state": "code",
            "code": "model._cron_realign_intercompany_order_journals()",
        })
        # Register the xmlid so future upgrades recognize it
        env["ir.model.data"].create({
            "name": "ir_cron_daily_intercompany_order_journal_realign",
            "module": "erc_intercompany_je",
            "model": "ir.cron",
            "res_id": cron.id,
            "noupdate": True,
        })
    else:
        _logger.info("Migration 19.0.6.2.3: realignment cron already exists.")

    # 2. Run immediate realignment on all draft IC orders (HQ first, then branches)
    _logger.info("Migration 19.0.6.2.3: realigning IC journals on draft orders.")
    root_companies = (
        env["res.company"]
        .sudo()
        .with_context(active_test=False)
        .search([("parent_id", "=", False), ("active", "=", True)], order="id")
    )
    for root_company in root_companies:
        companies = root_company._get_same_group_companies()
        for company in companies:
            try:
                company._realign_company_ic_orders(company)
            except Exception:
                _logger.exception(
                    "Migration 19.0.6.2.3: realignment failed for %s (%s)",
                    company.display_name,
                    company.id,
                )
