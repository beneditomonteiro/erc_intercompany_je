# -*- coding: utf-8 -*-
# License OPL-1 (Odoo Proprietary License v1.0) - (c) 2026 ERC Implementors LTDA

from odoo import _, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_expected_ic_journal(self):
        """Return expected IC journal, or False if not deterministic."""
        self.ensure_one()
        if not self.partner_id or not self.partner_id.is_intercompany:
            return False
        lines = self.invoice_line_ids.filtered(
            lambda l: not l.display_type and l.product_id
        )
        if not lines:
            return False
        has_services = any(l.product_id.type == "service" for l in lines)
        has_goods = any(l.product_id.type != "service" for l in lines)
        if has_services and has_goods:
            return False  # mixed: skip
        company = self.company_id
        if self.move_type in ("out_invoice", "out_refund"):
            if has_services:
                return (
                    company.interco_service_sale_journal_id
                    or company.interco_sale_journal_id
                )
            return company.interco_sale_journal_id
        if self.move_type in ("in_invoice", "in_refund"):
            if has_services:
                return (
                    company.interco_service_expense_journal_id
                    or company.interco_purchase_journal_id
                )
            return company.interco_purchase_journal_id
        return False

    def _check_ic_journal_alignment(self):
        """Post chatter warning on mismatch. Never blocks posting."""
        for move in self:
            if not move.partner_id or not move.partner_id.is_intercompany:
                continue
            expected = move._get_expected_ic_journal()
            if not expected or not move.journal_id or move.journal_id.id == expected.id:
                continue
            move.message_post(
                body=_(
                    "Journal mismatch: invoice uses <b>%(actual)s</b> "
                    "but IC configuration expects <b>%(expected)s</b>. "
                    "Posting was not blocked.",
                    actual=move.journal_id.display_name,
                    expected=expected.display_name,
                ),
                message_type="comment",
                subtype_xmlid="mail.mt_note",
            )

    def action_post(self):
        res = super().action_post()
        self._check_ic_journal_alignment()
        return res
