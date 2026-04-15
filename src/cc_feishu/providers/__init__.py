from typing import Any

from ..auth.token_provider import FeishuTokenProvider
from ..client.http import FeishuHttpClient
from ..config import FeishuConfig, validate_config
from ..errors import ValidationError

PROVIDERS: dict[str, dict[str, Any]] = {
    "feishu": {
        "name": "Feishu Open Platform",
        "services": ["drive", "upload", "docs", "sheets", "slides", "bitable"],
    }
}


def init_provider(config: FeishuConfig) -> FeishuHttpClient:
    errors = validate_config(config)
    if errors:
        raise ValidationError("; ".join(errors))
    token_provider = FeishuTokenProvider(config)
    return FeishuHttpClient(config=config, token_provider=token_provider)
