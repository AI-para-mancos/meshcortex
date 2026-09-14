from pathlib import Path

import pytest
import yaml

ROUTING_CONFIG_DIR = Path(__file__).resolve().parents[3] / "configs" / "routing"
SPLITS = ("few_shot", "typical", "adversarial")
LANGUAGES = {"es", "en", "mixed"}


def _load(filename):
    return yaml.safe_load((ROUTING_CONFIG_DIR / filename).read_text(encoding="utf-8"))


TAXONOMY = _load("taxonomy.yaml")
SEED_SET = _load("seed_prompts.yaml")
CLASS_NAMES = {cls["name"] for cls in TAXONOMY["classes"]}
ENTRIES = [entry for split in SPLITS for entry in SEED_SET[split]]


def test_splits_are_exactly_the_declared_ones():
    """A stray extra key would hold prompts that nothing ever evaluates."""
    assert set(SEED_SET) == set(SPLITS)


@pytest.mark.parametrize("cls", TAXONOMY["classes"], ids=lambda cls: cls["name"])
def test_class_is_fully_defined(cls):
    assert cls["definition"].strip()
    assert cls["signals"]
    assert cls["not_this_class"].strip()


def test_prompt_ids_are_unique_across_splits():
    ids = [entry["id"] for entry in ENTRIES]

    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("entry", ENTRIES, ids=lambda entry: entry["id"])
def test_entry_is_complete_and_labelled(entry):
    assert entry["prompt"].strip()
    assert entry["lang"] in LANGUAGES
    assert entry["label"] in CLASS_NAMES


@pytest.mark.parametrize("entry", SEED_SET["adversarial"], ids=lambda entry: entry["id"])
def test_adversarial_entry_records_its_trap(entry):
    assert entry.get("note", "").strip()


def test_few_shot_pool_shares_no_prompt_with_the_evaluation_splits():
    """Catches a pooled prompt re-pasted under a fresh id, which unique ids would miss."""
    pool = {entry["prompt"].strip() for entry in SEED_SET["few_shot"]}
    evaluated = {
        entry["prompt"].strip() for split in ("typical", "adversarial") for entry in SEED_SET[split]
    }

    assert pool.isdisjoint(evaluated)
