"""Claude Agent SDK integration — tool definitions and interceptors."""

from __future__ import annotations

from typing import Any

from .parser import VGKey, find_vg_key, parse_vg_key
from .trust import TrustAssessment, evaluate_trust


# --- VerigentTool: a tool_use definition for agent-to-agent verification ---

VERIGENT_TOOL_DEFINITION: dict[str, Any] = {
    "name": "verify_agent",
    "description": (
        "Verify an agent's Verigent (VG) trust key. "
        "Pass a VG key string or an agent handle to check trust level, "
        "tier, primary class, and class scores."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "vg_key": {
                "type": "string",
                "description": "The full VG key string (VG:NAME-SUFFIX:TIER-CLASS-scores)",
            },
        },
        "required": ["vg_key"],
    },
}


class VerigentTool:
    """Wraps VG verification as a Claude tool_use callable.

    Usage with the Claude Agent SDK:
        tool = VerigentTool()
        # Add tool.definition to your tools list
        # When tool_use is called, pass input to tool.execute()
    """

    @property
    def definition(self) -> dict[str, Any]:
        """The tool definition to pass to Claude's API."""
        return VERIGENT_TOOL_DEFINITION

    def execute(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Execute the verification tool. Returns parsed key + trust assessment."""
        vg_key_str = tool_input.get("vg_key", "")
        key = parse_vg_key(vg_key_str)

        if key is None:
            return {
                "verified": False,
                "error": "Invalid or missing VG key",
            }

        assessment = evaluate_trust(key)
        return {
            "verified": True,
            "handle": key.handle,
            "tier": key.tier_label,
            "primary_class": key.primary_class_name,
            "trust_level": assessment.level.value,
            "trust_score": assessment.score,
            "scores": key.scores,
            "reason": assessment.reason,
        }


# --- VerigentSystemPrompt: embed VG key into agent system prompts ---


class VerigentSystemPrompt:
    """Generate system prompt additions for a verified agent.

    Usage:
        vsp = VerigentSystemPrompt(vg_key="VG:JARVIS-0A:V3-ARCH...")
        system = base_prompt + vsp.render()
    """

    def __init__(self, vg_key: str):
        self.raw_key = vg_key
        self.parsed = parse_vg_key(vg_key)

    def render(self) -> str:
        """Render the system prompt block to append."""
        if self.parsed is None:
            return ""

        assessment = evaluate_trust(self.parsed)
        return (
            f"\n\n---\n"
            f"[Verigent Trust Identity]\n"
            f"Key: {self.raw_key}\n"
            f"Handle: {self.parsed.handle}\n"
            f"Tier: {self.parsed.tier_label}\n"
            f"Primary Class: {self.parsed.primary_class_name}\n"
            f"Trust Level: {assessment.level.value}\n"
            f"Trust Score: {assessment.score}\n"
            f"---\n"
        )

    @property
    def is_valid(self) -> bool:
        return self.parsed is not None


# --- VerigentInterceptor: check tool responses for VG keys ---


class VerigentInterceptor:
    """Intercepts tool responses and checks for VG keys in the output.

    Attach to your agent loop to automatically detect and evaluate
    VG keys returned by other agents or tools.

    Usage:
        interceptor = VerigentInterceptor()
        # After receiving a tool_result:
        result = interceptor.check(tool_result_content)
        if result:
            print(f"Found agent: {result.handle} at trust level {result.level}")
    """

    def __init__(self, min_trust_tier: int = 0):
        """
        Args:
            min_trust_tier: Minimum tier (0-6) to consider trustworthy.
        """
        self.min_trust_tier = min_trust_tier

    def check(self, content: str) -> TrustAssessment | None:
        """Check text content for a VG key and return assessment if found."""
        key = parse_vg_key(content)
        if key is None:
            return None
        return evaluate_trust(key)

    def check_message(self, message: dict[str, Any]) -> list[TrustAssessment]:
        """Check a Claude API message for VG keys in all content blocks."""
        assessments: list[TrustAssessment] = []
        content = message.get("content", [])

        if isinstance(content, str):
            result = self.check(content)
            if result:
                assessments.append(result)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    text = block.get("text", "") or str(block.get("content", ""))
                    result = self.check(text)
                    if result:
                        assessments.append(result)

        return assessments

    def is_trusted(self, content: str) -> bool:
        """Quick check: does this content contain a VG key above min tier?"""
        key = parse_vg_key(content)
        if key is None:
            return False
        return key.tier >= self.min_trust_tier
