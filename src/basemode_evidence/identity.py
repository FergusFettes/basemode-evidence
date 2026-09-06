"""Fold contributed endpoint IDs onto one canonical `provider/creator/model`.

Contributions are immutable once merged, and they arrive from whatever
basemode version the contributor is running. Older ones name an endpoint the
way a single provider does — `anthropic/claude-opus-5`, with no creator, or
`deepinfra/deepseek-ai/...` and `novita/deepseek/...` for the same
organisation under two spellings. Aggregating those as written puts one model
under several rows and compares nothing.

So the compiled dataset canonicalizes at read time rather than asking anyone
to rewrite evidence they already published. Bundles on disk keep exactly the
bytes they were contributed with, and the per-bundle tables record what each
one actually said.

This deliberately does not import basemode: the evidence repository must be
able to validate and compile a contribution without running provider code.
The tables below are the public naming vocabulary, and duplicating them here
is the price of that independence.
"""

from __future__ import annotations

#: Creator spellings that mean the same organisation. Mirrors
#: `basemode.identity.CREATOR_ALIASES`; keep the two in step when a reseller
#: invents a new spelling for someone already listed.
CREATOR_ALIASES: dict[str, str] = {
    "deepseek-ai": "deepseek",
    "z-ai": "zai",
    "zai-org": "zai",
    "minimaxai": "minimax",
    "meta-llama": "meta",
    "moonshotai": "moonshot",
    "x-ai": "xai",
    "mistralai": "mistral",
    "alibaba": "qwen",
    "qwen-ai": "qwen",
    "google-deepmind": "google",
    "nvidia-nim": "nvidia",
    "nim": "nvidia",
}

#: The creator a first-party provider means when it names no creator at all.
FIRST_PARTY_CREATOR: dict[str, str] = {
    "anthropic": "anthropic",
    "openai": "openai",
    "gemini": "google",
    "xai": "xai",
    "zai": "zai",
    "moonshot": "moonshot",
    "deepseek": "deepseek",
}

#: Resellers publish bare hyphenated names too (`cerebras/zai-glm-4.6`).
#: Longest prefix wins, so ordering matters.
_CREATOR_BY_STEM_PREFIX: tuple[tuple[str, str], ...] = (
    ("zai-glm", "zai"),
    ("glm", "zai"),
    ("gpt-oss", "openai"),
    ("gpt", "openai"),
    ("gemma", "google"),
    ("gemini", "google"),
    ("llama", "meta"),
    ("qwen", "qwen"),
    ("kimi", "moonshot"),
    ("deepseek", "deepseek"),
    ("mistral", "mistral"),
    ("mixtral", "mistral"),
    ("minimax", "minimax"),
    ("grok", "xai"),
    ("phi", "microsoft"),
    ("nemotron", "nvidia"),
)

UNKNOWN_CREATOR = "unknown"


def canonical_creator(name: str) -> str:
    # OpenRouter prefixes a creator with `~` on its floating "latest" aliases;
    # that marks the model, not a different organisation.
    lowered = name.strip().lower().lstrip("~")
    return CREATOR_ALIASES.get(lowered, lowered)


def canonical_endpoint(endpoint: str) -> str:
    """Canonicalize one contributed endpoint ID, leaving unknowns honest."""
    parts = [part for part in endpoint.strip().lower().split("/") if part]
    if not parts:
        return endpoint
    if len(parts) == 1:
        return f"unknown/{UNKNOWN_CREATOR}/{parts[0]}"
    route, stem = parts[0], parts[-1]
    if len(parts) >= 3:
        return f"{route}/{canonical_creator(parts[1])}/{stem}"
    creator = FIRST_PARTY_CREATOR.get(route)
    if creator is None:
        creator = next(
            (known for prefix, known in _CREATOR_BY_STEM_PREFIX if stem.startswith(prefix)),
            UNKNOWN_CREATOR,
        )
    return f"{route}/{creator}/{stem}"
