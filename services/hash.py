from __future__ import annotations

import hashlib
import hmac
from typing import Iterable, Optional, Union, List


class HashService:
    """
    Minimal global hashing utility working with arrays of strings.

    - normalize_string(s): trims and lowercases a single string
    - compute(strings): normalizes list of strings and returns SHA-256 hex digest
    - compare_raw_to_hash(expected_hash, strings): constant-time compare of computed hash vs expected

    Notes:
    - For convenience, a single string is also accepted and treated as [string].
    - Strings are concatenated with a '|' delimiter after normalization for determinism.
    """

    @staticmethod
    def normalize_string(s: Optional[str]) -> str:
        if s is None:
            return ""
        return s.strip().lower()

    @classmethod
    def compute(cls, strings: Union[str, Iterable[str]]) -> str:
        """Compute SHA-256 over normalized strings joined by '|'."""
        # Backward compatibility: allow single string input
        if isinstance(strings, str):
            strings = [strings]
        # Ensure list of normalized strings
        normalized: List[str] = [cls.normalize_string(s) for s in strings]
        # Deterministic payload
        payload = "|".join(normalized).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    @classmethod
    def compare_raw_to_hash(
        cls, expected_hash: str, strings: Union[str, Iterable[str]]
    ) -> bool:
        """Normalize strings, compute SHA-256 and compare in constant time."""
        actual = cls.compute(strings)
        return hmac.compare_digest(actual, expected_hash)
