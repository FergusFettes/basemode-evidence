import pytest

from basemode_evidence.identity import canonical_endpoint


@pytest.mark.parametrize(
    ("contributed", "expected"),
    [
        # Older basemode versions contributed the provider's own spelling.
        ("anthropic/claude-opus-5", "anthropic/anthropic/claude-opus-5"),
        ("gemini/gemini-3-flash-preview", "gemini/google/gemini-3-flash-preview"),
        ("cerebras/zai-glm-4.6", "cerebras/zai/zai-glm-4.6"),
        # Resellers disagree about the creator's name.
        ("deepinfra/deepseek-ai/deepseek-v3.2", "deepinfra/deepseek/deepseek-v3.2"),
        ("novita/deepseek/deepseek-v3.2", "novita/deepseek/deepseek-v3.2"),
        ("openrouter/z-ai/glm-5", "openrouter/zai/glm-5"),
        # Already canonical: unchanged.
        ("openrouter/meta/llama-4-scout", "openrouter/meta/llama-4-scout"),
    ],
)
def test_legacy_endpoints_fold_onto_one_name(contributed, expected) -> None:
    assert canonical_endpoint(contributed) == expected


def test_openrouter_variant_suffixes_are_part_of_the_model() -> None:
    """`:free` and `:batch` are different endpoints, not noise to strip."""
    assert (
        canonical_endpoint("openrouter/z-ai/glm-5.3-flash:batch")
        == "openrouter/zai/glm-5.3-flash:batch"
    )
    assert canonical_endpoint("openrouter/google/gemma-4-31b-it:free") != canonical_endpoint(
        "openrouter/google/gemma-4-31b-it"
    )


def test_a_floating_alias_keeps_its_creator() -> None:
    """OpenRouter marks its `latest` aliases with `~` on the creator."""
    assert (
        canonical_endpoint("openrouter/~anthropic/claude-opus-latest")
        == "openrouter/anthropic/claude-opus-latest"
    )


def test_canonicalization_is_idempotent() -> None:
    for contributed in (
        "anthropic/claude-opus-5",
        "openrouter/z-ai/glm-5",
        "openrouter/~openai/gpt-latest",
    ):
        once = canonical_endpoint(contributed)
        assert canonical_endpoint(once) == once


def test_an_unrecognisable_name_is_not_guessed() -> None:
    assert canonical_endpoint("novita/elephant") == "novita/unknown/elephant"


@pytest.mark.parametrize(
    "endpoint",
    [
        "openrouter/z-ai/glm-5.3-flash:batch",
        "openrouter/~anthropic/claude-opus-latest",
        "together_ai/meta/llama-3.3-70b-instruct-turbo",
    ],
)
def test_real_endpoint_names_satisfy_the_schema_pattern(endpoint: str) -> None:
    """The pattern has to admit the IDs providers actually use."""
    import json
    import re
    from pathlib import Path

    schema = json.loads(
        (Path(__file__).resolve().parents[1] / "schemas/contribution-v1.schema.json").read_text()
    )
    assert re.fullmatch(schema["$defs"]["identifier"]["pattern"], endpoint)


@pytest.mark.parametrize("value", ["https://example.com", "http://a.b/c", "a//b"])
def test_the_pattern_still_refuses_url_shaped_endpoints(value: str) -> None:
    """Allowing `:` for variant suffixes must not let a URL back in."""
    import json
    import re
    from pathlib import Path

    schema = json.loads(
        (Path(__file__).resolve().parents[1] / "schemas/contribution-v1.schema.json").read_text()
    )
    assert not re.fullmatch(schema["$defs"]["identifier"]["pattern"], value)
