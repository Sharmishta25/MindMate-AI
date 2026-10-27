"""Authenticated field encryption. Metadata/legacy tables/exports are not encrypted."""
import json
from cryptography.fernet import Fernet,MultiFernet,InvalidToken
from mindmate.services.core import DataError


class Cipher:
    def __init__(self,keys):
        try:
            values=keys.split(',') if isinstance(keys,str) else list(keys)
            if not values or any(not value.strip() for value in values): raise ValueError()
            self.engine=MultiFernet([Fernet(value.strip()) for value in values])
        except (ValueError,TypeError):
            raise DataError('Configure a valid MINDMATE_ENCRYPTION_KEYS key ring; keys are never recovered from passwords') from None

    def encrypt(self,payload,limit=262144):
        try:
            encoded=json.dumps(payload,ensure_ascii=False,allow_nan=False).encode('utf-8')
            if len(encoded)>limit: raise ValueError()
            return self.engine.encrypt(encoded).decode('ascii')
        except (ValueError,TypeError,UnicodeError):
            raise ValueError('Record is too large or contains invalid data') from None

    def decrypt(self,token):
        try:
            return json.loads(self.engine.decrypt(token.encode('ascii')))
        except (InvalidToken,ValueError,TypeError,UnicodeError):
            raise DataError('Encrypted record could not be read. Check the key ring or restore a verified backup; do not reset storage.') from None

    def rotate(self,token):
        try: return self.engine.rotate(token.encode('ascii')).decode('ascii')
        except (InvalidToken,ValueError,TypeError): raise DataError('Rotation failed; no record should be discarded') from None
