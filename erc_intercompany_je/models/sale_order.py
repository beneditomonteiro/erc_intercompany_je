# -*- coding: utf-8 -*-
# License OPL-1 (Odoo Proprietary License v1.0) - (c) 2026 ERC Implementors LTDA

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_intercompany_journal_display = fields.Boolean(
        related="company_id.is_intercompany_journal_display"
    )

    def _get_intercompany_sale_journal(self):
        """Determine the correct IC sale journal based on order line content.

        All services → ISS journal.
        All goods → ICS journal.
        Mixed → raise UserError.
        No lines yet → False (no default).
        """
        self.ensure_one()
        company = self.company_id
        if not self.partner_id or not self.partner_id.is_intercompany:
            return False
        product_lines = self.order_line.filtered(
            lambda l: not l.display_type and not l.is_downpayment and l.product_id
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
                    "- One for services (→ journal ISS)\n"
                    "- One for goods/products (→ journal ICS)"
                )
            )
        if has_services:
            return (
                company.interco_service_sale_journal_id
                or company.interco_sale_journal_id
            )
        return company.interco_sale_journal_id

    def _recompute_intercompany_journal(self):
        """Re-evaluate IC journal based on current line content."""
        for order in self:
            if not order.partner_id or not order.partner_id.is_intercompany:
                continue
            journal = order._get_intercompany_sale_journal()
            if journal:
                order.journal_id = journal

    @api.depends(
        "company_id",
        "partner_id",
        "partner_id.is_intercompany",
        "partner_id.sale_intercompany_journal_id",
    )
    def _compute_journal_id(self):
        super()._compute_journal_id()
        for order in self:
            if not order.partner_id.is_intercompany:
                continue
            product_lines = order.order_line.filtered(
                lambda l: not l.display_type and not l.is_downpayment and l.product_id
            )
            if not product_lines:
                continue
            journal = order._get_intercompany_sale_journal()
            if journal and journal.company_id == order.company_id:
                order.journal_id = journal

    @api.onchange("partner_id")
    def _onchange_partner_id_intercompany_journal(self):
        """IC partner selected — do NOT set a default journal.
        Journal is determined by line content (service vs goods)."""
        pass

    @api.onchange("order_line")
    def _onchange_order_line_intercompany_journal(self):
        """When lines change, select ISS or ICS based on product type."""
        self._recompute_intercompany_journal()

    def _prepare_invoice(self):
        """Override to set the correct IC sale journal based on line content."""
        res = super()._prepare_invoice()
        if self.partner_id and self.partner_id.is_intercompany:
            journal = self._get_intercompany_sale_journal()
            if journal:
                res["journal_id"] = journal.id
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _is_manufactured_product(self):
        self.ensure_one()
        product = self.product_id
        if not product or product.type == "service":
            return False
        if "mrp.bom" in self.env:
            bom = self.env["mrp.bom"].sudo().search(
                [
                    ("company_id", "in", [False, self.order_id.company_id.id]),
                    "|",
                    ("product_id", "=", product.id),
                    ("product_tmpl_id", "=", product.product_tmpl_id.id),
                ],
                limit=1,
            )
            if bom:
                return True
        routes = product.route_ids | product.categ_id.total_route_ids
        return any("manufact" in (route.name or "").lower() for route in routes)

    def _get_intercompany_income_account(self):
        self.ensure_one()
        company = self.order_id.company_id
        if self.product_id and self.product_id.type == "service":
            return company.interco_income_service_account_id
        if company.intercompany_bom_production_account and self._is_manufactured_product():
            journal = company.interco_sale_journal_id
            if journal and journal.intercompany_production_account_id:
                return journal.intercompany_production_account_id
            return (
                company.interco_income_production_account_id
                or company.interco_income_resale_account_id
                or company.interco_income_service_account_id
            )
        return (
            company.interco_income_resale_account_id
            or company.interco_income_production_account_id
            or company.interco_income_service_account_id
        )

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        order = self.order_id
        if (
            order.partner_id
            and order.partner_id.is_intercompany
            and not self.display_type
            and not self.is_downpayment
        ):
            interco_account = self._get_intercompany_income_account()
            if interco_account:
                res["account_id"] = interco_account.id
            elif order.company_id.intercompany_enforce_accounts:
                raise UserError(
                    _(
                        "Missing intercompany revenue account configuration. "
                        "Configure Production/Resale/Service intercompany accounts in Settings."
                    )
                )
        return res
