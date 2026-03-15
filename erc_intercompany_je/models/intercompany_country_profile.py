# -*- coding: utf-8 -*-
# License OPL-1 (Odoo Proprietary License v1.0) - (c) 2026 ERC Implementors LTDA

from odoo import fields, models


class IntercompanyCountryProfile(models.Model):
    _name = "erc.intercompany.country.profile"
    _inherit = ["mail.thread"]
    _description = "Intercompany Country Account Seed Profile"
    _order = "country_id"

    country_id = fields.Many2one(
        "res.country",
        required=True,
        ondelete="cascade",
        index=True,
        tracking=True,
    )
    receivable_seed_code = fields.Char(required=True, tracking=True)
    payable_seed_code = fields.Char(required=True, tracking=True)
    income_production_seed_code = fields.Char(required=True, tracking=True)
    income_resale_seed_code = fields.Char(tracking=True)
    income_service_seed_code = fields.Char(required=True, tracking=True)
    expense_service_seed_code = fields.Char(required=True, tracking=True)
    expense_other_seed_code = fields.Char(required=True, tracking=True)

    _sql_constraints = [
        (
            "country_unique",
            "unique(country_id)",
            "An intercompany country profile already exists for this country.",
        ),
    ]
