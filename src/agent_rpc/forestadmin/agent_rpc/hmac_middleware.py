import datetime

from forestadmin.datasource_toolkit.exceptions import ForestException
from forestadmin.rpc_common.hmac import generate_hmac, is_valid_hmac


class HmacValidationError(ForestException):
    pass


class HmacValidator:
    ALLOWED_TIME_DIFF = 300
    SIGNATURE_REUSE_WINDOW = 5

    def __init__(self, secret_key: str) -> None:
        self.secret_key = secret_key
        self.used_signatures = dict()

    def validate_hmac(self, sign, timestamp):
        """Validate the HMAC signature."""
        if not sign or not timestamp:
            raise HmacValidationError("Missing HMAC signature or timestamp")

        self.validate_timestamp(timestamp)

        expected_sign = generate_hmac(self.secret_key.encode("utf-8"), timestamp.encode("utf-8"))
        if not is_valid_hmac(self.secret_key.encode("utf-8"), timestamp.encode("utf-8"), expected_sign.encode("utf-8")):
            raise HmacValidationError("Invalid HMAC signature")

        if sign in self.used_signatures.keys():
            last_used = self.used_signatures[sign]
            if (datetime.datetime.now(datetime.timezone.utc) - last_used).total_seconds() > self.SIGNATURE_REUSE_WINDOW:
                raise HmacValidationError("HMAC signature has already been used")

        self.used_signatures[sign] = datetime.datetime.now(datetime.timezone.utc)
        self._cleanup_old_signs()
        return True

    def validate_timestamp(self, timestamp):
        try:
            current_time = datetime.datetime.fromisoformat(timestamp)
        except Exception:
            raise HmacValidationError("Invalid timestamp format")

        if (datetime.datetime.now(datetime.timezone.utc) - current_time).total_seconds() > self.ALLOWED_TIME_DIFF:
            raise HmacValidationError("Timestamp is too old or in the future")

    def _cleanup_old_signs(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        to_rm = []
        for sign, last_used in self.used_signatures.items():
            if (now - last_used).total_seconds() > self.ALLOWED_TIME_DIFF:
                to_rm.append(sign)

        for sign in to_rm:
            del self.used_signatures[sign]
