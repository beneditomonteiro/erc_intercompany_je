import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

DEFAULT_REQUIRED_INTERCOMPANY_MODULE = "account_inter_company_rules"
PARAM_REQUIRED_INTERCOMPANY_MODULE = (
    "erc_intercompany_je.required_intercompany_module"
)
PARAM_REQUIRE_RULES_ON_INSTALL = "erc_intercompany_je.require_rules_on_install"
PARAM_REQUIRE_RULES_RUNTIME = "erc_intercompany_je.require_rules_runtime"


def _get_required_intercompany_module_name(env):
    module_name = (
        env["ir.config_parameter"]
        .sudo()
        .get_param(PARAM_REQUIRED_INTERCOMPANY_MODULE)
    )
    module_name = (module_name or "").strip()
    return module_name or DEFAULT_REQUIRED_INTERCOMPANY_MODULE


def _is_required_intercompany_module_available(env):
    module_name = _get_required_intercompany_module_name(env)
    if not module_name:
        return True
    module = env["ir.module.module"].sudo().search(
        [("name", "=", module_name)],
        limit=1,
    )
    return bool(module and module.state in {"installed", "to install", "to upgrade"})


def _assert_required_intercompany_module(env):
    if not _is_param_enabled(env, PARAM_REQUIRE_RULES_ON_INSTALL, True):
        return
    if _is_required_intercompany_module_available(env):
        return
    module_name = _get_required_intercompany_module_name(env)
    _logger.warning(
        "\n"
        "╔══════════════════════════════════════════════════════════════════╗\n"
        "║  ERC Intercompany JE — Prerequisite Not Installed              ║\n"
        "╠══════════════════════════════════════════════════════════════════╣\n"
        "║                                                                ║\n"
        "║  Module '%s' is not yet installed.                      ║\n"
        "║                                                                ║\n"
        "║  Installation will continue, but intercompany account setup    ║\n"
        "║  will be SKIPPED until you install the prerequisite module     ║\n"
        "║  and run: Settings > Intercompany Account Segregation >        ║\n"
        "║           'Analyze & Auto-Create Accounts'                     ║\n"
        "║                                                                ║\n"
        "╚══════════════════════════════════════════════════════════════════╝",
        module_name,
    )


def _is_param_enabled(env, key, default=True):
    value = env["ir.config_parameter"].sudo().get_param(key)
    if value in (None, ""):
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _run_intercompany_autosetup(env, reason):
    if not _is_param_enabled(env, PARAM_REQUIRE_RULES_RUNTIME, True):
        _logger.info(
            "%s intercompany setup: prerequisite runtime check disabled by backend parameter.",
            reason,
        )
    elif not _is_required_intercompany_module_available(env):
        module_name = _get_required_intercompany_module_name(env)
        _logger.warning(
            "%s intercompany setup skipped: module %s is not available.",
            reason,
            module_name,
        )
        return
    companies = env["res.company"].with_context(active_test=False).search(
        [("active", "=", True)],
        order="id",
    )
    for company in companies:
        _logger.info(
            "%s intercompany setup for company %s (%s)",
            reason,
            company.display_name,
            company.id,
        )
        company.with_context(
            allowed_company_ids=[company.id],
            company_id=company.id,
        ).action_setup_intercompany_accounts()


def post_init_hook(env_or_cr, registry=None):
    """Create/link intercompany accounts right after module installation."""
    if isinstance(env_or_cr, api.Environment):
        env = env_or_cr
    else:
        env = api.Environment(env_or_cr, SUPERUSER_ID, {})
    if not _is_param_enabled(env, "erc_intercompany_je.autosetup_on_install", True):
        _logger.info("Post-init intercompany autosetup skipped by backend parameter.")
        return
    _run_intercompany_autosetup(env, "Post-init")


def pre_init_hook(env_or_cr):
    """Block installation with a clear message when intercompany rules are missing."""
    if isinstance(env_or_cr, api.Environment):
        env = env_or_cr
    else:
        env = api.Environment(env_or_cr, SUPERUSER_ID, {})
    _assert_required_intercompany_module(env)
