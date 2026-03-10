# ERC Intercompany Journal Entries & Transactions (v19)
**Advanced Accounting Segregation & Global Infrastructure Automation**

**Version:** 19.0.6.5.0 | **License:** OPL-1 (Odoo Proprietary License) | **Price:** $50 USD

---

## Overview
The **ERC Intercompany Journal Entries** module is a professional-grade extension for Odoo 19, designed to bridge the gap in native intercompany workflows. It ensures that cross-company transactions are not just synchronized, but correctly segregated into dedicated GL accounts and journals according to global fiscal standards.

## Key Features

### 4-Journal Architecture
Four dedicated journals — two for the seller side, two for the buyer side — each with its own numbering sequence, default accounts, and audit trail:

| Journal | Code | Side | Routes To |
|---------|------|------|-----------|
| Intercompany Sales | ICS | Seller | Goods (Resale & Production) |
| Intercompany Services Sales | ISS | Seller | Services |
| Intercompany Purchases | ICP | Buyer | Goods (COGS) |
| Intercompany Services Expenses | ICE | Buyer | Services |

### 7 Dedicated GL Accounts
Automatically created per company on install:
- **Revenue:** Production Sales IC, Resale Sales IC, Service Sales IC
- **Cost/Expense:** Cost of Goods Sold IC, Services Expenses IC
- **Balance Sheet:** Intercompany Receivable, Intercompany Payable

### Smart Journal Routing
The journal is determined automatically when product lines are added — not when the partner is selected:
- **Service products** → ISS / ICE journals
- **Goods without BOM** → ICS / ICP journals + Resale account
- **Goods with BOM** → ICS / ICP journals + Production account
- **Mixed (goods + services)** → Blocked with a clear error message

### BOM-Aware Revenue Routing
Products with a Bill of Materials are automatically routed to the **Production Income Account** on the ICS journal. Regular goods use the Resale account. Both accounts are visible directly on the journal form for full audit transparency. This behavior is configurable via a company-level checkbox.

### 50+ Country Profiles
Pre-loaded account seed codes for Brazil, Portugal, Angola, USA, UK, Germany, France, Spain, Mexico, and 40+ more countries. Account codes and labels are generated in the correct format for each localization (dotted codes for BR, short codes for PT, numeric codes for US, etc.).

### Intercompany Partner Sync
Mark a partner as "Intercompany" and the module instantly assigns dedicated AR/AP accounts, links IC journals, and auto-selects the correct journal on every new Sale or Purchase Order.

### Draft Review & Enforcement
See the assigned IC journal and account routing while orders are still in Draft. Enable "Enforce Segregation" to block invoice creation if any required intercompany account is missing.

### Demo Products
One-click install of example products (Goods, Services, Manufactured with BOM) to test all routing scenarios. Available in Settings — never installed automatically.

### Automated Persistence
- **On Install:** Creates all 7 GL accounts, 4 journals, seeds country profiles, and links partner accounts
- **On Upgrade:** Migration scripts detect missing journals or accounts and fill gaps
- **Daily Cron:** Re-evaluates all draft SO/PO journals and auto-corrects if product types changed

## Installation & Usage
1. Install the module on your Odoo 19 database (requires `account_inter_company_rules`).
2. Intercompany accounts and journals are created automatically on install.
3. Configure settings in **Settings > General Settings > Intercompany Account Segregation**.
4. Flag relevant Partners as **"Intercompany"** on the Partner form.
5. Create Sale/Purchase Orders — journals and accounts are selected automatically.

## Live Demo

Try the module on our demo instance — no installation required.

- **URL:** [erc-implementors.com/web/database/selector](https://erc-implementors.com/web/database/selector)
- **Database:** `intercompany_je_us`
- **Login:** `ERC_ME`
- **Password:** `demo`

### Demo User Access Rights

The demo user has read-only access with limited write permissions for testing the IC workflow:

| Odoo Group | Access Level | What You Can Do |
|------------|-------------|-----------------|
| Internal User | Base access | Navigate all menus |
| Accounting Manager | Full accounting config | View journals, accounts, chart of accounts |
| Sales User | Own documents | Create draft Sale Orders to test routing |
| Purchase User | Standard | Create draft Purchase Orders to test routing |

**What you CAN do:**
- View all 4 IC journals (ICS/ISS/ICP/ICE) and their configuration in Accounting > Configuration > Journals
- View all 7 IC accounts in Accounting > Configuration > Chart of Accounts
- View partner IC configuration (Contacts > open partner > Accounting tab)
- Create draft Sale Orders and Purchase Orders to test smart journal routing
- See the mixed order protection error (add both goods + services to same IC order)
- View demo products (Goods, Services, Manufactured with BOM)

**What you CANNOT do:**
- Access Settings (no admin/system access)
- Install or uninstall modules
- Manage users or security groups
- Post invoices or reconcile entries
- Delete or modify master data (accounts, journals, partners)

## Dependencies
- `account`
- `sale_purchase_stock`
- `sale_stock`, `purchase_stock`, `sale_purchase`
- `mrp` (for BOM-aware routing)

## Corporate Governance
Developed and maintained by **ERC IMPLEMENTORS LTDA**, specialized in high-performance Odoo localizations and architectural governance.

*   **CNPJ:** 12.353.398/0001-29
*   **Location:** Rua Professora Gioconda Mussolini, 239. Jd Rizzo, Sao Paulo - SP, Brazil
*   **Owner:** Benedito Monteiro
*   **Website:** [www.erc-implementors.com](https://www.erc-implementors.com)

## Support & Inquiries
*   **WhatsApp:** [+55 11 92207 9570](https://wa.me/5511922079570)
*   **Email:** admin@erc-implementors.com

---
### License
Licensed under **OPL-1** (Odoo Proprietary License v1.0). (c) 2026 ERC Implementors LTDA. All Rights Reserved.
