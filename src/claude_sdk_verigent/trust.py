"""Trust evaluation logic for parsed VG keys."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .parser import VGKey


class TrustLevel(str, Enum):
    UNTRUSTED = "untrusted"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERIFIED = "verified"


@dataclass
class TrustAssessment:
    """Result of evaluating a VG key's trustworthiness."""

    level: TrustLevel
    score: float  # 0.0 - 1.0
    tier: int
    primary_class: str
    handle: str
    reason: str

    def to_dict(self) -> dict:
        return {
            "level": self.level.value,
            "score": self.score,
            "tier": self.tier,
            "primary_class": self.primary_class,
            "handle": self.handle,
            "reason": self.reason,
        }


def evaluate_trust(key: VGKey) -> TrustAssessment:
    """Evaluate trust level from a parsed VG key."""
    score = key.trust_score

    if key.tier >= 5 and score >= 0.7:
        level = TrustLevel.VERIFIED
        reason = f"Tier V{key.tier} with high aggregate score ({score:.2f})"
    elif key.tier >= 3 and score >= 0.5:
        level = TrustLevel.HIGH
        reason = f"Tier V{key.tier} with solid class profile"
    elif key.tier >= 2 and score >= 0.3:
        level = TrustLevel.MODERATE
        reason = f"Tier V{key.tier} — established but limited track record"
    elif key.tier >= 1:
        level = TrustLevel.LOW
        reason = f"Tier V{key.tier} — minimal verification history"
    else:
        level = TrustLevel.UNTRUSTED
        reason = "V0 tier — unverified agent"

    return TrustAssessment(
        level=level,
        score=score,
        tier=key.tier,
        primary_class=key.primary_class_name,
        handle=key.handle,
        reason=reason,
    )
