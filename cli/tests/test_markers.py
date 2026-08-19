import pytest

PLAIN = """# Title

Some prose.
"""

WITH_VARIANT = """Intro.

<!-- e0:variant id="install" -->
<!-- when: os=macos -->
```bash
brew install ffmpeg
```
<!-- when: os=linux -->
```bash
sudo apt install ffmpeg
```
<!-- /e0:variant -->

Outro.
"""

WITH_RETONE = """Intro.

<!-- e0:retone based-on="the student's Linux knowledge" -->
<!-- /e0:retone -->

Outro.
"""


def test_plain_text_is_one_fixed_segment(e0mod):
    regions = e0mod.parse_regions(PLAIN)
    assert len(regions) == 1
    assert regions[0]["kind"] == "fixed"
    assert regions[0]["text"] == PLAIN


def test_variant_is_isolated_between_fixed_segments(e0mod):
    regions = e0mod.parse_regions(WITH_VARIANT)
    kinds = [region["kind"] for region in regions]
    assert kinds == ["fixed", "variant", "fixed"]
    assert regions[0]["text"].startswith("Intro.")
    assert regions[2]["text"].strip() == "Outro."


def test_variant_branches_are_parsed_with_conditions(e0mod):
    variant = e0mod.parse_regions(WITH_VARIANT)[1]
    assert variant["id"] == "install"
    assert len(variant["branches"]) == 2
    assert variant["branches"][0]["when"] == {"os": "macos"}
    assert "brew install ffmpeg" in variant["branches"][0]["text"]
    assert variant["branches"][1]["when"] == {"os": "linux"}
    assert "sudo apt install ffmpeg" in variant["branches"][1]["text"]


def test_branch_text_preserves_fenced_code_blocks(e0mod):
    variant = e0mod.parse_regions(WITH_VARIANT)[1]
    assert variant["branches"][0]["text"].count("```") == 2


def test_retone_block_records_its_basis_and_body(e0mod):
    regions = e0mod.parse_regions(WITH_RETONE)
    retone = regions[1]
    assert retone["kind"] == "retone"
    assert retone["basedOn"] == "the student's Linux knowledge"
    assert retone["text"].strip() == ""


def test_parse_when_handles_multiple_conditions(e0mod):
    assert e0mod.parse_when("os=macos shell=zsh") == {"os": "macos", "shell": "zsh"}
    assert e0mod.parse_when("os=linux") == {"os": "linux"}
    assert e0mod.parse_when("") == {}


def test_select_branch_matches_on_facts(e0mod):
    branches = [
        {"when": {"os": "macos"}, "text": "brew"},
        {"when": {"os": "linux"}, "text": "apt"},
    ]
    assert e0mod.select_branch(branches, {"os": "linux"})["text"] == "apt"
    assert e0mod.select_branch(branches, {"os": "windows"}) is None


def test_select_branch_requires_every_condition_to_match(e0mod):
    branches = [{"when": {"os": "linux", "shell": "fish"}, "text": "fishy"}]
    assert e0mod.select_branch(branches, {"os": "linux"}) is None
    assert e0mod.select_branch(branches, {"os": "linux", "shell": "fish"}) is not None


def test_unclosed_variant_raises_marker_error(e0mod):
    with pytest.raises(e0mod.MarkerError):
        e0mod.parse_regions('<!-- e0:variant id="x" -->\nno closing tag\n')


def test_closing_without_opening_raises_marker_error(e0mod):
    with pytest.raises(e0mod.MarkerError):
        e0mod.parse_regions("text\n<!-- /e0:variant -->\n")


def test_nested_regions_raise_marker_error(e0mod):
    with pytest.raises(e0mod.MarkerError):
        e0mod.parse_regions(
            '<!-- e0:variant id="a" -->\n<!-- e0:variant id="b" -->\n'
            "<!-- /e0:variant -->\n<!-- /e0:variant -->\n"
        )


def test_roundtrip_reassembles_the_original_text(e0mod):
    for source in (PLAIN, WITH_VARIANT, WITH_RETONE):
        regions = e0mod.parse_regions(source)
        rebuilt = "".join(region["raw"] for region in regions)
        assert rebuilt == source
