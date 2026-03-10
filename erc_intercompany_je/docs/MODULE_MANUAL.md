# ERC Intercompany Journal Entries & Transactions (v19)
**Module Manual — Version 19.0.6.5.0**

---

## 1. Functional Overview

The **ERC Intercompany Journal Entries** module is an enterprise-grade solution for Odoo 19 multi-company environments. It automates the segregation of intercompany transactions into dedicated GL accounts and journals, ensuring clean consolidated reporting and full audit traceability.

### Core Value Proposition
- **Zero-Drift Accounting:** Every intercompany transaction is routed to dedicated GL accounts — never mixed with third-party operations.
- **Automated Segregation:** Smart routing based on product type (service, goods, manufactured goods with BOM).
- **Audit-Ready Traceability:** Independent journal sequences, visible account routing in draft, and enforcement controls.

---

## 2. Key Features

### 2.1 4-Journal Architecture

The module creates four dedicated journals per company, separating goods from services on both the seller and buyer sides:

| Journal | Code | Type | Purpose | Default Account |
|---------|------|------|---------|-----------------|
| Intercompany Sales | ICS | Sale | Goods revenue | Resale Sales IC |
| Intercompany Services Sales | ISS | Sale | Service revenue | Service Sales IC |
| Intercompany Purchases | ICP | Purchase | Goods cost | COGS IC |
| Intercompany Services Expenses | ICE | Purchase | Service expense | Services Expenses IC |

Each journal has:
- Its own numbering sequence (e.g., `ICS/2026/0001`)
- Dedicated credit note sequence (e.g., `RICS/2026/0001`)
- Default income/expense accounts pre-configured
- Auto-incrementing codes if taken (ICS -> IC2 -> IC3)

> **Note:** Document Series and Use Documents fields are available depending on your localization (e.g., LATAM countries).

### 2.2 7 Dedicated GL Accounts

Created automatically per company on install, using country-specific seed codes:

**Revenue (Seller Side):**
| Account | US Code | Used When |
|---------|---------|-----------|
| Production Sales IC | 40000001 | Goods with BOM (manufactured) |
| Resale Sales IC | 40010001 | Goods without BOM |
| Service Sales IC | 40030001 | Service-type products |

**Cost/Expense (Buyer Side):**
| Account | US Code | Used When |
|---------|---------|-----------|
| Cost of Goods Sold IC | 50000001 | All goods purchases |
| Services Expenses IC | 65350001 | Service purchases |

**Balance Sheet:**
| Account | US Code | Used When |
|---------|---------|-----------|
| Intercompany Receivable | 13100001 | IC partner invoices (AR) |
| Intercompany Payable | 21100001 | IC partner bills (AP) |

Codes shown are for US profile. Brazilian companies use `3.01.xx`, Portuguese use `71xx`, etc.

### 2.3 Smart Journal Routing

The journal is determined automatically based on the order lines — not on partner selection:

1. **Select IC partner** → No journal set yet
2. **Add product lines** → Module detects product type
3. **Journal auto-selected** → ICS/ISS (sales) or ICP/ICE (purchases)

**Routing rules:**
- All lines are **services** → ISS / ICE journal
- All lines are **goods** → ICS / ICP journal
- **Mixed** (goods + services on same order) → Blocked with clear error message

The user must create separate orders for goods and services when dealing with intercompany partners.

### 2.4 BOM-Aware Revenue Routing

Products with a Bill of Materials are automatically routed to the **Production Income Account** instead of the Resale account:

1. User adds a product with BOM to an IC Sale Order
2. Module detects the BOM via `mrp.bom` lookup
3. Invoice line uses the Production Income Account from the ICS journal
4. Regular goods (no BOM) use the Resale Income Account

The ICS journal displays **both** accounts (Default Income + Production Income) for full audit transparency.

**Configurable:** A company-level checkbox ("BOM Products Use Production Revenue Account") controls this behavior. Disable it to route all goods through Resale regardless of BOM.

### 2.5 50+ Country Localization Profiles

Pre-loaded account seed codes for 50+ countries including:
- **Americas:** Brazil, USA, Canada, Mexico, Argentina, Chile, Colombia, Peru, Uruguay
- **Europe:** Portugal, Spain, France, Germany, UK, Italy, Netherlands, Belgium, Switzerland, Austria, Denmark, Sweden, Norway, Finland, Poland, Czech Republic, Hungary, Romania, Greece, Ireland, Luxembourg
- **Middle East & Africa:** Angola, UAE, Saudi Arabia, Qatar, Oman, Bahrain, Egypt, Morocco, Algeria, South Africa, Turkey
- **Asia-Pacific:** India, China, Japan, South Korea, Taiwan, Singapore, Malaysia, Australia, New Zealand

The module reads your company's fiscal country and generates account codes matching the local COA standard:
- Numeric codes (US: `40000001`)
- Dotted codes (BR: `3.01.01.01`)
- Short codes (PT: `7111`)

