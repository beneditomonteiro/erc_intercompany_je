# ERC Intercompany JE Persistency Manual (Odoo 19)
**Version:** 19.0.6.5.0

## Scope
This module auto-configures intercompany accounting artifacts with persistent behavior across:
- Fresh installs
- Module upgrades
- Daily maintenance cron

## What Is Persistent

### Intercompany Accounts (7 per company)
- 3 Revenue: Production Sales IC, Resale Sales IC, Service Sales IC
- 2 Cost/Expense: Cost of Goods Sold IC, Services Expenses IC
- 2 Balance Sheet: Intercompany Receivable, Intercompany Payable

Account codes are generated based on the company's fiscal country profile (50+ countries supported).

### Intercompany Journals (4 per company)
| Journal | Code | Type | Features |
|---------|------|------|----------|
| Intercompany Sales | ICS | Sale | Default + Production income accounts |
| Intercompany Services Sales | ISS | Sale | Default service income account |
| Intercompany Purchases | ICP | Purchase | Default COGS account |
| Intercompany Services Expenses | ICE | Purchase | Default service expense account |

Each journal includes:
- Default income/expense accounts
- Dedicated credit note sequence (RICS, RISS, RICP, RICE)
- Dedicated debit note sequence
- Mirrored `Use Documents` behavior when available (`l10n_latam_use_documents`)
- Auto-incrementing codes if taken (ICS -> IC2 -> IC3)

### Reporting Groups
- Intercompany Revenue group
- Intercompany Expense group
- Intercompany AR group
- Intercompany AP group

### Partner Synchronization
- Intercompany partner account/journal synchronization
- Auto-assignment of IC receivable/payable on partner flagging

## Backend Parameters (Seeded on Install/Update)
The module seeds these `ir.config_parameter` keys from `data/intercompany_backend_params.xml`:

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `erc_intercompany_je.required_intercompany_module` | `account_inter_company_rules` | Prerequisite module name |
| `erc_intercompany_je.require_rules_on_install` | `1` | Validate prerequisite on install |
| `erc_intercompany_je.require_rules_runtime` | `1` | Validate prerequisite at runtime |
| `erc_intercompany_je.autosetup_on_install` | `1` | Run autosetup on post_init hook |
| `erc_intercompany_je.autosetup_on_upgrade` | `1` | Run autosetup on migration |
| `erc_intercompany_je.autosetup_cron_enabled` | `1` | Enable daily maintenance cron |
| `erc_intercompany_je.journal_autofill_defaults` | `1` | Auto-populate journal default accounts |
| `erc_intercompany_je.journal_mirror_use_documents` | `1` | Mirror l10n_latam_use_documents setting |
| `erc_intercompany_je.journal_force_use_documents` | `1` | Force use_documents if localization supports |
| `erc_intercompany_je.journal_control_sequence` | `1` | Enable refund/debit note sequences |

## Lifecycle Hooks

### Post-Init Hook
- Runs `_run_intercompany_autosetup(env, "Post-init")` for all active companies
- Controlled by `autosetup_on_install`
- Creates accounts, journals, reporting groups, and partner links

### Pre-Init Hook
- Validates that the prerequisite module (`account_inter_company_rules`) is available
- Logs warning if missing (does not block installation)

### Migration Scripts
- Located in `migrations/<version>/post-migration.py`
- Runs autosetup on upgrade (controlled by `autosetup_on_upgrade`)
- Detects missing journals or accounts and fills gaps
- Preserves existing data — only creates what's missing

### Daily Crons (2)
1. **Account Setup Cron:** Executes `_cron_setup_intercompany_accounts_daily()` — ensures all companies have IC accounts and journals created/linked
2. **Order Journal Realignment Cron:** Executes `_cron_realign_intercompany_order_journals()` — re-evaluates all draft SO/PO journals and auto-corrects if product types changed

## Country Profiles
- Model: `erc.intercompany.country.profile`
- Seeded from `data/intercompany_country_profile.xml` (50+ countries)
- Each profile contains 7 seed codes (receivable, payable, 3 income, 2 expense)
- Brazilian COA template auto-detection: `br_meepp`, `br_generic`, `br`

## Security
- ACLs defined in `security/ir.model.access.csv` for `erc.intercompany.country.profile`
- Account managers: read, write, create (no delete)
- System administrators: full access

## Data Files Load Order
1. `security/ir.model.access.csv`
2. `data/intercompany_backend_params.xml`
3. `data/intercompany_country_profile.xml`
4. `data/ir_cron.xml`
5. `views/res_partner.xml`

## Notes
- Demo data files (`intercompany_demo_products.xml`, `intercompany_demo_bom.xml`) are loaded on demand via Settings, not on install
- Migration warning logs are stored under `docs/` for traceability
- This module has no dedicated `wizard/` or `controllers/` package at this stage
