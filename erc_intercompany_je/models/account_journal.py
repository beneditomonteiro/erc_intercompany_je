# -*- coding: utf-8 -*-
# License OPL-1 (Odoo Proprietary License v1.0) - (c) 2026 ERC Implementors LTDA

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    intercompany_production_account_id = fields.Many2one(
        "account.account",
        string="Default Production Income Account",
        domain="[('account_type', 'in', ('income', 'income_other'))]",
        check_company=True,
        help="Used for intercompany sales of goods that have a Bill of Materials (BOM). "
        "When set and the BOM routing feature is enabled, invoice lines for "
        "manufactured products will use this account instead of the journal's "
        "Default Income Account.",
    )
