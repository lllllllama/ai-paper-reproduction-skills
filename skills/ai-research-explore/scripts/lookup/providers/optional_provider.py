"""Optional paid-provider adapter placeholder."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional


OPTIONAL_PROVIDER_ENV_VARS = {
    "openrouter": "RESEARCH_LOOKUP_OPENROUTER_API_KEY",
    "perplexity": "RESEARCH_LOOKUP_PERPLEXITY_API_KEY",
    "parallel": "RESEARCH_LOOKUP_PARALLEL_API_KEY",
}


def resolve_optional_record(locator_info: Dict[str, Any], lookup_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    configured = lookup_config.get("optional_providers") if isinstance(lookup_config, dict) else None
    providers = [str(item).strip().lower() for item in (configured or []) if str(item).strip()]
    for provider_name in providers:
        env_name = OPTIONAL_PROVIDER_ENV_VARS.get(provider_name)
        if env_name and os.environ.get(env_name):
            return None
    return None
