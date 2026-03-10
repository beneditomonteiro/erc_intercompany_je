# -*- coding: utf-8 -*-
# License OPL-1 (Odoo Proprietary License v1.0) - (c) 2026 ERC Implementors LTDA

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_intercompany = fields.Boolean(string="Intercompany", copy=False)
    sale_intercompany_journal_id = fields.Many2one(
        "account.journal",
        domain=[("type", "=", "sale")],
    )
    purchase_intercompany_journal_id = fields.Many2one(
        "account.journal",
        domain=[("type", "=", "purchase")],
    )
    intercompany_receivable_account_id = fields.Many2one(
        "account.account",
        string="Intercompany Receivable Account",
        domain="[('account_type', '=', 'asset_receivable')]",
        copy=False,
    )
    intercompany_payable_account_id = fields.Many2one(
        "account.account",
        string="Intercompany Payable Account",
        domain="[('account_type', '=', 'liability_payable')]",
        copy=False,
    )

    def _check_company(self, fnames=None):
        """Allow IC accounts on shared partners (company_id=False).

        When a partner is flagged as intercompany, its AR/AP property
        accounts intentionally belong to a specific company.  Odoo core
        raises a UserError because the partner itself has no company_id.
        We skip that check when the write originates from our IC sync.
        """
        if self.env.context.get("skip_intercompany_company_check"):
            ic_fields = {
                "property_account_receivable_id",
                "property_account_payable_id",
            }
            if fnames is not None:
                fnames = [f for f in fnames if f not in ic_fields]
                if not fnames:
                    return
            else:
                fnames = [
                    f for f in self._fields
                    if f not in ic_fields
                ]
        return super()._check_company(fnames=fnames)

    def _apply_intercompany_partner_accounts(self):
        if self.env.context.get("skip_intercompany_partner_account_sync"):
            return
        company = self.env.company
        for partner in self.filtered("is_intercompany"):
            partner_in_company = partner.with_company(company)
            partner_vals = {}
            if (
                company.interco_sale_journal_id
                and not partner.sale_intercompany_journal_id
            ):
                partner_vals["sale_intercompany_journal_id"] = (
                    company.interco_sale_journal_id.id
                )
            if (
                company.interco_purchase_journal_id
                and not partner.purchase_intercompany_journal_id
            ):
                partner_vals["purchase_intercompany_journal_id"] = (
                    company.interco_purchase_journal_id.id
                )
            receivable = (
                partner.intercompany_receivable_account_id
                or company.interco_receivable_account_id
            )
            payable = (
                partner.intercompany_payable_account_id
                or company.interco_payable_account_id
            )
            company_vals = {}
            if (
                receivable
                and partner_in_company.property_account_receivable_id != receivable
            ):
                company_vals["property_account_receivable_id"] = receivable.id
            if payable and partner_in_company.property_account_payable_id != payable:
                company_vals["property_account_payable_id"] = payable.id
            if partner_vals:
                partner.with_context(
                    skip_intercompany_partner_account_sync=True
                ).write(partner_vals)
            if company_vals:
                partner_in_company.with_context(
                    skip_intercompany_partner_account_sync=True,
                    skip_intercompany_company_check=True,
                ).write(company_vals)

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        partners._apply_intercompany_partner_accounts()
        return partners

    def write(self, vals):
        res = super().write(vals)
        if {
            "is_intercompany",
            "intercompany_receivable_account_id",
            "intercompany_payable_account_id",
            "sale_intercompany_journal_id",
            "purchase_intercompany_journal_id",
        } & set(vals):
            self._apply_intercompany_partner_accounts()
        return res

    @api.onchange("is_intercompany")
    def _onchange_is_intercompany(self):
        for partner in self:
            if not partner.is_intercompany:
                partner.sale_intercompany_journal_id = (
                    partner.purchase_intercompany_journal_id
                ) = False
            else:
                company = self.env.company
                partner.sale_intercompany_journal_id = (
                    partner.sale_intercompany_journal_id
                    or company.interco_sale_journal_id
                )
                partner.purchase_intercompany_journal_id = (
                    partner.purchase_intercompany_journal_id
                    or company.interco_purchase_journal_id
                )
                partner.intercompany_receivable_account_id = (
                    partner.intercompany_receivable_account_id
                    or company.interco_receivable_account_id
                )
                partner.intercompany_payable_account_id = (
                    partner.intercompany_payable_account_id
                    or company.interco_payable_account_id
                )



class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    is_intercompany_journal_display = fields.Boolean(
        related="company_id.is_intercompany_journal_display",
        string="Is Inter Company Journal Display",
        readonly=False,
    )


class Company(models.Model):
    _inherit = "res.company"

    is_intercompany_journal_display = fields.Boolean("Is Inter Company Journal Display")
