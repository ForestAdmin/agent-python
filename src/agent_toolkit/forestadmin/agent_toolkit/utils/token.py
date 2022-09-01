import zoneinfo
from datetime import datetime, timedelta
from typing import Any, Dict, Tuple

from jose import jwt


def build_jwt(body: Dict[str, Any], secret: str, expiration: int = 1) -> Tuple[str, Dict[str, Any]]:
    body["exp"] = datetime.timestamp(
        datetime.utcnow().replace(tzinfo=zoneinfo.ZoneInfo("UTC")) + timedelta(hours=expiration)
    )
    return jwt.encode(body, secret, algorithm="HS256"), body  # type: ignore
