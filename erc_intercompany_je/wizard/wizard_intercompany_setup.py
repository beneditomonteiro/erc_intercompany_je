# -*- coding: utf-8 -*-
# License OPL-1 (Odoo Proprietary License v1.0) - (c) 2026 ERC Implementors LTDA

from odoo import _, api, fields, models


class WizardIntercompanySetup(models.TransientModel):
    _name = "wizard.intercompany.setup"
    _description = "Batch Intercompany Account Setup"

    company_ids = fields.Many2many(
        "res.company",
        string="Companies",
        default=lambda self: self.env.company._get_same_group_companies(),
    )
    force_realign = fields.Boolean(
        string="Force Re-alignment",
        help="Re-run setup even on companies that are already fully configured.",
    )
    preview_text = fields.Text(
        string="Preview",
        compute="_compute_preview_text",
    )

    @api.depends("company_ids", "force_realign")
    def _compute_preview_text(self):
        for wiz in self:
            lines = []
            for company in wiz.company_ids:
                errors = company._validate_before_setup()
                if errors:
                    lines.append(
                        _("%(company)s — BLOCKED: %(errors)s",
                          company=company.display_name,
                          errors="; ".join(errors))
                    )
                    continue
                status = company.interco_setup_status
                if status == "complete" and not wiz.force_realign:
                    lines.append(
                        _("%(company)s — Already complete (skipped)",
                          company=company.display_name)
                    )
                else:
                    proposals = company.get_intercompany_account_proposal()
                    count = len([p for p in proposals if p.get("status") != "configured"])
                    lines.append(
                        _("%(company)s — %(count)s account(s) to create/link",
                          company=company.display_name,
                          count=count)
                    )
            wiz.preview_text = "\n".join(lines) if lines else _("No companies selected.")

    def action_run_setup(self):
        self.ensure_one()
        results = []
        for company in self.company_ids:
            errors = company._validate_before_setup()
            if errors:
                results.append(
                    _("%(company)s — SKIPPED: %(errors)s",
                      company=company.display_name,
                      errors="; ".join(errors))
                )
                continue
            if company.interco_setup_status == "complete" and not self.force_realign:
                results.append(
                    _("%(company)s — Already complete (skipped)",
                      company=company.display_name)
                )
                continue
            company.action_setup_intercompany_accounts()
            results.append(
                _("%(company)s — Setup executed",
                  company=company.display_name)
            )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Batch Intercompany Setup"),
                "message": "\n".join(results),
                "type": "success",
                "sticky": True,
            },
        }
