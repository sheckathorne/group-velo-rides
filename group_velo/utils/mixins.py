from sqids.sqids import Sqids

from config.settings.base import SQIDS_ALPHABET, SQIDS_MIN_LEN


class SqidMixin:
    sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)

    def decode_sqid(self, val):
        return self.sqids.decode(val)[0]

    def encode_sqid(self, val):
        return self.sqids.encode([val])
