import json
import logging
from datetime import datetime, timezone

from . import context


class JsonFormatter(logging.Formatter):
    def format(self, record):
        ctx = context.current()
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "tenant_id": str(ctx.tenant_id) if ctx.tenant_id else None,
            "request_id": ctx.request_id or None,
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)
