"""claude-sdk-verigent — Verigent trust verification for the Claude Agent SDK."""

from .middleware import VerigentInterceptor, VerigentSystemPrompt, VerigentTool
from .parser import VGKey, find_vg_key, parse_vg_key
from .trust import TrustAssessment, TrustLevel, evaluate_trust

__all__ = [
    "VGKey",
    "VerigentInterceptor",
    "VerigentSystemPrompt",
    "VerigentTool",
    "TrustAssessment",
    "TrustLevel",
    "evaluate_trust",
    "find_vg_key",
    "parse_vg_key",
]

__version__ = "0.1.0"
