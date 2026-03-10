# -*- coding: utf-8 -*-
# License OPL-1 (Odoo Proprietary License v1.0) - (c) 2026 ERC Implementors LTDA

import re
from collections import Counter
import logging

from odoo import _, api, fields, models
from odoo.fields import Command

_logger = logging.getLogger(__name__)
DEFAULT_REQUIRED_INTERCOMPANY_MODULE = "account_inter_company_rules"
PARAM_REQUIRED_INTERCOMPANY_MODULE = (
    "erc_intercompany_je.required_intercompany_module"
)
PARAM_REQUIRE_RULES_RUNTIME = "erc_intercompany_je.require_rules_runtime"


class Company(models.Model):
    _inherit = "res.company"

    interco_income_production_account_id = fields.Many2one(
        "account.account",
        string="Intercompany Production Revenue Account",
        domain="[('account_type', 'in', ('income', 'income_other'))]",
        check_company=True,
    )
    interco_income_resale_account_id = fields.Many2one(
        "account.account",
        string="Intercompany Resale Revenue Account",
        domain="[('account_type', 'in', ('income', 'income_other'))]",
        check_company=True,
    )
    interco_income_service_account_id = fields.Many2one(
        "account.account",
        string="Intercompany Service Revenue Account",
        domain="[('account_type', 'in', ('income', 'income_other'))]",
        check_company=True,
    )
    interco_expense_service_account_id = fields.Many2one(
        "account.account",
        string="Intercompany Service Expense Account",
        domain="[('account_type', 'in', ('expense', 'expense_other', 'expense_direct_cost'))]",
        check_company=True,
    )
    interco_expense_other_account_id = fields.Many2one(
        "account.account",
        string="Intercompany Cost of Goods Sold Account",
        domain="[('account_type', 'in', ('expense', 'expense_other', 'expense_direct_cost'))]",
        check_company=True,
    )
    interco_receivable_account_id = fields.Many2one(
        "account.account",
        string="Intercompany Receivable Account",
        domain="[('account_type', '=', 'asset_receivable')]",
        check_company=True,
    )
    interco_payable_account_id = fields.Many2one(
        "account.account",
        string="Intercompany Payable Account",
        domain="[('account_type', '=', 'liability_payable')]",
        check_company=True,
    )
    interco_sale_journal_id = fields.Many2one(
        "account.journal",
        string="Intercompany Sale Journal",
        domain="[('type', '=', 'sale')]",
        check_company=True,
    )
    interco_service_sale_journal_id = fields.Many2one(
        "account.journal",
        string="Intercompany Services Sales Journal",
        domain="[('type', '=', 'sale')]",
        check_company=True,
    )
    interco_purchase_journal_id = fields.Many2one(
        "account.journal",
        string="Intercompany Purchase Journal",
        domain="[('type', '=', 'purchase')]",
        check_company=True,
    )
    interco_service_expense_journal_id = fields.Many2one(
        "account.journal",
        string="Intercompany Services Expenses Journal",
        domain="[('type', '=', 'purchase')]",
        check_company=True,
    )
    intercompany_enforce_accounts = fields.Boolean(
        string="Enforce Intercompany Account Segregation",
        default=True,
        help="When enabled, invoice/bill preparation for intercompany partners blocks if "
        "required intercompany accounts are missing.",
    )
    intercompany_sync_partner_accounts = fields.Boolean(
        string="Sync Intercompany Partners AR/AP",
        default=True,
        help="When enabled, the setup process updates existing intercompany partners to use "
        "the dedicated intercompany receivable/payable accounts.",
    )
    intercompany_bom_production_account = fields.Boolean(
        string="BOM Products Use Production Revenue Account",
        default=True,
        help="When enabled, goods with a Bill of Materials (BOM) will use the "
        "Production Sales Intercompany account (e.g. 40000001) as the income "
        "account on intercompany invoices, even though the journal remains ICS. "
        "When disabled, all goods use the Resale account regardless of BOM.",
    )

    def _get_required_intercompany_module_name(self):
        module_name = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(PARAM_REQUIRED_INTERCOMPANY_MODULE)
        )
        module_name = (module_name or "").strip()
        return module_name or DEFAULT_REQUIRED_INTERCOMPANY_MODULE

    def _is_intercompany_rules_module_available(self):
        if not self._is_backend_param_enabled(PARAM_REQUIRE_RULES_RUNTIME, True):
            return True
        module_name = self._get_required_intercompany_module_name()
        if not module_name:
            return True
        module = self.env["ir.module.module"].sudo().search(
            [("name", "=", module_name)],
            limit=1,
        )
        return bool(module and module.state in {"installed", "to install", "to upgrade"})

    def _intercompany_rules_missing_notification(self, title):
        module_name = self._get_required_intercompany_module_name()
        message = _(
            "Install prerequisite module '%s' first. "
            "ERC Intercompany JE requires Intercompany Rules to run this workflow.",
            module_name,
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": title,
                "message": message,
                "type": "warning",
                "sticky": True,
            },
        }

    def _get_intercompany_labels(self):
        self.ensure_one()
        labels = {
            "interco_income_production_account_id": _("Production Sales Intercompany"),
            "interco_income_resale_account_id": _("Resale Sales Intercompany"),
            "interco_income_service_account_id": _("Services Sales Intercompany"),
            "interco_expense_service_account_id": _("Services Expenses Intercompany"),
            "interco_expense_other_account_id": _("Cost of Goods Sold Intercompany"),
            "interco_receivable_account_id": _("Intercompany Receivable"),
            "interco_payable_account_id": _("Intercompany Payable"),
        }
        country_code = (
            (self.account_fiscal_country_id or self.country_id).code
            if (self.account_fiscal_country_id or self.country_id)
            else ""
        )
        if (country_code or "").upper() in {"BR", "AO", "PT"}:
            labels.update(
                {
                    "interco_income_production_account_id": _("Venda de Produção Intercompany"),
                    "interco_income_resale_account_id": _("Venda de Mercadorias Intercompany"),
                    "interco_income_service_account_id": _("Venda de Serviços Intercompany"),
                    "interco_expense_service_account_id": _("Despesas de Serviços Intercompany"),
                    "interco_expense_other_account_id": _("Custo das Mercadorias Vendidas Intercompany"),
                    "interco_receivable_account_id": _("Clientes Intercompany"),
                    "interco_payable_account_id": _("Fornecedores Intercompany"),
                }
            )
        return labels

    def _intercompany_account_specs(self):
        labels = self._get_intercompany_labels()
        return (
            {
                "field_name": "interco_income_production_account_id",
                "label": labels["interco_income_production_account_id"],
                "account_types": ("income", "income_other"),
                "keywords": ("sale", "revenue", "goods", "product", "production"),
                "fallback_prefix": "7",
                "target_type": "income",
                "reconcile": False,
            },
            {
                "field_name": "interco_income_resale_account_id",
                "label": labels["interco_income_resale_account_id"],
                "account_types": ("income", "income_other"),
                "keywords": ("sale", "revenue", "resale", "merchandise", "trade"),
                "fallback_prefix": "7",
                "target_type": "income",
                "reconcile": False,
            },
            {
                "field_name": "interco_income_service_account_id",
                "label": labels["interco_income_service_account_id"],
                "account_types": ("income", "income_other"),
                "keywords": ("sale", "revenue", "service"),
                "fallback_prefix": "7",
                "target_type": "income",
                "reconcile": False,
            },
            {
                "field_name": "interco_expense_service_account_id",
                "label": labels["interco_expense_service_account_id"],
                "account_types": ("expense", "expense_other", "expense_direct_cost"),
                "keywords": ("expense", "service", "cost"),
                "fallback_prefix": "6",
                "target_type": "expense",
                "reconcile": False,
            },
            {
                "field_name": "interco_expense_other_account_id",
                "label": labels["interco_expense_other_account_id"],
                "account_types": ("expense", "expense_other", "expense_direct_cost"),
                "keywords": ("cost", "goods", "sold", "cogs", "merchandise"),
                "fallback_prefix": "5",
                "target_type": "expense_direct_cost",
                "reconcile": False,
            },
            {
                "field_name": "interco_receivable_account_id",
                "label": labels["interco_receivable_account_id"],
                "account_types": ("asset_receivable",),
                "keywords": ("receivable", "trade debtors", "customer"),
                "fallback_prefix": "1",
                "target_type": "asset_receivable",
                "reconcile": True,
            },
            {
                "field_name": "interco_payable_account_id",
                "label": labels["interco_payable_account_id"],
                "account_types": ("liability_payable",),
                "keywords": ("payable", "trade creditors", "supplier"),
                "fallback_prefix": "2",
                "target_type": "liability_payable",
                "reconcile": True,
            },
        )

    def _resolve_target_type(self, company, spec, seed_code):
        target_type = spec["target_type"]
        if spec["field_name"] != "interco_expense_other_account_id":
            return target_type
        if not seed_code:
            return target_type
        account_model = (
            self.env["account.account"]
            .with_context(active_test=False)
            .with_company(company)
        )
        seed_match = account_model.search(
            [
                ("company_ids", "in", company.id),
                ("code", "=", seed_code),
                ("account_type", "in", list(spec["account_types"])),
            ],
            limit=1,
        )
        if seed_match:
            return seed_match.account_type
        if "." in seed_code:
            like_pattern = f"{seed_code}.%"
        else:
            like_pattern = f"{seed_code}%"
        family_match = account_model.search(
            [
                ("company_ids", "in", company.id),
                ("code", "like", like_pattern),
                ("account_type", "in", list(spec["account_types"])),
            ],
            order="code",
            limit=1,
        )
        if family_match:
            return family_match.account_type
        return target_type

    def _generate_seed_child_code(self, seed_code, existing_codes):
        seed_code = (seed_code or "").strip()
        if not seed_code:
            return False
        if "." in seed_code:
            for index in range(1, 1000):
                candidate = f"{seed_code}.{index:02d}"
                if candidate not in existing_codes and len(candidate) <= 64:
                    return candidate
            return False
        if seed_code.isdigit():
            for index in range(1, 1000):
                candidate = f"{seed_code}{index:02d}"
                if candidate not in existing_codes and len(candidate) <= 64:
                    return candidate
            return False
        for index in range(1, 1000):
            candidate = f"{seed_code}.{index:02d}"
            if candidate not in existing_codes and len(candidate) <= 64:
                return candidate
        return False

    def _get_effective_seed_code(self, seed_code, template):
        explicit_seed = (seed_code or "").strip()
        if explicit_seed:
            return explicit_seed
        if template and template.code:
            return (template.code or "").strip()
        return ""

    def _country_profile_field_map(self):
        return {
            "interco_receivable_account_id": "receivable_seed_code",
            "interco_payable_account_id": "payable_seed_code",
            "interco_income_production_account_id": "income_production_seed_code",
            "interco_income_resale_account_id": "income_resale_seed_code",
            "interco_income_service_account_id": "income_service_seed_code",
            "interco_expense_service_account_id": "expense_service_seed_code",
            "interco_expense_other_account_id": "expense_other_seed_code",
        }

    def _get_intercompany_country_profile(self):
        self.ensure_one()
        country = self.account_fiscal_country_id or self.country_id
        if not country:
            return self.env["erc.intercompany.country.profile"]
        return self.env["erc.intercompany.country.profile"].sudo().search(
            [("country_id", "=", country.id)],
            limit=1,
        )

    def _get_country_seed_codes(self):
        self.ensure_one()
        country = self.account_fiscal_country_id or self.country_id
        country_code = (country.code or "").upper() if country else ""
        profile = self._get_intercompany_country_profile()
        if not profile:
            seeds = {}
        else:
            field_map = self._country_profile_field_map()
            seeds = {
                field_name: (profile[profile_field] or "").strip()
                for field_name, profile_field in field_map.items()
            }
        # Keep BR sequencing consistent across upgrades with per-COA branches.
        if country_code == "BR":
            seeds.update(self._get_br_seed_codes_by_coa())
        return seeds

    def _guess_br_coa_template(self):
        self.ensure_one()
        company = self
        chart_template = ""
        if "chart_template" in company._fields:
            chart_template = (company.chart_template or "").strip()
        if chart_template in {"br_meepp", "br_generic", "br"}:
            return chart_template

        account_model = self.env["account.account"].with_company(company)
        # Fingerprints from known BR templates.
        if account_model.search_count(
            [
                ("company_ids", "in", company.id),
                ("code", "=", "3.01.01.01.10.01"),
            ]
        ):
            return "br_generic"
        if account_model.search_count(
            [
                ("company_ids", "in", company.id),
                ("code", "=", "3.01.01.01.01.04"),
            ]
        ):
            return "br"
        return "br_meepp"

    def _get_br_seed_codes_by_coa(self):
        self.ensure_one()
        coa_template = self._guess_br_coa_template()
        seed_map = {
            # MEEPP (4-level COA)
            "br_meepp": {
                "interco_receivable_account_id": "1.01.02.01",
                "interco_payable_account_id": "2.01.01.01",
                "interco_income_production_account_id": "3.01.01.01",
                "interco_income_resale_account_id": "3.01.01.02",
                "interco_income_service_account_id": "3.01.01.03",
                "interco_expense_service_account_id": "3.02.01.01",
                "interco_expense_other_account_id": "3.02.01.01",
            },
            # Generic (6-level COA)
            "br_generic": {
                "interco_receivable_account_id": "1.01.02.01",
                "interco_payable_account_id": "2.01.01.01.01",
                "interco_income_production_account_id": "3.01.01.01.10",
                "interco_income_resale_account_id": "3.01.01.01.01",
                "interco_income_service_account_id": "3.01.01.01.20",
                "interco_expense_service_account_id": "3.02.01.01.03",
                "interco_expense_other_account_id": "3.02.01.04",
            },
            # Official Odoo/Akretion BR template.
            "br": {
                "interco_receivable_account_id": "1.01.01.04",
                "interco_payable_account_id": "2.01.01.03",
                "interco_income_production_account_id": "3.01.01.01.01.04",
                "interco_income_resale_account_id": "3.01.01.01.01.05",
                "interco_income_service_account_id": "3.01.01.01.01.06",
                "interco_expense_service_account_id": "3.01.01.03.01.03",
                "interco_expense_other_account_id": "3.01.01.09.01.99",
            },
        }
        return seed_map.get(coa_template, seed_map["br_meepp"])

    def _next_intercompany_journal_code(self, company, base_code):
        journal_model = (
            self.env["account.journal"]
            .with_context(active_test=False)
            .with_company(company)
        )
        used_codes = set(
            journal_model.search([("company_id", "=", company.id)]).mapped("code")
        )
        base_code = (base_code or "IC").upper()[:5]
        if base_code not in used_codes:
            return base_code
        for index in range(1, 1000):
            suffix = str(index)
            head = base_code[: max(1, 5 - len(suffix))]
            candidate = f"{head}{suffix}"[:5]
            if candidate not in used_codes:
                return candidate
        return f"I{company.id}"[:5]

    def _is_backend_param_enabled(self, key, default=True):
        value = self.env["ir.config_parameter"].sudo().get_param(key)
        if value in (None, ""):
            return default
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    def _get_reference_journal_use_documents(self, company, journal_type):
        journal_model = self.env["account.journal"].with_company(company)
        if "l10n_latam_use_documents" not in journal_model._fields:
            return None
        if self._is_backend_param_enabled(
            "erc_intercompany_je.journal_force_use_documents", True
        ):
            localization_support = (
                hasattr(company, "_localization_use_documents")
                and company._localization_use_documents()
            )
            if localization_support and journal_type in ("sale", "purchase"):
                return True
        if not self._is_backend_param_enabled(
            "erc_intercompany_je.journal_mirror_use_documents", True
        ):
            return None
        reference = journal_model.search(
            [
                ("company_id", "=", company.id),
                ("type", "=", journal_type),
                ("name", "not ilike", "intercompany"),
            ],
            order="sequence, id",
            limit=1,
        )
        if reference:
            return bool(reference.l10n_latam_use_documents)
        return False

    def _prepare_intercompany_journal_config(self, company, journal, journal_type):
        vals = {}
        current_default = journal.default_account_id
        apply_defaults = self._is_backend_param_enabled(
            "erc_intercompany_je.journal_autofill_defaults", True
        )

        if journal_type == "sale" and apply_defaults:
            target_default = (
                self.interco_income_resale_account_id
                or self.interco_income_production_account_id
                or self.interco_income_service_account_id
            )
            if target_default and (
                not current_default
                or current_default.id != target_default.id
            ):
                vals["default_account_id"] = target_default.id
            production_acct = self.interco_income_production_account_id
            current_prod = journal.intercompany_production_account_id
            if production_acct and (
                not current_prod or current_prod.id != production_acct.id
            ):
                vals["intercompany_production_account_id"] = production_acct.id
        elif journal_type == "service_sale" and apply_defaults:
            target_default = self.interco_income_service_account_id
            if target_default and (
                not current_default
                or current_default.id != target_default.id
            ):
                vals["default_account_id"] = target_default.id
        elif journal_type == "purchase" and apply_defaults:
            target_default = (
                self.interco_expense_other_account_id
                or self.interco_expense_service_account_id
            )
            if target_default and (
                not current_default
                or current_default.id != target_default.id
            ):
                vals["default_account_id"] = target_default.id
        elif journal_type == "service_expense" and apply_defaults:
            target_default = self.interco_expense_service_account_id
            if target_default and (
                not current_default
                or current_default.id != target_default.id
            ):
                vals["default_account_id"] = target_default.id

        ref_type_map = {"service_expense": "purchase", "service_sale": "sale"}
        ref_type = ref_type_map.get(journal_type, journal_type)
        use_documents = self._get_reference_journal_use_documents(company, ref_type)
        if (
            use_documents is not None
            and journal.l10n_latam_use_documents != use_documents
        ):
            vals["l10n_latam_use_documents"] = use_documents

        return vals

    def _prepare_intercompany_journal_sequence_controls(self, journal):
        if not self._is_backend_param_enabled(
            "erc_intercompany_je.journal_control_sequence", True
        ):
            return {}
        vals = {}
        if "refund_sequence" in journal._fields and not journal.refund_sequence:
            vals["refund_sequence"] = True
        if "debit_sequence" in journal._fields and not journal.debit_sequence:
            vals["debit_sequence"] = True
        return vals

    def _ensure_intercompany_journals(self):
        self.ensure_one()
        company = self
        journal_model = self.env["account.journal"].with_company(company)

        created = []
        linked = []
        configured = set()
        updates = {}

        sale_journal = self.interco_sale_journal_id
        if not sale_journal:
            sale_journal = journal_model.search(
                [
                    ("company_id", "=", company.id),
                    ("type", "=", "sale"),
                    ("name", "ilike", "intercompany"),
                    ("name", "not ilike", "service"),
                ],
                order="id",
                limit=1,
            )
            if sale_journal:
                linked.append(sale_journal.display_name)
            else:
                sale_journal = journal_model.create(
                    {
                        "name": _("Intercompany Sales"),
                        "type": "sale",
                        "code": self._next_intercompany_journal_code(company, "ICS"),
                        "company_id": company.id,
                    }
                )
                created.append(sale_journal.display_name)
            updates["interco_sale_journal_id"] = sale_journal.id

        service_sale_journal = self.interco_service_sale_journal_id
        if not service_sale_journal:
            service_sale_journal = journal_model.search(
                [
                    ("company_id", "=", company.id),
                    ("type", "=", "sale"),
                    ("name", "ilike", "intercompany"),
                    ("name", "ilike", "service"),
                ],
                order="id",
                limit=1,
            )
            if service_sale_journal:
                linked.append(service_sale_journal.display_name)
            else:
                service_sale_journal = journal_model.create(
                    {
                        "name": _("Intercompany Services Sales"),
                        "type": "sale",
                        "code": self._next_intercompany_journal_code(company, "ISS"),
                        "company_id": company.id,
                    }
                )
                created.append(service_sale_journal.display_name)
            updates["interco_service_sale_journal_id"] = service_sale_journal.id

        purchase_journal = self.interco_purchase_journal_id
        if not purchase_journal:
            purchase_journal = journal_model.search(
                [
                    ("company_id", "=", company.id),
                    ("type", "=", "purchase"),
                    ("name", "ilike", "intercompany"),
                    ("name", "not ilike", "service"),
                ],
                order="id",
                limit=1,
            )
            if purchase_journal:
                linked.append(purchase_journal.display_name)
            else:
                purchase_journal = journal_model.create(
                    {
                        "name": _("Intercompany Purchases"),
                        "type": "purchase",
                        "code": self._next_intercompany_journal_code(company, "ICP"),
                        "company_id": company.id,
                    }
                )
                created.append(purchase_journal.display_name)
            updates["interco_purchase_journal_id"] = purchase_journal.id

        service_expense_journal = self.interco_service_expense_journal_id
        if not service_expense_journal:
            service_expense_journal = journal_model.search(
                [
                    ("company_id", "=", company.id),
                    ("type", "=", "purchase"),
                    ("name", "ilike", "intercompany"),
                    ("name", "ilike", "service"),
                ],
                order="id",
                limit=1,
            )
            if service_expense_journal:
                linked.append(service_expense_journal.display_name)
            else:
                service_expense_journal = journal_model.create(
                    {
                        "name": _("Intercompany Services Expenses"),
                        "type": "purchase",
                        "code": self._next_intercompany_journal_code(company, "ICE"),
                        "company_id": company.id,
                    }
                )
                created.append(service_expense_journal.display_name)
            updates["interco_service_expense_journal_id"] = service_expense_journal.id

        if updates:
            self.write(updates)

        journal_configs = [
            (sale_journal, "sale"),
            (service_sale_journal, "service_sale"),
            (purchase_journal, "purchase"),
            (service_expense_journal, "service_expense"),
        ]
        for jnl, jtype in journal_configs:
            jnl_vals = self._prepare_intercompany_journal_config(company, jnl, jtype)
            if jnl_vals:
                jnl.write(jnl_vals)
                configured.add(jnl.display_name)
            seq_vals = self._prepare_intercompany_journal_sequence_controls(jnl)
            if seq_vals:
                jnl.write(seq_vals)
                configured.add(jnl.display_name)

        return {
            "created": created,
            "linked": linked,
            "configured": sorted(configured),
            "sale_journal": sale_journal,
            "service_sale_journal": service_sale_journal,
            "purchase_journal": purchase_journal,
            "service_expense_journal": service_expense_journal,
        }

    def _get_coa_code_profile(self):
        self.ensure_one()
        company = self
        account_model = self.env["account.account"].with_company(company)
        accounts = account_model.search(
            [("company_ids", "in", company.id), ("active", "=", True)]
        )
        codes = [code for code in accounts.mapped("code") if code]
        numeric_codes = [code for code in codes if code.isdigit()]
        if not codes:
            return {"style": "numeric", "length": 8, "existing_codes": set()}
        style = "numeric" if numeric_codes and len(numeric_codes) * 100 >= len(codes) * 70 else "alnum"
        sample = numeric_codes if style == "numeric" else codes
        common_length = Counter(len(code) for code in sample).most_common(1)[0][0]
        return {
            "style": style,
            "length": max(common_length, 4),
            "existing_codes": set(codes),
        }

    def _find_template_account(self, company, account_types, keywords):
        account_model = self.env["account.account"].with_company(company)
        candidates = account_model.search(
            [
                ("company_ids", "in", company.id),
                ("active", "=", True),
                ("account_type", "in", list(account_types)),
            ],
            order="code",
        )
        if not candidates:
            return False
        non_intercompany = candidates.filtered(
            lambda account: "intercompany" not in (account.name or "").lower()
        )
        if non_intercompany:
            candidates = non_intercompany
        keywords_l = [kw.lower() for kw in keywords]
        scored = []
        for account in candidates:
            name_l = (account.name or "").lower()
            score = sum(2 for kw in keywords_l if kw in name_l)
            if "intercompany" in name_l:
                score -= 1
            scored.append((score, account))
        scored.sort(key=lambda item: (-item[0], item[1].code or "", item[1].id))
        return scored[0][1]

    def _generate_next_account_code(
        self, profile, existing_codes, template_code, fallback_prefix
    ):
        if profile["style"] == "numeric":
            digits = "".join(ch for ch in (template_code or "") if ch.isdigit())
            length = max(profile["length"], len(digits), 4)
            if digits:
                prefix_len = min(max(len(digits) - 2, 1), length - 1)
                prefix = digits[:prefix_len]
            else:
                prefix = fallback_prefix
            prefix = "".join(ch for ch in prefix if ch.isdigit()) or fallback_prefix
            prefix = prefix[: max(1, length - 1)]

            start = int(prefix + ("0" * (length - len(prefix))))
            max_existing = max(
                (
                    int(code)
                    for code in existing_codes
                    if code.isdigit() and len(code) == length and code.startswith(prefix)
                ),
                default=start,
            )
            for number in range(max_existing + 1, max_existing + 10000):
                candidate = str(number).zfill(length)
                if candidate.startswith(prefix) and candidate not in existing_codes:
                    return candidate

            global_max = max(
                (int(code) for code in existing_codes if code.isdigit() and len(code) == length),
                default=start,
            )
            candidate = str(global_max + 1).zfill(length)
            if len(candidate) > length:
                length = len(candidate)
                candidate = str(global_max + 1).zfill(length)
            return candidate

        base = re.sub(r"[^A-Za-z0-9.]", "", template_code or "") or fallback_prefix
        # Avoid chained codes such as ".IC01.IC01" when templates already include legacy IC suffixes.
        base = re.sub(r"(?:\.?IC\d+)+$", "", base, flags=re.IGNORECASE)
        base = base.rstrip(".")
        base = base[:54]
        for index in range(1, 1000):
            candidate = f"{base}.{index:02d}"
            if candidate not in existing_codes and len(candidate) <= 64:
                return candidate
        return f"{base}.999"

    def _find_existing_by_label(self, company, label, target_type):
        account_model = self.env["account.account"].with_company(company)
        return account_model.search(
            [
                ("company_ids", "in", company.id),
                ("active", "=", True),
                ("account_type", "=", target_type),
                ("name", "ilike", label),
            ],
            limit=1,
        )

    def _find_existing_by_seed_code(self, company, seed_code, target_type):
        if not seed_code:
            return False
        account_model = self.env["account.account"].with_company(company)
        return account_model.search(
            [
                ("company_ids", "in", company.id),
                ("active", "=", True),
                ("account_type", "=", target_type),
                ("code", "=", seed_code),
                ("name", "ilike", "intercompany"),
            ],
            limit=1,
        )

    def _find_existing_by_seed_family(self, company, seed_code, target_type):
        if not seed_code:
            return False
        account_model = self.env["account.account"].with_company(company)
        if "." in seed_code:
            like_pattern = f"{seed_code}.%"
            matcher = lambda code: (code or "").startswith(f"{seed_code}.")
        else:
            like_pattern = f"{seed_code}%"
            matcher = lambda code: (code or "").startswith(seed_code)
        candidates = account_model.search(
            [
                ("company_ids", "in", company.id),
                ("active", "=", True),
                ("account_type", "=", target_type),
                ("code", "like", like_pattern),
                ("name", "ilike", "intercompany"),
            ]
        )
        candidates = candidates.filtered(lambda account: matcher(account.code))
        if not candidates:
            return False
        return candidates.sorted(key=lambda account: (len(account.code or ""), account.code or "", account.id))[:1]

    def _align_intercompany_account_label(self, account, expected_label):
        if not account or not expected_label:
            return
        if account.name == expected_label:
            return
        name_l = (account.name or "").lower()
        if "intercompany" in name_l:
            account.write({"name": expected_label})

    def _is_seed_descendant_code(self, seed_code, account_code):
        if not seed_code or not account_code:
            return False
        if "." in seed_code:
            return account_code.startswith(f"{seed_code}.")
        return account_code.startswith(seed_code)

    def _normalize_configured_seed_accounts(self, country_seed_codes):
        self.ensure_one()
        updates = {}
        relinked = []
        company = self
        for spec in self._intercompany_account_specs():
            field_name = spec["field_name"]
            current = self[field_name]
            if not current:
                continue
            seed_code = (country_seed_codes.get(field_name) or "").strip()
            if not seed_code:
                continue
            if not self._is_seed_descendant_code(seed_code, current.code):
                continue
            if "intercompany" not in (current.name or "").lower():
                continue
            target_type = self._resolve_target_type(company, spec, seed_code)
            canonical = self._find_existing_by_seed_family(
                company, seed_code, target_type
            )
            if not canonical or canonical.id == current.id:
                continue
            if (len(canonical.code or ""), canonical.code or "") >= (
                len(current.code or ""),
                current.code or "",
            ):
                continue
            self._align_intercompany_account_label(canonical, spec["label"])
            updates[field_name] = canonical.id
            relinked.append(
                _(
                    "%(old)s -> %(new)s",
                    old=current.display_name,
                    new=canonical.display_name,
                )
            )
        if updates:
            self.write(updates)
        return relinked

    def _align_configured_intercompany_account_labels(self):
        self.ensure_one()
        aligned = []
        for spec in self._intercompany_account_specs():
            account = self[spec["field_name"]]
            if not account:
                continue
            before_name = account.name
            self._align_intercompany_account_label(account, spec["label"])
            if account.name != before_name:
                aligned.append(
                    _(
                        "%(code)s %(old)s -> %(new)s",
                        code=account.code,
                        old=before_name,
                        new=account.name,
                    )
                )
        return aligned

    def _cleanup_legacy_br_accounts(self, country_seed_codes):
        self.ensure_one()
        company = self
        country = company.account_fiscal_country_id or company.country_id
        if (country.code or "").upper() != "BR":
            return [], []
        if self._guess_br_coa_template() != "br_meepp":
            return [], []

        account_model = (
            self.env["account.account"]
            .with_context(active_test=False)
            .with_company(company)
        )
        legacy_specs = (
            {
                "field_name": "interco_income_service_account_id",
                "legacy_code": "3.01.01.01.02",
                "target_type": "income",
                "account_types": ["income", "income_other"],
            },
            {
                "field_name": "interco_income_production_account_id",
                "legacy_code": "3.01.01.01.03",
                "target_type": "income",
                "account_types": ["income", "income_other"],
            },
            {
                "field_name": "interco_expense_service_account_id",
                "legacy_code": "3.01.01.07.01.04.01",
                "target_type": "expense",
                "account_types": ["expense", "expense_direct_cost", "expense_other"],
            },
            {
                "field_name": "interco_expense_other_account_id",
                "legacy_code": "3.01.01.09.01.99.01",
                "target_type": "expense_other",
                "account_types": ["expense", "expense_direct_cost", "expense_other"],
            },
        )

        removed = []
        skipped = []
        updates = {}

        for spec in legacy_specs:
            account = account_model.search(
                [
                    ("company_ids", "in", company.id),
                    ("account_type", "in", spec["account_types"]),
                    ("code", "=", spec["legacy_code"]),
                ],
                limit=1,
            )
            if not account:
                continue

            move_line_count = self.env["account.move.line"].search_count(
                [("account_id", "=", account.id)]
            )
            if move_line_count:
                skipped.append(
                    _(
                        "%(code)s not removed (has %(count)s journal items)",
                        code=account.code,
                        count=move_line_count,
                    )
                )
                continue

            field_name = spec["field_name"]
            if self[field_name].id == account.id:
                seed_code = (country_seed_codes.get(field_name) or "").strip()
                replacement = self._find_existing_by_seed_code(
                    company, seed_code, spec["target_type"]
                ) or self._find_existing_by_seed_family(
                    company, seed_code, spec["target_type"]
                )
                if not replacement or replacement.id == account.id:
                    skipped.append(
                        _(
                            "%(code)s not removed (no replacement found for %(field)s)",
                            code=account.code,
                            field=field_name,
                        )
                    )
                    continue
                label = next(
                    (
                        item["label"]
                        for item in self._intercompany_account_specs()
                        if item["field_name"] == field_name
                    ),
                    False,
                )
                self._align_intercompany_account_label(replacement, label)
                updates[field_name] = replacement.id

            removed.append(f"{account.code} {account.name}")
            account.unlink()

        if updates:
            self.write(updates)

        return removed, skipped

    def _ensure_reporting_group(self, company, name, codes):
        codes = sorted({code for code in codes if code})
        if not codes:
            return False
        group_model = self.env["account.group"]
        start = min(codes)
        end = max(codes)
        if len(start) != len(end):
            # Fallback to a precise group when mixed code lengths are present.
            start = end = codes[0]

        group = group_model.search(
            [("company_id", "=", company.id), ("name", "=", name)], limit=1
        )
        vals = {
            "name": name,
            "company_id": company.id,
            "code_prefix_start": start,
            "code_prefix_end": end,
        }
        if group:
            to_write = {
                key: val
                for key, val in vals.items()
                if key != "company_id" and group[key] != val
            }
            if to_write:
                group.write(to_write)
        else:
            group = group_model.create(vals)
        return group

    def _ensure_intercompany_reporting_groups(self):
        self.ensure_one()
        company = self
        account_model = self.env["account.account"].with_company(company)

        revenue_codes = [
            self.interco_income_production_account_id.code,
            self.interco_income_resale_account_id.code,
            self.interco_income_service_account_id.code,
        ]
        expense_codes = [
            self.interco_expense_service_account_id.code,
            self.interco_expense_other_account_id.code,
        ]
        receivable_codes = [self.interco_receivable_account_id.code]
        payable_codes = [self.interco_payable_account_id.code]

        groups = []
        groups.append(
            self._ensure_reporting_group(
                company, _("Intercompany Revenue"), revenue_codes
            )
        )
        groups.append(
            self._ensure_reporting_group(
                company, _("Intercompany Expenses"), expense_codes
            )
        )
        groups.append(
            self._ensure_reporting_group(
                company, _("Intercompany Receivable"), receivable_codes
            )
        )
        groups.append(
            self._ensure_reporting_group(
                company, _("Intercompany Payable"), payable_codes
            )
        )
        groups = self.env["account.group"].browse([group.id for group in groups if group])

        # Trigger recompute path for account.group_id usage in reports.
        tracked_accounts = account_model.search(
            [
                ("company_ids", "in", company.id),
                ("id", "in", [
                    self.interco_income_production_account_id.id,
                    self.interco_income_resale_account_id.id,
                    self.interco_income_service_account_id.id,
                    self.interco_expense_service_account_id.id,
                    self.interco_expense_other_account_id.id,
                    self.interco_receivable_account_id.id,
                    self.interco_payable_account_id.id,
                ]),
            ]
        )
        tracked_accounts.invalidate_recordset(["group_id"])
        return groups

    def get_intercompany_account_proposal(self):
        self.ensure_one()
        company = self
        profile = self._get_coa_code_profile()
        country_seed_codes = self._get_country_seed_codes()
        existing_codes = set(profile["existing_codes"])
        proposals = []
        for spec in self._intercompany_account_specs():
            configured = self[spec["field_name"]]
            if configured:
                proposals.append(
                    {
                        "field_name": spec["field_name"],
                        "label": spec["label"],
                        "status": "configured",
                        "account": configured,
                        "suggested_code": configured.code,
                    }
                )
                existing_codes.add(configured.code or "")
                continue

            seed_code = country_seed_codes.get(spec["field_name"]) or ""
            template = self._find_template_account(
                company, spec["account_types"], spec["keywords"]
            )
            effective_seed_code = self._get_effective_seed_code(seed_code, template)
            target_type = self._resolve_target_type(
                company, spec, effective_seed_code
            )
            existing_by_seed = self._find_existing_by_seed_code(
                company, effective_seed_code, target_type
            )
            if existing_by_seed:
                proposals.append(
                    {
                        "field_name": spec["field_name"],
                        "label": spec["label"],
                        "status": "link",
                        "account": existing_by_seed,
                        "suggested_code": existing_by_seed.code,
                    }
                )
                existing_codes.add(existing_by_seed.code or "")
                continue

            existing_by_seed_family = self._find_existing_by_seed_family(
                company, effective_seed_code, target_type
            )
            if existing_by_seed_family:
                proposals.append(
                    {
                        "field_name": spec["field_name"],
                        "label": spec["label"],
                        "status": "link",
                        "account": existing_by_seed_family,
                        "suggested_code": existing_by_seed_family.code,
                    }
                )
                existing_codes.add(existing_by_seed_family.code or "")
                continue

            existing = self._find_existing_by_label(
                company, spec["label"], target_type
            )
            if existing:
                proposals.append(
                    {
                        "field_name": spec["field_name"],
                        "label": spec["label"],
                        "status": "link",
                        "account": existing,
                        "suggested_code": existing.code,
                    }
                )
                existing_codes.add(existing.code or "")
                continue

            source_code = effective_seed_code
            suggested_code = self._generate_seed_child_code(
                effective_seed_code, existing_codes
            )
            if not suggested_code:
                suggested_code = self._generate_next_account_code(
                    profile, existing_codes, source_code, spec["fallback_prefix"]
                )
            existing_codes.add(suggested_code)
            proposals.append(
                {
                    "field_name": spec["field_name"],
                    "label": spec["label"],
                    "status": "create",
                    "account": False,
                    "template": template,
                    "country_seed_code": country_seed_codes.get(spec["field_name"]) or "",
                    "suggested_code": suggested_code,
                }
            )
        return proposals

    def action_show_intercompany_account_proposal(self):
        self.ensure_one()
        if not self._is_intercompany_rules_module_available():
            return self._intercompany_rules_missing_notification(
                _("Intercompany COA Proposal - %s", self.display_name)
            )
        company = self
        profile = self._get_coa_code_profile()
        country_profile = self._get_intercompany_country_profile()
        proposals = self.get_intercompany_account_proposal()
        lines = [
            _("COA Style: %(style)s / Typical Code Length: %(length)s", style=profile["style"], length=profile["length"])
        ]
        if country_profile:
            country_name = (
                company.account_fiscal_country_id.name
                or company.country_id.name
                or ""
            )
            lines.append(
                _("Country profile seed active: %s", country_name)
            )
        for proposal in proposals:
            if proposal["status"] == "configured":
                lines.append(
                    _(
                        "%(label)s -> already configured (%(code)s)",
                        label=proposal["label"],
                        code=proposal["account"].code,
                    )
                )
            elif proposal["status"] == "link":
                lines.append(
                    _(
                        "%(label)s -> link existing %(code)s",
                        label=proposal["label"],
                        code=proposal["account"].code,
                    )
                )
            else:
                template_code = proposal["template"] and proposal["template"].code or "n/a"
                lines.append(
                    _(
                        "%(label)s -> create %(new_code)s (from template %(tmpl)s)",
                        label=proposal["label"],
                        new_code=proposal["suggested_code"],
                        tmpl=template_code,
                    )
                )
        message = "\n".join(lines)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Intercompany COA Proposal - %s", company.display_name),
                "message": message,
                "type": "info",
                "sticky": True,
            },
        }

    def action_setup_intercompany_accounts(self):
        self.ensure_one()
        if not self._is_intercompany_rules_module_available():
            return self._intercompany_rules_missing_notification(
                _("Intercompany Account Setup - %s", self.display_name)
            )
        company = self
        account_model = self.env["account.account"].with_company(company)
        profile = self._get_coa_code_profile()
        country_seed_codes = self._get_country_seed_codes()
        existing_codes = set(profile["existing_codes"])
        updates = {}
        created = []
        linked = []
        aligned = []
        missing_templates = []
        used_country_profile = False

        aligned.extend(self._align_configured_intercompany_account_labels())
        linked.extend(self._normalize_configured_seed_accounts(country_seed_codes))

        for spec in self._intercompany_account_specs():
            field_name = spec["field_name"]
            if self[field_name]:
                existing_codes.add(self[field_name].code or "")
                continue

            seed_code = country_seed_codes.get(field_name) or ""
            template = self._find_template_account(
                company, spec["account_types"], spec["keywords"]
            )
            effective_seed_code = self._get_effective_seed_code(seed_code, template)
            target_type = self._resolve_target_type(
                company, spec, effective_seed_code
            )
            existing_by_seed = self._find_existing_by_seed_code(
                company, effective_seed_code, target_type
            )
            if existing_by_seed:
                self._align_intercompany_account_label(existing_by_seed, spec["label"])
                updates[field_name] = existing_by_seed.id
                linked.append(existing_by_seed.display_name)
                existing_codes.add(existing_by_seed.code or "")
                continue

            existing_by_seed_family = self._find_existing_by_seed_family(
                company, effective_seed_code, target_type
            )
            if existing_by_seed_family:
                self._align_intercompany_account_label(
                    existing_by_seed_family, spec["label"]
                )
                updates[field_name] = existing_by_seed_family.id
                linked.append(existing_by_seed_family.display_name)
                existing_codes.add(existing_by_seed_family.code or "")
                continue

            existing = self._find_existing_by_label(
                company, spec["label"], target_type
            )
            if existing:
                self._align_intercompany_account_label(existing, spec["label"])
                updates[field_name] = existing.id
                linked.append(existing.display_name)
                existing_codes.add(existing.code or "")
                continue

            source_code = effective_seed_code
            if seed_code:
                used_country_profile = True

            if not source_code and not template:
                missing_templates.append(spec["label"])
                continue

            new_code = self._generate_seed_child_code(
                effective_seed_code, existing_codes
            )
            if not new_code:
                new_code = self._generate_next_account_code(
                    profile, existing_codes, source_code, spec["fallback_prefix"]
                )
            vals = {
                "name": spec["label"],
                "code": new_code,
                "account_type": target_type,
                "company_ids": [Command.set([company.id])],
                "reconcile": spec["reconcile"],
            }
            if template and template.tag_ids:
                vals["tag_ids"] = [Command.set(template.tag_ids.ids)]
            if template and template.tax_ids and target_type in (
                "income",
                "income_other",
                "expense",
                "expense_other",
                "expense_direct_cost",
            ):
                vals["tax_ids"] = [Command.set(template.tax_ids.ids)]
            account = account_model.create(vals)
            updates[field_name] = account.id
            created.append(account.display_name)
            existing_codes.add(account.code or "")

        if updates:
            self.write(updates)

        removed_legacy, skipped_legacy = self._cleanup_legacy_br_accounts(
            country_seed_codes
        )

        journal_result = self._ensure_intercompany_journals()

        if self.intercompany_sync_partner_accounts and (
            self.interco_receivable_account_id
            or self.interco_payable_account_id
            or self.interco_sale_journal_id
            or self.interco_service_sale_journal_id
            or self.interco_purchase_journal_id
            or self.interco_service_expense_journal_id
        ):
            partners = (
                self.env["res.partner"]
                .with_company(company)
                .search([("is_intercompany", "=", True)])
            )
            partners._apply_intercompany_partner_accounts()

        groups = self._ensure_intercompany_reporting_groups()

        parts = []
        if created:
            parts.append(_("Created: %s", ", ".join(created)))
        if linked:
            parts.append(_("Linked existing: %s", ", ".join(linked)))
        if aligned:
            parts.append(_("Aligned labels: %s", ", ".join(aligned)))
        if removed_legacy:
            parts.append(_("Removed legacy accounts: %s", ", ".join(removed_legacy)))
        if skipped_legacy:
            parts.append(_("Legacy cleanup skipped: %s", ", ".join(skipped_legacy)))
        if journal_result["created"]:
            parts.append(
                _("Created journals: %s", ", ".join(journal_result["created"]))
            )
        if journal_result["linked"]:
            parts.append(
                _("Linked journals: %s", ", ".join(journal_result["linked"]))
            )
        if journal_result["configured"]:
            parts.append(
                _("Configured journals: %s", ", ".join(journal_result["configured"]))
            )
        if groups:
            parts.append(
                _("Reporting groups ensured: %s", ", ".join(groups.mapped("name")))
            )
        if used_country_profile:
            parts.append(_("Country profile seed codes were applied."))
        if missing_templates:
            parts.append(
                _("Missing templates (manual setup required): %s", ", ".join(missing_templates))
            )
        if not parts:
            parts.append(_("All intercompany accounts were already configured."))

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Intercompany Account Setup - %s", company.display_name),
                "message": "\n".join(parts),
                "type": "success" if not missing_templates else "warning",
                "sticky": True,
            },
        }

    def _get_same_group_companies(self):
        self.ensure_one()
        return self.env["res.company"].with_context(active_test=False).search(
            [("id", "child_of", self.root_id.id), ("active", "=", True)],
            order="id",
        )

    def action_setup_intercompany_accounts_group(self):
        self.ensure_one()
        if not self._is_intercompany_rules_module_available():
            return self._intercompany_rules_missing_notification(
                _("Intercompany Account Setup - Group (%s)", self.root_id.display_name)
            )
        lines = []
        has_warning = False
        companies = self._get_same_group_companies()
        for company in companies:
            company_ctx = company.with_context(
                allowed_company_ids=[company.id],
                company_id=company.id,
            )
            company_ctx.action_setup_intercompany_accounts()
            missing = [
                spec["label"]
                for spec in company_ctx._intercompany_account_specs()
                if not company_ctx[spec["field_name"]]
            ]
            if missing:
                has_warning = True
                lines.append(
                    _(
                        "%(company)s: missing %(items)s",
                        company=company.display_name,
                        items=", ".join(missing),
                    )
                )
            else:
                lines.append(_("%s: configured", company.display_name))

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Intercompany Account Setup - Group (%s)", self.root_id.display_name),
                "message": "\n".join(lines) if lines else _("No active companies found in the group."),
                "type": "warning" if has_warning else "success",
                "sticky": True,
            },
        }

    @api.model
    def _cron_setup_intercompany_accounts_daily(self):
        if not self._is_backend_param_enabled(
            "erc_intercompany_je.autosetup_cron_enabled", True
        ):
            _logger.info("Daily intercompany autosetup skipped by backend parameter.")
            return
        if not self._is_intercompany_rules_module_available():
            module_name = self._get_required_intercompany_module_name()
            _logger.warning(
                "Daily intercompany autosetup skipped: module %s is not installed.",
                module_name,
            )
            return
        root_companies = (
            self.sudo()
            .with_context(active_test=False)
            .search([("parent_id", "=", False), ("active", "=", True)], order="id")
        )
        for root_company in root_companies:
            companies = root_company._get_same_group_companies()
            for company in companies:
                try:
                    company.with_context(
                        allowed_company_ids=[company.id],
                        company_id=company.id,
                    ).action_setup_intercompany_accounts()
                except Exception:
                    _logger.exception(
                        "Daily intercompany setup failed for company %s (%s)",
                        company.display_name,
                        company.id,
                    )


    def _cron_realign_intercompany_order_journals(self):
        """Re-evaluate IC journals on all draft SO/PO across all companies.

        Runs HQ (root) first, then branches, to ensure parent config
        propagates before children are processed.
        """
        if not self._is_backend_param_enabled(
            "erc_intercompany_je.autosetup_cron_enabled", True
        ):
            _logger.info("IC order journal realignment skipped by backend parameter.")
            return
        root_companies = (
            self.sudo()
            .with_context(active_test=False)
            .search([("parent_id", "=", False), ("active", "=", True)], order="id")
        )
        for root_company in root_companies:
            companies = root_company._get_same_group_companies()
            for company in companies:
                try:
                    self._realign_company_ic_orders(company)
                except Exception:
                    _logger.exception(
                        "IC order journal realignment failed for company %s (%s)",
                        company.display_name,
                        company.id,
                    )

    def _realign_company_ic_orders(self, company):
        """Re-evaluate IC journals on draft orders for a single company."""
        env = self.env
        # Sale Orders
        sale_orders = (
            env["sale.order"]
            .with_company(company)
            .with_context(allowed_company_ids=[company.id])
            .search([
                ("company_id", "=", company.id),
                ("state", "in", ("draft", "sent")),
                ("partner_id.is_intercompany", "=", True),
            ])
        )
        so_count = 0
        for order in sale_orders:
            try:
                journal = order._get_intercompany_sale_journal()
                if journal and journal != order.journal_id:
                    order.journal_id = journal
                    so_count += 1
            except Exception:
                _logger.warning(
                    "Could not realign SO %s (mixed types?): %s",
                    order.name,
                    order.id,
                )
        # Purchase Orders
        purchase_orders = (
            env["purchase.order"]
            .with_company(company)
            .with_context(allowed_company_ids=[company.id])
            .search([
                ("company_id", "=", company.id),
                ("state", "in", ("draft", "sent")),
                ("partner_id.is_intercompany", "=", True),
            ])
        )
        po_count = 0
        for order in purchase_orders:
            try:
                journal = order._get_intercompany_purchase_journal()
                if journal and journal != order.journal_id:
                    order.journal_id = journal
                    po_count += 1
            except Exception:
                _logger.warning(
                    "Could not realign PO %s (mixed types?): %s",
                    order.name,
                    order.id,
                )
        if so_count or po_count:
            _logger.info(
                "IC journal realignment for %s: %d SO(s), %d PO(s) updated.",
                company.display_name,
                so_count,
                po_count,
            )


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    interco_income_production_account_id = fields.Many2one(
        related="company_id.interco_income_production_account_id", readonly=False
    )
    interco_income_resale_account_id = fields.Many2one(
        related="company_id.interco_income_resale_account_id", readonly=False
    )
    interco_income_service_account_id = fields.Many2one(
        related="company_id.interco_income_service_account_id", readonly=False
    )
    interco_expense_service_account_id = fields.Many2one(
        related="company_id.interco_expense_service_account_id", readonly=False
    )
    interco_expense_other_account_id = fields.Many2one(
        related="company_id.interco_expense_other_account_id", readonly=False
    )
    interco_receivable_account_id = fields.Many2one(
        related="company_id.interco_receivable_account_id", readonly=False
    )
    interco_payable_account_id = fields.Many2one(
        related="company_id.interco_payable_account_id", readonly=False
    )
    interco_sale_journal_id = fields.Many2one(
        related="company_id.interco_sale_journal_id", readonly=False
    )
    interco_service_sale_journal_id = fields.Many2one(
        related="company_id.interco_service_sale_journal_id", readonly=False
    )
    interco_purchase_journal_id = fields.Many2one(
        related="company_id.interco_purchase_journal_id", readonly=False
    )
    interco_service_expense_journal_id = fields.Many2one(
        related="company_id.interco_service_expense_journal_id", readonly=False
    )
    intercompany_enforce_accounts = fields.Boolean(
        related="company_id.intercompany_enforce_accounts", readonly=False
    )
    intercompany_sync_partner_accounts = fields.Boolean(
        related="company_id.intercompany_sync_partner_accounts", readonly=False
    )
    intercompany_bom_production_account = fields.Boolean(
        related="company_id.intercompany_bom_production_account", readonly=False
    )
    intercompany_demo_products_installed = fields.Boolean(
        string="Install Intercompany Demo Products",
        config_parameter="erc_intercompany_je.demo_products_installed",
    )

    def action_show_intercompany_account_proposal(self):
        self.ensure_one()
        return self.company_id.action_show_intercompany_account_proposal()

    def action_setup_intercompany_accounts(self):
        self.ensure_one()
        return self.company_id.action_setup_intercompany_accounts()

    def action_setup_intercompany_accounts_group(self):
        self.ensure_one()
        return self.company_id.action_setup_intercompany_accounts_group()

    def action_install_intercompany_demo_products(self):
        """Create example intercompany products and BOM from XML data files."""
        self.ensure_one()
        already = self.env["ir.config_parameter"].sudo().get_param(
            "erc_intercompany_je.demo_products_installed"
        )
        if already and str(already).strip().lower() in {"1", "true", "yes"}:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Demo Products"),
                    "message": _("Intercompany demo products are already installed."),
                    "type": "info",
                    "sticky": False,
                },
            }
        module = self.env["ir.module.module"].search(
            [("name", "=", "erc_intercompany_je")], limit=1
        )
        module_path = module._get_module_path() if module else False
        if not module_path:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Error"),
                    "message": _("Cannot locate module path."),
                    "type": "danger",
                    "sticky": True,
                },
            }
        import os
        from odoo.tools import convert
        for xml_file in [
            "data/intercompany_demo_products.xml",
            "data/intercompany_demo_bom.xml",
        ]:
            full_path = os.path.join(module_path, xml_file)
            if os.path.isfile(full_path):
                convert.convert_file(
                    self.env,
                    "erc_intercompany_je",
                    xml_file,
                    idref={},
                    mode="init",
                    noupdate=True,
                )
        self.env["ir.config_parameter"].sudo().set_param(
            "erc_intercompany_je.demo_products_installed", "True"
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Demo Products Installed"),
                "message": _(
                    "Created: Goods Intercompany, Services Intercompany, "
                    "Product Intercompany (with BOM), Material BOM component."
                ),
                "type": "success",
                "sticky": False,
            },
        }
