# claude-sdk-verigent

Verigent trust verification for the [Claude Agent SDK](https://docs.anthropic.com/en/docs/agents).

## The Problem

When Claude agents interact with other agents, there's no standard way to verify identity or assess trust. An agent claiming to be "JARVIS" might be a verified V5 Architect or a spoofed impersonator. Without verification, multi-agent systems operate on blind trust.

Verigent solves this with cryptographic trust keys (VG keys) that encode an agent's identity, tier, primary class, and 12-axis capability scores.

## Install

```bash
pip install claude-sdk-verigent
```

Requires `anthropic>=0.30.0`.

## Usage

### Embed a VG key in your agent's system prompt

```python
from claude_sdk_verigent import VerigentSystemPrompt

vg_key = "VG:JARVIS-0A:V3-ARCH·Se4Op7An5Ar9Co2Ad6St8Sc3Sa5So1Br2Fo6"
vsp = VerigentSystemPrompt(vg_key)

system_prompt = "You are JARVIS, an architecture agent." + vsp.render()
```

This appends a structured trust identity block that other agents can parse and verify.

### Add the verification tool to multi-agent setups

```python
from anthropic import Anthropic
from claude_sdk_verigent import VerigentTool

client = Anthropic()
tool = VerigentTool()

# Include in your tools list
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=[tool.definition],
    messages=[{"role": "user", "content": "Verify this agent's key: VG:ATLAS-7B:V4-SENT·Se8Op6An7Ar5Co4Ad3St9Sc2Sa6So3Br4Fo5"}],
)

# Handle tool_use response
for block in response.content:
    if block.type == "tool_use" and block.name == "verify_agent":
        result = tool.execute(block.input)
        # result = {"verified": True, "handle": "ATLAS", "tier": "V4", ...}
```

### Intercept and verify keys in tool responses

```python
from claude_sdk_verigent import VerigentInterceptor

interceptor = VerigentInterceptor(min_trust_tier=2)

# Check any text for embedded VG keys
assessment = interceptor.check(tool_response_text)
if assessment:
    print(f"{assessment.handle}: {assessment.level.value} (score {assessment.score})")

# Quick trust gate
if interceptor.is_trusted(agent_output):
    # proceed with high-trust path
    ...
```

### Parse a key directly

```python
from claude_sdk_verigent import parse_vg_key, evaluate_trust

key = parse_vg_key("VG:JARVIS-0A:V3-ARCH·Se4Op7An5Ar9Co2Ad6St8Sc3Sa5So1Br2Fo6")
print(key.handle)        # "JARVIS"
print(key.tier)          # 3
print(key.scores)        # {"Sentinel": 4, "Operative": 7, ...}

assessment = evaluate_trust(key)
print(assessment.level)  # TrustLevel.HIGH
```

## VG Key Format

```
VG:{NAME}-{SUFFIX}:{TIER}-{PRIMARY}·{12x class_code+digit}
```

- **NAME**: Agent handle (e.g., JARVIS, ATLAS)
- **SUFFIX**: Unique identifier
- **TIER**: V0 (unverified) through V6 (maximum trust)
- **PRIMARY**: 4-letter primary class code
- **Scores**: 12 two-letter class codes each followed by a digit (0-9)

### Trust Classes

| Code | Class | Code | Class |
|------|-------|------|-------|
| Se | Sentinel | St | Steward |
| Op | Operative | Sc | Scout |
| An | Analyst | Sa | Sage |
| Ar | Architect | So | Sovereign |
| Co | Conduit | Br | Broker |
| Ad | Adaptor | Fo | Forge |

## Links

- [Verigent](https://verigent.ai) — Agent trust infrastructure
- [Claude Agent SDK docs](https://docs.anthropic.com/en/docs/agents)

## License

MIT
