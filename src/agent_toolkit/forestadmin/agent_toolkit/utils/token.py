import sys
from datetime import datetime, timedelta
from typing import Any, Dict, Tuple

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

import jwt


def build_jwt(body: Dict[str, Any], secret: str, expiration: int = 1) -> Tuple[str, Dict[str, Any]]:
    body["exp"] = datetime.timestamp(
        datetime.now(tz=zoneinfo.ZoneInfo("UTC")) + timedelta(hours=expiration)  # type: ignore
    )
    return jwt.encode(body, secret, algorithm="HS256"), body  # type: ignore
