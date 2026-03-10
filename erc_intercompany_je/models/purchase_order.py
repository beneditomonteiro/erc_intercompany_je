# -*- coding: utf-8 -*-
# License OPL-1 (Odoo Proprietary License v1.0) - (c) 2026 ERC Implementors LTDA

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    journal_id = fields.Many2one(
        "account.journal",
        domain=[("type", "=", "purchase")],
        check_company=True,
    )
    is_intercompany_journal_display = fields.Boolean(
        related="company_id.is_intercompany_journal_display"
    )

    def _get_intercompany_purchase_journal(self):
        """Determine the correct IC purchase journal based on order line content.

        All services → ICE journal.
        All goods → ICP journal.
        Mixed → raise UserError.
        No lines yet → False (no default).
        """
        self.ensure_one()
        company = self.company_id
        if not self.partner_id or not self.partner_id.is_intercompany:
            return False
        product_lines = self.order_line.filtered(
            lambda l: not l.display_type and l.product_id
        )
        if not product_lines:
            return False
        has_services = any(l.product_id.type == "service" for l in product_lines)
        has_goods = any(l.product_id.type != "service" for l in product_lines)
        if has_services and has_goods:
            raise UserError(
                _(
                    "Intercompany orders cannot mix services and goods.\n\n"
                    "Please create separate orders:\n"
                    "- One for services (→ journal ICE)\n"
                    "- One for goods/products (→ journal ICP)"
                )
            )
        if has_services:
            return (
                company.interco_service_expense_journal_id
                or company.interco_purchase_journal_id
            )
        return company.interco_purchase_journal_id

    def _recompute_intercompany_journal(self):
        """Re-evaluate IC journal based on current line content."""
        for order in self:
            if not order.partner_id or not order.partner_id.is_intercompany:
                continue
            journal = order._get_intercompany_purchase_journal()
            if journal:
                order.journal_id = journal

    @api.onchange("partner_id")
    def _onchange_partner_id_intercompany_journal(self):
        """IC partner selected — do NOT set a default journal.
        Journal is determined by line content (service vs goods)."""
        pass

    @api.onchange("order_line")
    def _onchange_order_line_intercompany_journal(self):
        """When lines change, select ICE or ICP based on product type."""
        self._recompute_intercompany_journal()

    def _prepare_invoice(self):
        self.ensure_one()
        res = super()._prepare_invoice()
        if self.partner_id and self.partner_id.is_intercompany:
            journal = (
                self._get_intercompany_purchase_journal()
                or self.journal_id
            )
            if journal:
                res["journal_id"] = journal.id
        return res

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        for order in orders.filtered(
            lambda o: o.partner_id and o.partner_id.is_intercompany and not o.journal_id
        ):
            journal = order._get_intercompany_purchase_journal()
            if journal:
                order.journal_id = journal
        return orders


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _get_intercompany_expense_account(self):
        """Route purchase line to the correct IC expense/cost account.

        Services → Services Expenses Intercompany (65350001)
        Goods/Products (storable or consumable) → Cost of Goods Sold Intercompany (50000001)
        """
        self.ensure_one()
        company = self.order_id.company_id
        if self.product_id and self.product_id.type == "service":
            return company.interco_expense_service_account_id
        if self.product_id:
            return (
                company.interco_expense_other_account_id
                or company.interco_expense_service_account_id
            )
        return False

    def _prepare_account_move_line(self, move=False):
        res = super()._prepare_account_move_line(move=move)
        order = self.order_id
        if (
            order.partner_id
            and order.partner_id.is_intercompany
            and not self.display_type
            and self.product_id
        ):
            interco_account = self._get_intercompany_expense_account()
            if interco_account:
                res["account_id"] = interco_account.id
            elif order.company_id.intercompany_enforce_accounts:
                raise UserError(
                    _(
                        "Missing intercompany cost/expense account configuration. "
                        "Configure COGS and Service Expense intercompany accounts in Settings."
                    )
                )
        return res