### 2.6 Intercompany Partner Configuration

Mark a partner as "Intercompany" on the Partner form to reveal:
- **Sale Intercompany Journal** (Many2one)
- **Purchase Intercompany Journal** (Many2one)
- **Intercompany Receivable Account** (Many2one)
- **Intercompany Payable Account** (Many2one)

When `is_intercompany` is checked:
- Journals default to the company's IC journals
- Partner's `property_account_receivable_id` and `property_account_payable_id` are updated to IC accounts
- Every new SO/PO for that partner auto-selects the correct IC journal

### 2.7 Draft Review & Enforcement

- **Draft visibility:** The assigned IC journal and account routing are visible while orders are in Draft status.
- **Enforce Segregation:** When enabled, the module blocks invoice/bill creation if any required intercompany account is missing — preventing GL contamination before it happens.
- **Sync Partner AR/AP:** Auto-assigns IC receivable/payable accounts when a partner is flagged as intercompany.

### 2.8 Demo Products

One-click install of example products to test all routing scenarios:
- **Goods Intercompany** — Consumable (routes to ICS/ICP + Resale account)
- **Services Intercompany** — Service (routes to ISS/ICE + Service accounts)
- **Product Intercompany** — Consumable with BOM (routes to ICS/ICP + Production account)
- **Material BOM** — Component for the BOM

Available in Settings > Intercompany Demo Products. Never installed automatically — safe for production databases.

---

## 3. Configuration Guide

### 3.1 Settings (General Settings > Intercompany)

Three configuration sections:

**Section 1 — Intercompany Journal on Orders:**
- Toggle to display journal selector on SO/PO forms
- 4 journal fields (ICS, ISS, ICP, ICE)

**Section 2 — Intercompany Demo Products:**
- Checkbox + button to install demo products
- One-time action, button disappears after install

**Section 3 — Intercompany Account Segregation:**
- **Enforce Segregation** — block invoices if accounts missing
- **Sync Partner AR/AP** — auto-assign IC receivable/payable
- **BOM -> Production Account** — route manufactured goods
- 7 account fields (3 revenue, 2 cost/expense, AR, AP)
- Action buttons:
  - *Analyze COA Proposal* — shows account analysis (informational)
  - *Analyze & Auto-Create Accounts* — creates/links accounts
  - *Setup For Company Group* — applies to all companies

### 3.2 Partner Configuration

On the Partner form (Accounting tab):
1. Check **"Intercompany"** checkbox
2. Fields appear: Sale/Purchase IC journals + Receivable/Payable IC accounts
3. Values default to company settings when checked

### 3.3 Journal Configuration

Each IC journal form shows:
- Short Code and sequence prefix
- Default Income/Expense Account
- **Default Production Income Account** (on ICS journal only)
- Dedicated Credit Note Sequence toggle

---

## 4. Technical Architecture

### 4.1 Models Extended

| Model | Fields Added | Key Methods |
|-------|-------------|-------------|
| `res.company` | 11 IC fields (7 accounts + 4 journals) | `action_setup_intercompany_accounts()`, `_ensure_intercompany_journals()` |
| `res.config.settings` | Related fields for all 11 | Settings UI actions |
| `res.partner` | `is_intercompany`, 4 IC fields | `_apply_intercompany_partner_accounts()` |
| `account.journal` | `intercompany_production_account_id` | Production account override |
| `sale.order` | `is_intercompany_journal_display` | `_get_intercompany_sale_journal()`, `_prepare_invoice()` |
| `sale.order.line` | — | `_get_intercompany_income_account()`, `_is_manufactured_product()` |
| `purchase.order` | `journal_id`, `is_intercompany_journal_display` | `_get_intercompany_purchase_journal()`, `_prepare_invoice()` |
| `purchase.order.line` | — | `_get_intercompany_expense_account()` |

**New Model:**
- `erc.intercompany.country.profile` — stores country-specific account seed codes

### 4.2 Smart Routing Logic

**Sale Order Line → Income Account:**
```
Is service?
  └─ Yes → interco_income_service_account_id
  └─ No → Has BOM? (mrp.bom lookup)
       └─ Yes (and BOM config enabled) → Journal's production_account OR company's production_account
       └─ No → interco_income_resale_account_id
```

**Purchase Order Line → Expense Account:**
```
Is service?
  └─ Yes → interco_expense_service_account_id
  └─ No → interco_expense_other_account_id (COGS)
```

### 4.3 Account Auto-Creation

The `action_setup_intercompany_accounts()` method:
1. Reads the company's fiscal country
2. Looks up the country profile for seed codes
3. Analyzes existing COA (numeric vs alphanumeric, code length)
4. For each of the 7 accounts:
   - Finds existing account matching keywords/seed code
   - If not found, generates a new account code
   - Creates the account with correct type and labels
5. Creates/configures 4 journals (ICS, ISS, ICP, ICE)
6. Creates reporting groups for IC accounts

### 4.4 Automation

