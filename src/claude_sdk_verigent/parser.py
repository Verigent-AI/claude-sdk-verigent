"""VG key parser — pure regex, no external dependencies."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

CLASS_CODES = {
    "Se": "Sentinel",
    "Op": "Operative",
    "An": "Analyst",
    "Ar": "Architect",
    "Co": "Conduit",
    "Ad": "Adaptor",
    "St": "Steward",
    "Sc": "Scout",
    "Sa": "Sage",
    "So": "Sovereign",
    "Br": "Broker",
    "Fo": "Forge",
}

VG_KEY_PATTERN = re.compile(
    r"VG:([A-Z0-9][\w-]*)-([A-Z0-9]+):(V[0-6])-([A-Z]{4})\xb7((?:[A-Z][a-z]\d){12})"
)

SCORE_PATTERN = re.compile(r"([A-Z][a-z])(\d)")


@dataclass
class VGKey:
    """Parsed Verigent key."""

    raw: str
    handle: str
    suffix: str
    tier: int  # 0-6
    primary_class: str  # 4-letter code
    scores: dict[str, int] = field(default_factory=dict)  # class_name -> 0-9

    @property
    def tier_label(self) -> str:
        return f"V{self.tier}"

    @property
    def primary_class_name(self) -> str:
        return CLASS_CODES.get(self.primary_class[:2], self.primary_class)

    @property
    def trust_score(self) -> float:
        """Aggregate trust score (0.0 - 1.0) derived from tier and class scores."""
        tier_weight = self.tier / 6.0
        if self.scores:
            avg_score = sum(self.scores.values()) / (len(self.scores) * 9.0)
        else:
            avg_score = 0.0
        return round(tier_weight * 0.6 + avg_score * 0.4, 3)


def parse_vg_key(text: str) -> VGKey | None:
    """Parse a VG key from text. Returns None if no valid key found."""
    match = VG_KEY_PATTERN.search(text)
    if not match:
        return None

    handle = match.group(1)
    suffix = match.group(2)
    tier = int(match.group(3)[1])
    primary = match.group(4)
    scores_raw = match.group(5)

    scores: dict[str, int] = {}
    for code_match in SCORE_PATTERN.finditer(scores_raw):
        code = code_match.group(1)
        digit = int(code_match.group(2))
        class_name = CLASS_CODES.get(code, code)
        scores[class_name] = digit

    return VGKey(
        raw=match.group(0),
        handle=handle,
        suffix=suffix,
        tier=tier,
        primary_class=primary,
        scores=scores,
    )


def find_vg_key(
    *,
    system_prompt: str | None = None,
    headers: dict[str, str] | None = None,
    metadata: dict | None = None,
) -> VGKey | None:
    """Search for a VG key across system prompts, headers, and metadata."""
    if system_prompt:
        key = parse_vg_key(system_prompt)
        if key:
            return key

    if headers:
        for header_name in ("X-Verigent", "x-verigent"):
            if header_name in headers:
                key = parse_vg_key(headers[header_name])
                if key:
                    return key

    if metadata:
        for field_name in ("x-verigent", "X-Verigent", "verigent"):
            if field_name in metadata:
                key = parse_vg_key(str(metadata[field_name]))
                if key:
                    return key

    return None
