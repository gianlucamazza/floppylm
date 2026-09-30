from floppylm.data import SEP, split_of, stories


def test_stories_dedup_and_strip() -> None:
    raw = "A cat.\n<|endoftext|>\n  A dog.  \n<|endoftext|>\nA cat.\n<|endoftext|>\n\n"
    assert list(stories(raw)) == ["A cat.", "A dog."]


def test_split_is_deterministic_and_disjoint() -> None:
    names = {split_of(f"story {i}") for i in range(5000)}
    assert names == {"train", "val", "test"}
    assert all(split_of("same") == split_of("same") for _ in range(3))
    frac = sum(split_of(f"s{i}") == "test" for i in range(20000)) / 20000
    assert 0.005 < frac < 0.015


def test_separator_is_single_byte() -> None:
    assert len(SEP) == 1