| Trigger | Method | Purpose |
|---------|--------|---------|
| Post-install hook | `_run_intercompany_autosetup()` | Creates accounts/journals for all companies |
| Migration scripts | `_run_intercompany_autosetup()` | Fills gaps on upgrade |
| Daily cron #1 | `_cron_setup_intercompany_accounts_daily()` | Ensures all companies have IC accounts |
| Daily cron #2 | `_cron_realign_intercompany_order_journals()` | Re-evaluates draft SO/PO journals |

---

## 5. Backend Parameters

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `erc_intercompany_je.required_intercompany_module` | `account_inter_company_rules` | Prerequisite module |
| `erc_intercompany_je.require_rules_on_install` | `1` | Block install if missing |
| `erc_intercompany_je.require_rules_runtime` | `1` | Block runtime if missing |
| `erc_intercompany_je.autosetup_on_install` | `1` | Run autosetup on post_init |
| `erc_intercompany_je.autosetup_on_upgrade` | `1` | Run autosetup on migration |
| `erc_intercompany_je.autosetup_cron_enabled` | `1` | Enable daily cron |
| `erc_intercompany_je.journal_autofill_defaults` | `1` | Auto-populate journal defaults |
| `erc_intercompany_je.journal_mirror_use_documents` | `1` | Mirror l10n_latam_use_documents |
| `erc_intercompany_je.journal_force_use_documents` | `1` | Force use_documents if available |
| `erc_intercompany_je.journal_control_sequence` | `1` | Enable refund/debit sequences |

---

## 6. Security

| Model | Role | Read | Write | Create | Delete |
|-------|------|------|-------|--------|--------|
| `erc.intercompany.country.profile` | Account Managers | Yes | Yes | Yes | No |
| `erc.intercompany.country.profile` | System Admins | Yes | Yes | Yes | Yes |

---

## 7. Dependencies

| Module | Purpose |
|--------|---------|
| `account` | Core accounting |
| `sale_purchase_stock` | SO/PO stock integration |
| `sale_stock` | Sale stock management |
| `purchase_stock` | Purchase stock management |
| `sale_purchase` | Sale-Purchase link |
| `mrp` | BOM detection for production routing |

**Prerequisite:** `account_inter_company_rules` (Odoo native intercompany module)

---

## 8. Live Demo

A public demo instance is available for testing all module features without installation.

### Access Details

| Field | Value |
|-------|-------|
| URL | [erc-implementors.com/web/database/selector](https://erc-implementors.com/web/database/selector) |
| Database | `intercompany_je_us` |
| Login | `ERC_ME` |
| Password | `demo` |

### Demo User Access Rights

The `ERC_ME` user is configured with the following Odoo security groups:

| Odoo Group (xml_id) | Role | Purpose |
|---------------------|------|---------|
| `base.group_user` | Internal User | Base navigation and menu access |
| `account.group_account_manager` | Accounting Manager | View/manage journals, accounts, chart of accounts |
| `sales_team.group_sale_salesman` | Sales User (Own Documents) | Create draft Sale Orders |
| `purchase.group_purchase_user` | Purchase User | Create draft Purchase Orders |

### What the Demo User Can Do

- **Accounting > Configuration > Journals** — View all 4 IC journals (ICS, ISS, ICP, ICE), their default accounts, production account, and sequence configuration
- **Accounting > Configuration > Chart of Accounts** — View all 7 IC accounts created by the module
- **Contacts** — Open any partner > Accounting tab > see `is_intercompany` flag, IC journals, and IC receivable/payable accounts
- **Sales > Orders** — Create draft Sale Orders with an IC partner to test smart journal routing (service → ISS, goods → ICS)
- **Purchase > Orders** — Create draft Purchase Orders with an IC partner to test routing (service → ICE, goods → ICP)
- **Mixed Order Protection** — Add both goods and services to the same IC order to see the blocking error message
- **Demo Products** — View the pre-installed demo products (Goods, Services, Manufactured with BOM)

### What the Demo User Cannot Do

- Access Settings (no `base.group_system`)
- Install or uninstall modules
- Manage users or security groups
- Post invoices, create payments, or reconcile entries
- Delete or modify master data (accounts, journals, partners, products)
- Access Technical menus (no `base.group_no_one`)

### Recommended Demo Walkthrough

1. Go to **Accounting > Configuration > Journals** — observe the 4 IC journals
2. Open the **ICS** journal — note the Default Income Account and Production Income Account
3. Go to **Contacts** — open the IC partner and check the Accounting tab
4. Go to **Sales > Orders > New** — select the IC partner, add a service product → journal switches to ISS
5. Clear lines, add a goods product → journal switches to ICS
6. Try adding both goods + services → see the blocking error
7. Go to **Accounting > Configuration > Chart of Accounts** — filter by "Intercompany" to see all 7 accounts

---

**Developed By:** ERC Implementors LTDA
**Version:** 19.0.6.5.0
**Website:** [erc-implementors.com](https://erc-implementors.com)
