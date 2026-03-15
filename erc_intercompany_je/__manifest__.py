# -*- coding: utf-8 -*-
# Sovereign Odoo Code Forge (v19) - SFP Finalized
# ERC Implementors (c) 2026 - https://erc-implementors.com

{
    "name": "ERC Intercompany Journal Entries & Transactions",
    "summary": "Global Intercompany Segregation: Dynamic Account & Journal Creation in 50+ Countries",
    "description": """
Professional Intercompany Financial Segregation
==============================================
Bridge the gap in native Odoo 19 intercompany flows. This module ensures that cross-company transactions are not just synced, but correctly segregated into dedicated GL accounts.

Key Features:
-------------
* **4-Journal Architecture:** ICS (Sales), ISS (Services Sales), ICP (Purchases), ICE (Services Expenses) created per company.
* **Smart Journal Routing:** Journal auto-selects based on product type: services to ISS/ICE, goods to ICS/ICP.
* **BOM-Aware Revenue Routing:** Products with Bill of Materials use the Production Income Account on the ICS journal; regular goods use Resale. Fully configurable per company.
* **Mixed Order Protection:** Services and goods cannot be mixed on the same intercompany order.
* **7 Dedicated GL Accounts:** 3 revenue (Production, Resale, Service), 2 cost/expense (COGS, Service Expense), plus AR and AP.
* **50+ Country Profiles:** Localized seed codes and translated account names for 50+ countries.
* **Daily Cron Realignment:** Automated journal and account realignment across all branches.
* **Demo Products:** Optional example products (Goods, Services, Manufactured with BOM) for testing.
* **Partner Isolation:** Dedicated AR/AP accounts for intercompany partners with auto-sync.
* **Fiscal Localization:** Built-in logic for Brazilian (BR), Angolan (AO), Portuguese (PT), and US intercompany standards.

Phase 2 (v7.0):
* **Setup Status Dashboard:** Live badge showing Not Configured / Partial / Complete per company.
* **Pre-Setup Validation:** Country and COA checks before account creation.
* **Chatter & Audit Trail:** Country profile tracking + setup summary posted to partner chatter with PDF.
* **Auto-Clear on Unflag:** IC journal/account pointers cleared when partner is unflagged.
* **PDF Setup Summary:** QWeb report with GL accounts, journals, and seed codes.
* **Invoice Journal Alignment:** Chatter warning on journal mismatch at posting (non-blocking).
* **Batch Setup Wizard:** Run setup across all group companies from a single wizard.
    """,
    "version": "19.0.7.0.1",
    "category": "Accounting",
    "author": "ERC Implementors (Benedito Monteiro)",
    "website": "https://erc-implementors.com",
    "license": "OPL-1",
    "application": True,
    "installable": True,
    "price": 50.0,
    "currency": "USD",
    "images": [
        "static/description/banner.jpg",
        "static/description/icon.png"
    ],
    "depends": [
        "account",
        "mail",
        "sale_purchase_stock",
        "sale_stock",
        "purchase_stock",
        "sale_purchase",
        "mrp",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/intercompany_backend_params.xml",
        "data/intercompany_backend_params_tuned.xml",
        "data/intercompany_country_profile.xml",
        "data/ir_cron.xml",
        "views/wizard_intercompany_setup.xml",
        "views/res_partner.xml",
        "report/erc_intercompany_je_setup_report.xml",
        "report/erc_intercompany_je_setup_template.xml",
    ],
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",
}
